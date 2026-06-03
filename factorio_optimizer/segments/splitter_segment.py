from __future__ import annotations

from dataclasses import dataclass

from factorio_optimizer.core.objects import Direction, FactoryObject, Position
from factorio_optimizer.segments.ports import SegmentPort
from factorio_optimizer.segments.segment_base import Segment


@dataclass
class SplitterSegment(Segment):
    item: str = ""

    def __post_init__(self) -> None:
        self.segment_type = "splitter_segment"
        self.ports = self._build_ports()

    def expand(self) -> list[FactoryObject]:
        return [
            FactoryObject(
                object_id=f"{self.segment_id}_splitter",
                object_type="splitter",
                position=self.position,
                direction=self.direction,
                width=2,
                height=1,
                item=self.item,
                role="splitter",
            )
        ]

    def _build_ports(self) -> list[SegmentPort]:
        return [
            SegmentPort(
                port_id=f"{self.segment_id}_input",
                item=self.item,
                kind="input",
                position=Position(self.position.x - 1, self.position.y),
                direction=self.direction,
            ),
            SegmentPort(
                port_id=f"{self.segment_id}_primary_output",
                item=self.item,
                kind="output",
                position=Position(self.position.x + 2, self.position.y),
                direction=self.direction,
            ),
            SegmentPort(
                port_id=f"{self.segment_id}_secondary_output",
                item=self.item,
                kind="output",
                position=Position(self.position.x + 2, self.position.y + 1),
                direction=self.direction,
            ),
        ]


def create_splitter_segment(
    segment_id: str,
    item: str,
    position: Position,
    direction: Direction = "east",
) -> SplitterSegment:
    return SplitterSegment(
        segment_id=segment_id,
        segment_type="splitter_segment",
        position=position,
        direction=direction,
        item=item,
    )
