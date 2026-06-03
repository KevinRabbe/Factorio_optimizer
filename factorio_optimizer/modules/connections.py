from __future__ import annotations

from dataclasses import dataclass

from factorio_optimizer.core.objects import Position


@dataclass(frozen=True)
class ModuleConnection:
    flow_id: str
    item: str
    source_port_id: str
    target_port_id: str
    source_object_id: str
    target_object_id: str
    method: str
    path: list[Position]
