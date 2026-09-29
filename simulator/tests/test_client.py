import threading

import httpx

from app.client import ReadingsClient

READING = {"sensor_id": "6f1c8a2e-6b3d-4f9a-9c21-0b7e5d3a9d4b", "pressure": 3.42, "measured_at": "2026-09-16T10:00:00Z"}


def _client(handler, max_retries=2):
    calls = []

    def recording_handler(request):
        calls.append(request)
        return handler(request)

    client = ReadingsClient(
        "http://backend:8000", 1, max_retries, retry_delay_seconds=0,
        transport=httpx.MockTransport(recording_handler),
    )
    return client, calls


def test_posts_reading_to_contract_path():
    client, calls = _client(lambda request: httpx.Response(201, json={}))
    assert client.send(READING) is True
    assert calls[0].method == "POST"
    assert calls[0].url.path == "/api/readings"
    assert calls[0].read() == httpx.Request("POST", "/", json=READING).read()


def test_client_errors_are_not_retried():
    for status in (404, 422, 501):
        client, calls = _client(lambda request, status=status: httpx.Response(status))
        assert client.send(READING) is False
        assert len(calls) == 1


def test_unavailable_backend_is_retried_then_dropped():
    client, calls = _client(lambda request: httpx.Response(503), max_retries=2)
    assert client.send(READING) is False
    assert len(calls) == 3


def test_network_error_recovers_on_retry():
    responses = iter([httpx.ConnectError("refused"), httpx.Response(201, json={})])

    def handler(request):
        outcome = next(responses)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome

    client, calls = _client(handler)
    assert client.send(READING) is True
    assert len(calls) == 2


def test_wait_until_ready_returns_true_once_health_db_is_up():
    responses = iter([httpx.Response(503), httpx.Response(200)])
    client, calls = _client(lambda request: next(responses))

    ready = client.wait_until_ready(threading.Event(), poll_interval=0, timeout=1)

    assert ready is True
    assert [call.url.path for call in calls] == ["/api/health/db", "/api/health/db"]


def test_wait_until_ready_gives_up_after_timeout():
    client, calls = _client(lambda request: httpx.Response(503))

    ready = client.wait_until_ready(threading.Event(), poll_interval=0, timeout=0.05)

    assert ready is False
    assert len(calls) >= 1


def test_wait_until_ready_stops_immediately_when_stop_is_set():
    client, calls = _client(lambda request: httpx.Response(503))
    stop = threading.Event()
    stop.set()

    ready = client.wait_until_ready(stop, poll_interval=0, timeout=1)

    assert ready is False
    assert calls == []
