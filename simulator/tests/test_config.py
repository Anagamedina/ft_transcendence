from uuid import UUID

import pytest

from app.config import ConfigError, load_config

SENSOR_ID = "6f1c8a2e-6b3d-4f9a-9c21-0b7e5d3a9d4b"


def test_defaults_with_only_sensor_ids():
    config = load_config({"SIMULATOR_SENSOR_IDS": SENSOR_ID})
    assert config.sensor_ids == (UUID(SENSOR_ID),)
    assert config.scenario == "normal"
    assert config.interval_seconds == 5
    assert config.dry_run is False
    assert config.ready_poll_seconds == 2
    assert config.ready_timeout_seconds == 60
    assert config.heartbeat_file == "/tmp/simulator-heartbeat"


def test_parses_multiple_sensor_ids_and_flags():
    config = load_config({
        "SIMULATOR_SENSOR_IDS": f" {SENSOR_ID} , {SENSOR_ID.replace('6f', '7f', 1)} ",
        "SIMULATOR_SCENARIO": "HIGH",
        "SIMULATOR_INTERVAL_SECONDS": "0.5",
        "SIMULATOR_DRY_RUN": "true",
        "SIMULATOR_API_URL": "http://backend:8000/",
        "SIMULATOR_READY_POLL_SECONDS": "1",
        "SIMULATOR_READY_TIMEOUT_SECONDS": "0",
        "SIMULATOR_HEARTBEAT_FILE": "/tmp/custom-heartbeat",
    })
    assert len(config.sensor_ids) == 2
    assert config.scenario == "high"
    assert config.interval_seconds == 0.5
    assert config.dry_run is True
    assert config.api_url == "http://backend:8000"
    assert config.ready_poll_seconds == 1
    assert config.ready_timeout_seconds == 0
    assert config.heartbeat_file == "/tmp/custom-heartbeat"


@pytest.mark.parametrize("env", [
    {},
    {"SIMULATOR_SENSOR_IDS": "not-a-uuid"},
    {"SIMULATOR_SENSOR_IDS": SENSOR_ID, "SIMULATOR_SCENARIO": "leak"},
    {"SIMULATOR_SENSOR_IDS": SENSOR_ID, "SIMULATOR_INTERVAL_SECONDS": "0"},
    {"SIMULATOR_SENSOR_IDS": SENSOR_ID, "SIMULATOR_MAX_RETRIES": "-1"},
    {"SIMULATOR_SENSOR_IDS": SENSOR_ID, "SIMULATOR_READY_POLL_SECONDS": "0"},
    {"SIMULATOR_SENSOR_IDS": SENSOR_ID, "SIMULATOR_READY_TIMEOUT_SECONDS": "-1"},
])
def test_invalid_configuration_is_rejected(env):
    with pytest.raises(ConfigError):
        load_config(env)
