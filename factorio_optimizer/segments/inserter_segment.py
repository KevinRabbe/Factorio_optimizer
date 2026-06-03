from __future__ import annotations

from dataclasses import dataclass

from factorio_optimizer.core.objects import Direction, FactoryObject, Position
from factorio_optimizer.segments.ports import SegmentPort
from factorio_optimizer.segments.segment_base import Segment


_PICKUP_DELTAS: dict[Direction, tuple[int, int]] = {
    "north": (0, 1),
    "east": (-1, 0),
    "south": (0, -1),
    "west": (1, 0),
}

_DROPOFF_DELTAS: dict[Direction, tuple[int, int]] = {
    "north": (0, -1),
    "east": (1, 0),
    "south": (0, 1),
    "west": (-1, 0),
}


@dataclass
class InserterTransferSegment(Segment):
    item: str = ""
    role: str = "transfer"

    def __post_init__(self) -> None:
        self.segment_type = "inserter_transfer_segment"
        self.ports = self._build_ports()

    def expand(self) -> list[FactoryObject]:
        return [
            FactoryObject(
                object_id=f"{self.segment_id}_inserter",
                object_type="inserter",
                position=self.position,
                direction=self.direction,
                item=self.item,
                role=self.role,
            )
        ]

    def _build_ports(self) -> list[SegmentPort]:
        pickup_dx, pickup_dy = _PICKUP_DELTAS[self.direction]
        dropoff_dx, dropoff_dy = _DROPOFF_DELTAS[self.direction]

        pickup_position = Position(self.position.x + pickup_dx, self.position.y + pickup_dy)
        dropoff_position = Position(self.position.x + dropoff_dx, self.position.y + dropoff_dy)

        return [
            SegmentPort(
                port_id=f"{self.segment_id}_pickup",
                item=self.item,
                kind="input",
                position=pickup_position,
                direction=self.direction,
            ),
            SegmentPort(
                port_id=f"{self.segment_id}_dropoff",
                item=self.item,
                kind="output",
                position=dropoff_position,
                direction=self.direction,
            ),
        ]


def create_inserter_transfer_segment(
    segment_id: str,
    item: str,
    position: Position,
    direction: Direction,
    role: str,
) -> InserterTransferSegment:
    return InserterTransferSegment(
        segment_id=segment_id,
        segment_type="inserter_transfer_segment",
        position=position,
        direction=direction,
        item=item,
        role=role,
    )
