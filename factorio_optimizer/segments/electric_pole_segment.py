from __future__ import annotations

from dataclasses import dataclass

from factorio_optimizer.core.objects import Direction, FactoryObject, Position
from factorio_optimizer.segments.segment_base import Segment


@dataclass
class ElectricPoleSegment(Segment):
    entity_name: str = "small-electric-pole"

    def __post_init__(self) -> None:
        self.segment_type = "electric_pole_segment"
        self.ports = []

    def expand(self) -> list[FactoryObject]:
        return [
            FactoryObject(
                object_id=f"{self.segment_id}_pole",
                object_type="electric_pole",
                position=self.position,
                direction=self.direction,
                role="power",
                entity_name=self.entity_name,
            )
        ]


def create_electric_pole_segment(
    segment_id: str,
    position: Position,
    direction: Direction = "north",
    entity_name: str = "small-electric-pole",
) -> ElectricPoleSegment:
    return ElectricPoleSegment(
        segment_id=segment_id,
        segment_type="electric_pole_segment",
        position=position,
        direction=direction,
        entity_name=entity_name,
    )
