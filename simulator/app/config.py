import os
from dataclasses import dataclass
from uuid import UUID

from app.scenarios import SCENARIOS


DEFAULT_INGEST_API_KEY = "dev-only-ingest-key"


class ConfigError(ValueError):
    pass


@dataclass(frozen=True)
class SimulatorConfig:
    api_url: str
    ingest_api_key: str
    sensor_ids: tuple[UUID, ...]
    scenario: str
    # Per-sensor overrides from SIMULATOR_SCENARIOS; any other sensor uses `scenario`.
    sensor_scenarios: dict[UUID, str]
    interval_seconds: float
    request_timeout_seconds: float
    max_retries: int
    random_seed: int
    dry_run: bool
    ready_poll_seconds: float
    ready_timeout_seconds: float
    heartbeat_file: str


def _positive_float(env: dict[str, str], name: str, default: str) -> float:
    raw = env.get(name, default)
    try:
        value = float(raw)
    except ValueError as exc:
        raise ConfigError(f"{name} must be a number, got {raw!r}") from exc
    if value <= 0:
        raise ConfigError(f"{name} must be greater than 0, got {raw!r}")
    return value


def _non_negative_int(env: dict[str, str], name: str, default: str) -> int:
    raw = env.get(name, default)
    try:
        value = int(raw)
    except ValueError as exc:
        raise ConfigError(f"{name} must be an integer, got {raw!r}") from exc
    if value < 0:
        raise ConfigError(f"{name} must be 0 or greater, got {raw!r}")
    return value


def _non_negative_float(env: dict[str, str], name: str, default: str) -> float:
    raw = env.get(name, default)
    try:
        value = float(raw)
    except ValueError as exc:
        raise ConfigError(f"{name} must be a number, got {raw!r}") from exc
    if value < 0:
        raise ConfigError(f"{name} must be 0 or greater, got {raw!r}")
    return value


def _sensor_ids(env: dict[str, str]) -> tuple[UUID, ...]:
    raw = env.get("SIMULATOR_SENSOR_IDS", "")
    parts = [part.strip() for part in raw.split(",") if part.strip()]
    if not parts:
        raise ConfigError("SIMULATOR_SENSOR_IDS must list at least one sensor UUID")
    try:
        return tuple(UUID(part) for part in parts)
    except ValueError as exc:
        raise ConfigError(f"SIMULATOR_SENSOR_IDS contains an invalid UUID: {raw!r}") from exc


def _scenario_name(name: str, raw: str) -> str:
    scenario = raw.strip().lower()
    if scenario not in SCENARIOS:
        valid = ", ".join(sorted(SCENARIOS))
        raise ConfigError(f"{name} must use one of: {valid}; got {raw.strip()!r}")
    return scenario


def _sensor_scenarios(env: dict[str, str], sensor_ids: tuple[UUID, ...]) -> dict[UUID, str]:
    # SIMULATOR_SCENARIOS=<uuid>:<scenario>,<uuid>:<scenario>
    # Only for sensors already in SIMULATOR_SENSOR_IDS: an unknown id is
    # almost always a typo, and silently ignoring it would hide it.
    raw = env.get("SIMULATOR_SCENARIOS", "")
    scenarios: dict[UUID, str] = {}
    for part in (p.strip() for p in raw.split(",")):
        if not part:
            continue
        sensor, sep, scenario = part.rpartition(":")
        if not sep:
            raise ConfigError(f"SIMULATOR_SCENARIOS entries must be <sensor_id>:<scenario>, got {part!r}")
        try:
            sensor_id = UUID(sensor.strip())
        except ValueError as exc:
            raise ConfigError(f"SIMULATOR_SCENARIOS contains an invalid UUID: {part!r}") from exc
        if sensor_id not in sensor_ids:
            raise ConfigError(f"SIMULATOR_SCENARIOS sensor {sensor_id} is not in SIMULATOR_SENSOR_IDS")
        if sensor_id in scenarios:
            raise ConfigError(f"SIMULATOR_SCENARIOS lists sensor {sensor_id} twice")
        scenarios[sensor_id] = _scenario_name("SIMULATOR_SCENARIOS", scenario)
    return scenarios


def _ingest_api_key(env: dict[str, str]) -> str:
    # Same key the backend checks on POST /api/readings via X-Ingest-Key (#106).
    key = env.get("INGEST_API_KEY", DEFAULT_INGEST_API_KEY).strip()
    if not key:
        raise ConfigError("INGEST_API_KEY must not be empty")
    return key


def load_config(env: dict[str, str] | None = None) -> SimulatorConfig:
    env = dict(os.environ) if env is None else env

    scenario = _scenario_name("SIMULATOR_SCENARIO", env.get("SIMULATOR_SCENARIO", "normal"))
    sensor_ids = _sensor_ids(env)

    return SimulatorConfig(
        api_url=env.get("SIMULATOR_API_URL", "http://backend:8000").rstrip("/"),
        ingest_api_key=_ingest_api_key(env),
        sensor_ids=sensor_ids,
        scenario=scenario,
        sensor_scenarios=_sensor_scenarios(env, sensor_ids),
        interval_seconds=_positive_float(env, "SIMULATOR_INTERVAL_SECONDS", "5"),
        request_timeout_seconds=_positive_float(env, "SIMULATOR_REQUEST_TIMEOUT_SECONDS", "5"),
        max_retries=_non_negative_int(env, "SIMULATOR_MAX_RETRIES", "3"),
        random_seed=_non_negative_int(env, "SIMULATOR_SEED", "42"),
        dry_run=env.get("SIMULATOR_DRY_RUN", "false").strip().lower() in {"1", "true", "yes"},
        ready_poll_seconds=_positive_float(env, "SIMULATOR_READY_POLL_SECONDS", "2"),
        ready_timeout_seconds=_non_negative_float(env, "SIMULATOR_READY_TIMEOUT_SECONDS", "60"),
        heartbeat_file=env.get("SIMULATOR_HEARTBEAT_FILE", "/tmp/simulator-heartbeat"),
    )


def scenario_for(config: SimulatorConfig, sensor_id: UUID) -> str:
    return config.sensor_scenarios.get(sensor_id, config.scenario)
