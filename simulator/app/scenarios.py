import random
from collections.abc import Callable

Scenario = Callable[[random.Random], float | None]


def _bounded_gauss(rng: random.Random, mean: float, deviation: float, low: float, high: float) -> float:
    return round(min(max(rng.gauss(mean, deviation), low), high), 3)


def normal(rng: random.Random) -> float:
    return _bounded_gauss(rng, mean=3.5, deviation=0.25, low=2.5, high=4.5)


def low_pressure(rng: random.Random) -> float:
    return _bounded_gauss(rng, mean=0.8, deviation=0.15, low=0.2, high=1.2)


def high_pressure(rng: random.Random) -> float:
    return _bounded_gauss(rng, mean=7.5, deviation=0.3, low=6.6, high=9.0)


def offline(rng: random.Random) -> None:
    return None


SCENARIOS: dict[str, Scenario] = {
    "normal": normal,
    "low": low_pressure,
    "high": high_pressure,
    "offline": offline,
}
