from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Belt:
    name: str
    items_per_second: float

    @property
    def items_per_minute(self) -> float:
        return self.items_per_second * 60.0

    @property
    def items_per_hour(self) -> float:
        return self.items_per_second * 3600.0


BELTS: dict[str, Belt] = {
    "transport_belt": Belt(name="transport_belt", items_per_second=15.0),
    "fast_transport_belt": Belt(name="fast_transport_belt", items_per_second=30.0),
    "express_transport_belt": Belt(name="express_transport_belt", items_per_second=45.0),
}


def get_belt(belt_name: str) -> Belt:
    try:
        return BELTS[belt_name]
    except KeyError as exc:
        raise ValueError(f"Unknown belt: {belt_name}") from exc
