from __future__ import annotations

from dataclasses import dataclass, field

from factorio_optimizer.core.objects import FactoryObject, Position
from factorio_optimizer.modules.connections import ModuleConnection
from factorio_optimizer.segments.ports import SegmentPort
from factorio_optimizer.segments.segment_base import ExpandableSegment


@dataclass(frozen=True)
class ModuleRate:
    item: str
    amount_per_second: float


@dataclass(frozen=True)
class Footprint:
    width: int
    height: int

    def __post_init__(self) -> None:
        if self.width < 1:
            raise ValueError("Footprint width must be at least 1.")
        if self.height < 1:
            raise ValueError("Footprint height must be at least 1.")


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
    flow_links: list[ModuleConnection] = field(default_factory=list)
    recipe_name: str | None = None
    machine_name: str | None = None
    footprint: Footprint | None = None

    def expand(self) -> list[FactoryObject]:
        objects: list[FactoryObject] = []
        for segment in self.segments:
            objects.extend(segment.expand())
        return objects

    @property
    def ports(self) -> list[SegmentPort]:
        return [*self.input_ports, *self.output_ports]
