from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Inserter:
    name: str
    estimated_items_per_second: float

    @property
    def estimated_items_per_minute(self) -> float:
        return self.estimated_items_per_second * 60.0

    @property
    def estimated_items_per_hour(self) -> float:
        return self.estimated_items_per_second * 3600.0


INSERTERS: dict[str, Inserter] = {
    # Conservative early estimates. Later these should be replaced by measured values
    # based on pickup/dropoff situation and stack bonus.
    "burner_inserter": Inserter(name="burner_inserter", estimated_items_per_second=0.6),
    "inserter": Inserter(name="inserter", estimated_items_per_second=0.83),
    "fast_inserter": Inserter(name="fast_inserter", estimated_items_per_second=2.31),
}


def get_inserter(inserter_name: str) -> Inserter:
    try:
        return INSERTERS[inserter_name]
    except KeyError as exc:
        raise ValueError(f"Unknown inserter: {inserter_name}") from exc
