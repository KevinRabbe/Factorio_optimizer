from __future__ import annotations

from dataclasses import dataclass, field

from factorio_optimizer.core.flows import Flow
from factorio_optimizer.core.objects import FactoryObject


@dataclass
class BlueprintPlan:
    plan_id: str
    width: int
    height: int
    objects: list[FactoryObject] = field(default_factory=list)
    flows: list[Flow] = field(default_factory=list)

    def get_object(self, object_id: str) -> FactoryObject | None:
        for obj in self.objects:
            if obj.object_id == object_id:
                return obj
        return None
