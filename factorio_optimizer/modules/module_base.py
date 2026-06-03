from __future__ import annotations

from dataclasses import dataclass, field

from factorio_optimizer.core.objects import FactoryObject, Position
from factorio_optimizer.segments.ports import SegmentPort
from factorio_optimizer.segments.segment_base import ExpandableSegment


@dataclass(frozen=True)
class ModuleRate:
    item: str
    amount_per_second: float


@dataclass
class FactoryModule:
    module_id: str
    module_type: str
    position: Position
    input_ports: list[SegmentPort] = field(default_factory=list)
    output_ports: list[SegmentPort] = field(default_factory=list)
    input_rates: list[ModuleRate] = field(default_factory=list)
    output_rates: list[ModuleRate] = field(default_factory=list)
    segments: list[ExpandableSegment] = field(default_factory=list)

    def expand(self) -> list[FactoryObject]:
        objects: list[FactoryObject] = []
        for segment in self.segments:
            objects.extend(segment.expand())
        return objects

    @property
    def ports(self) -> list[SegmentPort]:
        return [*self.input_ports, *self.output_ports]
