import pytest

from app.outbox import OutboxError, ReadingOutbox


READING = {
    "id": "7d8b8f34-4c5b-4cf6-a9a1-7b7b8d7e2a11",
    "sensor_id": "6f1c8a2e-6b3d-4f9a-9c21-0b7e5d3a9d4b",
    "pressure": 3.42,
    "measured_at": "2026-09-16T10:00:00Z",
}


def test_outbox_survives_reload_and_acknowledges(tmp_path):
    path = tmp_path / "outbox.json"
    outbox = ReadingOutbox(str(path))
    outbox.add(READING)

    reloaded = ReadingOutbox(str(path))
    assert reloaded.pending() == [READING]

    reloaded.acknowledge(READING["id"])
    assert ReadingOutbox(str(path)).pending() == []


def test_outbox_does_not_duplicate_same_id(tmp_path):
    outbox = ReadingOutbox(str(tmp_path / "outbox.json"))
    outbox.add(READING)
    outbox.add(dict(READING))

    assert outbox.pending() == [READING]


def test_outbox_rejects_conflicting_payload_for_same_id(tmp_path):
    outbox = ReadingOutbox(str(tmp_path / "outbox.json"))
    outbox.add(READING)

    with pytest.raises(OutboxError):
        outbox.add({**READING, "pressure": 4.2})
