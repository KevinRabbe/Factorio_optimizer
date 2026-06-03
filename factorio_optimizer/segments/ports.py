from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from factorio_optimizer.core.objects import Direction, Position


PortKind = Literal["input", "output"]


@dataclass(frozen=True)
class SegmentPort:
    port_id: str
    item: str
    kind: PortKind
    position: Position
    direction: Direction

    def can_connect_to(self, other: "SegmentPort") -> bool:
        return self.kind == "output" and other.kind == "input" and self.item == other.item
