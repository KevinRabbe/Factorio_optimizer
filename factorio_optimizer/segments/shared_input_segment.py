from __future__ import annotations

from dataclasses import dataclass

from factorio_optimizer.core.objects import Direction, FactoryObject, Position
from factorio_optimizer.segments.ports import SegmentPort
from factorio_optimizer.segments.segment_base import Segment
from factorio_optimizer.segments.splitter_segment import create_splitter_segment


@dataclass
class SharedInputSegment(Segment):
    item: str = ""

    def __post_init__(self) -> None:
        self.segment_type = "shared_input_segment"
        self.ports = self._build_ports()

    def expand(self) -> list[FactoryObject]:
        # First version expands to a small belt line plus splitter stub.
        # Later this can become a real splitter entity export.
        splitter = create_splitter_segment(
            segment_id=f"{self.segment_id}_splitter",
            item=self.item,
            position=Position(self.position.x + 2, self.position.y),
            direction=self.direction,
        )
        return [
            FactoryObject(
                object_id=f"{self.segment_id}_input_belt_0",
                object_type="belt",
                position=self.position,
                direction=self.direction,
                item=self.item,
                role="shared_input",
            ),
            FactoryObject(
                object_id=f"{self.segment_id}_input_belt_1",
                object_type="belt",
                position=Position(self.position.x + 1, self.position.y),
                direction=self.direction,
                item=self.item,
                role="shared_input",
            ),
            *splitter.expand(),
        ]

    def _build_ports(self) -> list[SegmentPort]:
        return [
            SegmentPort(
                port_id=f"{self.segment_id}_input",
                item=self.item,
                kind="input",
                position=self.position,
                direction=self.direction,
            ),
            SegmentPort(
                port_id=f"{self.segment_id}_primary_output",
                item=self.item,
                kind="output",
                position=Position(self.position.x + 4, self.position.y),
                direction=self.direction,
            ),
            SegmentPort(
                port_id=f"{self.segment_id}_secondary_output",
                item=self.item,
                kind="output",
                position=Position(self.position.x + 4, self.position.y + 1),
                direction=self.direction,
            ),
        ]


def create_shared_input_segment(
    segment_id: str,
    item: str,
    position: Position,
    direction: Direction = "east",
) -> SharedInputSegment:
    return SharedInputSegment(
        segment_id=segment_id,
        segment_type="shared_input_segment",
        position=position,
        direction=direction,
        item=item,
    )
