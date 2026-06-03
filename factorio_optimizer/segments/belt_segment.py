from __future__ import annotations

from dataclasses import dataclass

from factorio_optimizer.core.objects import Direction, FactoryObject, Position
from factorio_optimizer.segments.ports import SegmentPort
from factorio_optimizer.segments.segment_base import Segment


_DIRECTION_DELTAS: dict[Direction, tuple[int, int]] = {
    "north": (0, -1),
    "east": (1, 0),
    "south": (0, 1),
    "west": (-1, 0),
}


@dataclass
class BeltSegment(Segment):
    item: str = ""
    length: int = 1

    def __post_init__(self) -> None:
        if self.length < 1:
            raise ValueError("BeltSegment length must be at least 1.")
        self.segment_type = "belt_segment"
        self.ports = self._build_ports()

    def expand(self) -> list[FactoryObject]:
        dx, dy = _DIRECTION_DELTAS[self.direction]
        return [
            FactoryObject(
                object_id=f"{self.segment_id}_belt_{index}",
                object_type="belt",
                position=Position(self.position.x + dx * index, self.position.y + dy * index),
                direction=self.direction,
                item=self.item,
                role="transport",
            )
            for index in range(self.length)
        ]

    def _build_ports(self) -> list[SegmentPort]:
        dx, dy = _DIRECTION_DELTAS[self.direction]
        end_position = Position(
            self.position.x + dx * (self.length - 1),
            self.position.y + dy * (self.length - 1),
        )
        return [
            SegmentPort(
                port_id=f"{self.segment_id}_input",
                item=self.item,
                kind="input",
                position=self.position,
                direction=self.direction,
            ),
            SegmentPort(
                port_id=f"{self.segment_id}_output",
                item=self.item,
                kind="output",
                position=end_position,
                direction=self.direction,
            ),
        ]


def create_belt_segment(
    segment_id: str,
    item: str,
    position: Position,
    direction: Direction,
    length: int,
) -> BeltSegment:
    return BeltSegment(
        segment_id=segment_id,
        segment_type="belt_segment",
        position=position,
        direction=direction,
        item=item,
        length=length,
    )
