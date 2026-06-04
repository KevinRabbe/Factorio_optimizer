from __future__ import annotations

from factorio_optimizer.core.blueprint_plan import BlueprintPlan
from factorio_optimizer.scoring.strategy import ScoreResult
from factorio_optimizer.validation.structure_validator import validate_plan_structure


class BasicLayoutScoring:
    name = "basic_layout"

    def score(self, plan: BlueprintPlan) -> ScoreResult:
        validation = validate_plan_structure(plan)
        valid_bonus = 10_000.0 if validation.passed else 0.0
        entity_penalty = len(plan.objects) * 10.0
        belt_penalty = _count_belts(plan) * 5.0
        area_penalty = _used_area(plan) * 3.0
        flow_penalty = _total_flow_length(plan) * 2.0

        total = valid_bonus - entity_penalty - belt_penalty - area_penalty - flow_penalty
        return ScoreResult(
            total=total,
            label=self.name,
            details={
                "valid_bonus": valid_bonus,
                "entity_penalty": entity_penalty,
                "belt_penalty": belt_penalty,
                "area_penalty": area_penalty,
                "flow_penalty": flow_penalty,
            },
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
