import os
import time

from app import healthcheck


def test_fresh_heartbeat_is_healthy(tmp_path, monkeypatch):
    path = tmp_path / "heartbeat"
    path.touch()
    monkeypatch.setenv("SIMULATOR_HEARTBEAT_FILE", str(path))
    monkeypatch.setenv("SIMULATOR_INTERVAL_SECONDS", "5")

    assert healthcheck.main() == 0


def test_stale_heartbeat_is_unhealthy(tmp_path, monkeypatch):
    path = tmp_path / "heartbeat"
    path.touch()
    old = time.time() - 3600
    os.utime(path, (old, old))
    monkeypatch.setenv("SIMULATOR_HEARTBEAT_FILE", str(path))
    monkeypatch.setenv("SIMULATOR_INTERVAL_SECONDS", "5")

    assert healthcheck.main() == 1


def test_missing_heartbeat_is_unhealthy(tmp_path, monkeypatch):
    monkeypatch.setenv("SIMULATOR_HEARTBEAT_FILE", str(tmp_path / "missing"))

    assert healthcheck.main() == 1
