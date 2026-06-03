from __future__ import annotations

from dataclasses import dataclass

from factorio_optimizer.core.objects import Position


@dataclass
class Flow:
    flow_id: str
    item: str
    source_id: str
    target_id: str
    method: str
    path: list[Position]
