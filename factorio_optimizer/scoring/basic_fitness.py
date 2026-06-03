from __future__ import annotations

from dataclasses import dataclass

from factorio_optimizer.core.blueprint_plan import BlueprintPlan
from factorio_optimizer.validation.static_validator import validate_plan


@dataclass
class FitnessBreakdown:
    valid_bonus: int
    entity_penalty: int
    belt_penalty: int
    area_penalty: int
    flow_penalty: int

    @property
    def total(self) -> int:
        return (
            self.valid_bonus
            - self.entity_penalty
            - self.belt_penalty
            - self.area_penalty
            - self.flow_penalty
        )


def score_plan(plan: BlueprintPlan) -> FitnessBreakdown:
    validation = validate_plan(plan)

    valid_bonus = 10_000 if validation.passed else 0
    entity_penalty = len(plan.objects) * 10
    belt_penalty = _count_belts(plan) * 5
    area_penalty = _used_area(plan) * 3
    flow_penalty = _total_flow_length(plan) * 2

    return FitnessBreakdown(
        valid_bonus=valid_bonus,
        entity_penalty=entity_penalty,
        belt_penalty=belt_penalty,
        area_penalty=area_penalty,
        flow_penalty=flow_penalty,
    )


def _count_belts(plan: BlueprintPlan) -> int:
    return sum(1 for obj in plan.objects if obj.object_type == "belt")


def _total_flow_length(plan: BlueprintPlan) -> int:
    return sum(len(flow.path) for flow in plan.flows)


def _used_area(plan: BlueprintPlan) -> int:
    occupied_x: list[int] = []
    occupied_y: list[int] = []

    for obj in plan.objects:
        if obj.object_type in {"input_interface", "output_interface"}:
            continue

        for tile in obj.occupied_tiles():
            occupied_x.append(tile.x)
            occupied_y.append(tile.y)

    if not occupied_x or not occupied_y:
        return 0

    width = max(occupied_x) - min(occupied_x) + 1
    height = max(occupied_y) - min(occupied_y) + 1

    return width * height
