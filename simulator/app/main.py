import logging
import pathlib
import random
import signal
import sys
import threading
import uuid
from datetime import datetime, timezone

from app.client import ReadingsClient
from app.config import ConfigError, SimulatorConfig, load_config
from app.scenarios import SCENARIOS

logger = logging.getLogger("simulator")


def build_reading(sensor_id: str, pressure: float) -> dict:
    measured_at = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    return {"id": str(uuid.uuid4()), "sensor_id": sensor_id, "pressure": pressure, "measured_at": measured_at}


def _touch_heartbeat(path: str) -> None:
    try:
        pathlib.Path(path).touch()
    except OSError as exc:
        logger.warning("could not update heartbeat file %s: %s", path, exc)


def run(config: SimulatorConfig, stop: threading.Event) -> bool:
    rng = random.Random(config.random_seed)
    scenario = SCENARIOS[config.scenario]
    client = None if config.dry_run else ReadingsClient(
        config.api_url, config.ingest_api_key, config.request_timeout_seconds, config.max_retries
    )

    logger.info(
        "starting scenario=%s sensors=%d interval=%ss dry_run=%s api=%s",
        config.scenario, len(config.sensor_ids), config.interval_seconds, config.dry_run, config.api_url,
    )
    try:
        if client is not None:
            logger.info(
                "waiting for backend readiness poll=%ss timeout=%s",
                config.ready_poll_seconds, config.ready_timeout_seconds or "none",
            )
            ready = client.wait_until_ready(
                stop, config.ready_poll_seconds, config.ready_timeout_seconds or None
            )
            if not ready:
                if stop.is_set():
                    logger.info("stopped while waiting for backend")
                    return True
                logger.error("backend not ready after %ss, giving up", config.ready_timeout_seconds)
                return False
            logger.info("backend ready")

        while not stop.is_set():
            for sensor_id in config.sensor_ids:
                if stop.is_set():
                    break
                pressure = scenario(rng)
                if pressure is None:
                    logger.info("sensor=%s offline, no reading sent", sensor_id)
                    continue
                reading = build_reading(str(sensor_id), pressure)
                if client is None:
                    logger.info("dry-run %s", reading)
                else:
                    client.send(reading)
            _touch_heartbeat(config.heartbeat_file)
            stop.wait(config.interval_seconds)
        return True
    finally:
        if client is not None:
            client.close()
        logger.info("stopped")


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    logging.getLogger("httpx").setLevel(logging.WARNING)
    try:
        config = load_config()
    except ConfigError as exc:
        logger.error("invalid configuration: %s", exc)
        return 1

    stop = threading.Event()
    for signum in (signal.SIGINT, signal.SIGTERM):
        signal.signal(signum, lambda *_: stop.set())

    return 0 if run(config, stop) else 1


if __name__ == "__main__":
    sys.exit(main())
