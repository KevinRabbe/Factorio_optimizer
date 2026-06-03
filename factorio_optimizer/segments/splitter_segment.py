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
        # Temporary representation: the object model does not have a splitter type yet.
        # Until export support is added, keep the splitter as two belt tiles.
        return [
            FactoryObject(
                object_id=f"{self.segment_id}_splitter_left_stub",
                object_type="belt",
                position=self.position,
                direction=self.direction,
                item=self.item,
                role="splitter_stub",
            ),
            FactoryObject(
                object_id=f"{self.segment_id}_splitter_right_stub",
                object_type="belt",
                position=Position(self.position.x + 1, self.position.y),
                direction=self.direction,
                item=self.item,
                role="splitter_stub",
            ),
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
