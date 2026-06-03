from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PowerProducer:
    name: str
    power_kw: float


POWER_PRODUCERS: dict[str, PowerProducer] = {
    "steam_engine": PowerProducer(name="steam_engine", power_kw=900.0),
}


def get_power_producer(name: str) -> PowerProducer:
    try:
        return POWER_PRODUCERS[name]
    except KeyError as exc:
        raise ValueError(f"Unknown power producer: {name}") from exc
