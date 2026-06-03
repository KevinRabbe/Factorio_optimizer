from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from factorio_optimizer.core.objects import Direction, FactoryObject, Position
from factorio_optimizer.segments.ports import SegmentPort
from factorio_optimizer.segments.segment_base import Segment


InterfaceKind = Literal["input", "output"]


@dataclass
class InterfaceSegment(Segment):
    item: str = ""
    kind: InterfaceKind = "input"

    def __post_init__(self) -> None:
        self.segment_type = "interface_segment"
        self.ports = self._build_ports()

    def expand(self) -> list[FactoryObject]:
        object_type = "input_interface" if self.kind == "input" else "output_interface"
        role = "source" if self.kind == "input" else "sink"

        return [
            FactoryObject(
                object_id=f"{self.segment_id}_interface",
                object_type=object_type,
                position=self.position,
                direction=self.direction,
                item=self.item,
                role=role,
            )
        ]

    def _build_ports(self) -> list[SegmentPort]:
        port_kind = "output" if self.kind == "input" else "input"
        return [
            SegmentPort(
                port_id=f"{self.segment_id}_{self.kind}",
                item=self.item,
                kind=port_kind,
                position=self.position,
                direction=self.direction,
            )
        ]


def create_interface_segment(
    segment_id: str,
    item: str,
    kind: InterfaceKind,
    position: Position,
    direction: Direction,
) -> InterfaceSegment:
    return InterfaceSegment(
        segment_id=segment_id,
        segment_type="interface_segment",
        position=position,
        direction=direction,
        item=item,
        kind=kind,
    )
