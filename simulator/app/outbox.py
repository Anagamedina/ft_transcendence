"""Small durable outbox for readings waiting for backend confirmation."""

from __future__ import annotations

import json
import os
import threading
import uuid
from pathlib import Path


class OutboxError(RuntimeError):
    """The outbox cannot be read or durably updated."""


class ReadingOutbox:
    """A JSON outbox with atomic replace and fsync semantics.

    The simulator has one producer/consumer thread, but the lock also keeps
    the class safe for a future retry worker. A reading is removed only after
    the API has acknowledged it; resending after a crash is safe because the
    reading carries its stable id.
    """

    def __init__(self, path: str) -> None:
        self._path = Path(path)
        self._lock = threading.Lock()
        self._entries = self._load()

    def pending(self) -> list[dict]:
        with self._lock:
            return [dict(entry) for entry in self._entries]

    def add(self, reading: dict) -> None:
        reading_id = reading.get("id")
        if not reading_id:
            raise OutboxError("a reading must have an id before entering the outbox")

        with self._lock:
            for entry in self._entries:
                if entry.get("id") == reading_id:
                    if entry != reading:
                        raise OutboxError(f"outbox id {reading_id} has conflicting data")
                    return
            self._entries.append(dict(reading))
            self._persist_locked()

    def acknowledge(self, reading_id: str) -> None:
        with self._lock:
            remaining = [entry for entry in self._entries if entry.get("id") != reading_id]
            if len(remaining) == len(self._entries):
                return
            self._entries = remaining
            self._persist_locked()

    def _load(self) -> list[dict]:
        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            if not self._path.exists():
                return []
            with self._path.open("r", encoding="utf-8") as handle:
                data = json.load(handle)
        except (OSError, json.JSONDecodeError) as exc:
            raise OutboxError(f"could not load outbox {self._path}") from exc

        if not isinstance(data, list) or any(
            not isinstance(entry, dict) or not entry.get("id") for entry in data
        ):
            raise OutboxError(f"outbox {self._path} has an invalid format")

        unique: dict[str, dict] = {}
        for entry in data:
            reading_id = entry["id"]
            previous = unique.get(reading_id)
            if previous is not None and previous != entry:
                raise OutboxError(f"outbox id {reading_id} has conflicting data")
            unique[reading_id] = entry
        return list(unique.values())

    def _persist_locked(self) -> None:
        temporary = self._path.with_name(f".{self._path.name}.{uuid.uuid4().hex}.tmp")
        try:
            with temporary.open("w", encoding="utf-8") as handle:
                json.dump(self._entries, handle, ensure_ascii=False, separators=(",", ":"))
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, self._path)
            try:
                directory_fd = os.open(self._path.parent, os.O_RDONLY)
                try:
                    os.fsync(directory_fd)
                finally:
                    os.close(directory_fd)
            except OSError:
                # File data is already durable on platforms without fsyncable
                # directory handles; do not turn a successful replace into a
                # false failure.
                pass
        except OSError as exc:
            try:
                temporary.unlink(missing_ok=True)
            except OSError:
                pass
            raise OutboxError(f"could not persist outbox {self._path}") from exc
