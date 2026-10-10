import threading

from app import main
from app.config import load_config

NORMAL_ID = "00000000-0000-4000-8000-000000000001"
LOW_ID = "00000000-0000-4000-8000-000000000004"
OFFLINE_ID = "00000000-0000-4000-8000-000000000007"


def test_each_sensor_sends_its_own_scenario(tmp_path, monkeypatch):
    config = load_config({
        "SIMULATOR_SENSOR_IDS": f"{NORMAL_ID},{LOW_ID},{OFFLINE_ID}",
        "SIMULATOR_SCENARIO": "normal",
        "SIMULATOR_SCENARIOS": f"{LOW_ID}:low,{OFFLINE_ID}:offline",
        "SIMULATOR_DRY_RUN": "true",
        "SIMULATOR_HEARTBEAT_FILE": str(tmp_path / "heartbeat"),
    })
    sent = []
    real_build = main.build_reading
    monkeypatch.setattr(main, "build_reading", lambda sensor_id, pressure: (
        sent.append((sensor_id, pressure)) or real_build(sensor_id, pressure)
    ))
    stop = threading.Event()
    # One loop over every sensor: the heartbeat is written at the end of it.
    monkeypatch.setattr(main, "_touch_heartbeat", lambda _path: stop.set())

    assert main.run(config, stop) is True

    pressures = dict(sent)
    assert set(pressures) == {NORMAL_ID, LOW_ID}  # offline sends nothing
    assert 2.5 <= pressures[NORMAL_ID] <= 4.5
    assert pressures[LOW_ID] < 1.5
