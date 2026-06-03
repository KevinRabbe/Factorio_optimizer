from __future__ import annotations

from dataclasses import dataclass

from factorio_optimizer.core.objects import FactoryObject, Position


@dataclass(frozen=True)
class Footprint:
    min_x: int
    min_y: int
    max_x: int
    max_y: int

    @property
    def width(self) -> int:
        return self.max_x - self.min_x + 1

    @property
    def height(self) -> int:
        return self.max_y - self.min_y + 1

    @property
    def area(self) -> int:
        return self.width * self.height


def calculate_objects_footprint(objects: list[FactoryObject]) -> Footprint:
    if not objects:
        return Footprint(min_x=0, min_y=0, max_x=0, max_y=0)

    occupied = [tile for obj in objects for tile in obj.occupied_tiles()]
    return Footprint(
        min_x=min(tile.x for tile in occupied),
        min_y=min(tile.y for tile in occupied),
        max_x=max(tile.x for tile in occupied),
        max_y=max(tile.y for tile in occupied),
    )


def calculate_positions_footprint(positions: list[Position]) -> Footprint:
    if not positions:
        return Footprint(min_x=0, min_y=0, max_x=0, max_y=0)

    return Footprint(
        min_x=min(position.x for position in positions),
        min_y=min(position.y for position in positions),
        max_x=max(position.x for position in positions),
        max_y=max(position.y for position in positions),
    )
