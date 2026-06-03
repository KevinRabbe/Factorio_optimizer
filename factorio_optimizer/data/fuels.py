from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Fuel:
    item: str
    energy_mj: float


FUELS: dict[str, Fuel] = {
    "coal": Fuel(item="coal", energy_mj=4.0),
    "wood": Fuel(item="wood", energy_mj=2.0),
}


def get_fuel(item: str) -> Fuel:
    try:
        return FUELS[item]
    except KeyError as exc:
        raise ValueError(f"Unknown fuel: {item}") from exc
