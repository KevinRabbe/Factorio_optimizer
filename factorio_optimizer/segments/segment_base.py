from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from factorio_optimizer.core.objects import Direction, FactoryObject, Position
from factorio_optimizer.segments.ports import SegmentPort


class ExpandableSegment(Protocol):
    segment_id: str
    segment_type: str
    position: Position
    direction: Direction
    ports: list[SegmentPort]

    def expand(self) -> list[FactoryObject]:
        ...


@dataclass
class Segment:
    segment_id: str
    segment_type: str
    position: Position
    direction: Direction
    ports: list[SegmentPort] = field(default_factory=list)

    def expand(self) -> list[FactoryObject]:
        raise NotImplementedError(f"{self.segment_type} does not implement expand().")
