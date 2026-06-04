from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


Direction = Literal["north", "east", "south", "west"]

ObjectType = Literal[
    "input_interface",
    "output_interface",
    "assembler",
    "furnace",
    "inserter",
    "belt",
    "splitter",
]


@dataclass(frozen=True)
class Position:
    x: int
    y: int


@dataclass
class FactoryObject:
    object_id: str
    object_type: ObjectType
    position: Position
    direction: Direction
    width: int = 1
    height: int = 1
    recipe: str | None = None
    item: str | None = None
    role: str | None = None

    def occupied_tiles(self) -> set[Position]:
        return {
            Position(self.position.x + dx, self.position.y + dy)
            for dx in range(self.width)
            for dy in range(self.height)
        }
