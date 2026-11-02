import random

import pytest

from app.scenarios import SCENARIOS

SENSOR_MIN_THRESHOLD_BAR = 1.5
SENSOR_MAX_THRESHOLD_BAR = 6.0


def _samples(name: str, count: int = 500) -> list[float | None]:
    rng = random.Random(42)
    return [SCENARIOS[name](rng) for _ in range(count)]


def test_normal_stays_inside_sensor_thresholds():
    assert all(SENSOR_MIN_THRESHOLD_BAR < value < SENSOR_MAX_THRESHOLD_BAR for value in _samples("normal"))


def test_low_stays_below_min_threshold():
    assert all(0 <= value < SENSOR_MIN_THRESHOLD_BAR for value in _samples("low"))


def test_high_stays_above_max_threshold():
    assert all(SENSOR_MAX_THRESHOLD_BAR < value <= 25 for value in _samples("high"))


def test_offline_sends_nothing():
    assert all(value is None for value in _samples("offline"))


@pytest.mark.parametrize("name", ["normal", "low", "high"])
def test_same_seed_gives_same_sequence(name):
    assert _samples(name, 20) == _samples(name, 20)
