import os
from dataclasses import dataclass
from uuid import UUID

from app.scenarios import SCENARIOS


class ConfigError(ValueError):
    pass


@dataclass(frozen=True)
class SimulatorConfig:
    api_url: str
    sensor_ids: tuple[UUID, ...]
    scenario: str
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


def load_config(env: dict[str, str] | None = None) -> SimulatorConfig:
    env = dict(os.environ) if env is None else env

    scenario = env.get("SIMULATOR_SCENARIO", "normal").strip().lower()
    if scenario not in SCENARIOS:
        valid = ", ".join(sorted(SCENARIOS))
        raise ConfigError(f"SIMULATOR_SCENARIO must be one of: {valid}; got {scenario!r}")

    return SimulatorConfig(
        api_url=env.get("SIMULATOR_API_URL", "http://backend:8000").rstrip("/"),
        sensor_ids=_sensor_ids(env),
        scenario=scenario,
        interval_seconds=_positive_float(env, "SIMULATOR_INTERVAL_SECONDS", "5"),
        request_timeout_seconds=_positive_float(env, "SIMULATOR_REQUEST_TIMEOUT_SECONDS", "5"),
        max_retries=_non_negative_int(env, "SIMULATOR_MAX_RETRIES", "3"),
        random_seed=_non_negative_int(env, "SIMULATOR_SEED", "42"),
        dry_run=env.get("SIMULATOR_DRY_RUN", "false").strip().lower() in {"1", "true", "yes"},
        ready_poll_seconds=_positive_float(env, "SIMULATOR_READY_POLL_SECONDS", "2"),
        ready_timeout_seconds=_non_negative_float(env, "SIMULATOR_READY_TIMEOUT_SECONDS", "60"),
        heartbeat_file=env.get("SIMULATOR_HEARTBEAT_FILE", "/tmp/simulator-heartbeat"),
    )
