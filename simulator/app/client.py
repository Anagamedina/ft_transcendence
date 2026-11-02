import logging
import threading
import time

import httpx

logger = logging.getLogger("simulator.client")

RETRYABLE_STATUS_CODES = {502, 503, 504}


class ReadingsClient:
    def __init__(
        self,
        api_url: str,
        ingest_api_key: str,
        timeout_seconds: float,
        max_retries: int,
        retry_delay_seconds: float = 1.0,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self._http = httpx.Client(base_url=api_url, timeout=timeout_seconds, transport=transport)
        self._ingest_headers = {"X-Ingest-Key": ingest_api_key}
        self._max_retries = max_retries
        self._retry_delay_seconds = retry_delay_seconds

    def send(self, reading: dict) -> bool:
        attempts = self._max_retries + 1
        for attempt in range(1, attempts + 1):
            try:
                response = self._http.post(
                    "/api/readings", json=reading, headers=self._ingest_headers
                )
            except httpx.TransportError as exc:
                logger.warning(
                    "sensor=%s attempt=%d/%d network error: %s",
                    reading["sensor_id"], attempt, attempts, exc.__class__.__name__,
                )
            else:
                if response.is_success:
                    logger.info(
                        "sensor=%s pressure=%s status=%d",
                        reading["sensor_id"], reading["pressure"], response.status_code,
                    )
                    return True
                if response.status_code == 401:
                    # Config error (wrong or missing INGEST_API_KEY), not a network one: never retry.
                    logger.error(
                        "sensor=%s status=401 ingest key rejected: check INGEST_API_KEY in .env",
                        reading["sensor_id"],
                    )
                    return False
                if response.status_code not in RETRYABLE_STATUS_CODES:
                    logger.error(
                        "sensor=%s status=%d rejected: %s",
                        reading["sensor_id"], response.status_code, response.text[:200],
                    )
                    return False
                logger.warning(
                    "sensor=%s attempt=%d/%d status=%d",
                    reading["sensor_id"], attempt, attempts, response.status_code,
                )
            if attempt < attempts:
                time.sleep(self._retry_delay_seconds)
        logger.error("sensor=%s dropped after %d attempts", reading["sensor_id"], attempts)
        return False

    def wait_until_ready(
        self, stop: threading.Event, poll_interval: float, timeout: float | None
    ) -> bool:
        deadline = None if not timeout else time.monotonic() + timeout
        while not stop.is_set():
            try:
                response = self._http.get("/api/health/db")
            except httpx.TransportError as exc:
                logger.info("backend not ready: %s", exc.__class__.__name__)
            else:
                if response.status_code == 200:
                    return True
                logger.info("backend not ready: status=%d", response.status_code)
            if deadline is not None and time.monotonic() >= deadline:
                return False
            stop.wait(poll_interval)
        return False

    def close(self) -> None:
        self._http.close()
