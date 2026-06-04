from __future__ import annotations

from factorio_optimizer.core.blueprint_plan import BlueprintPlan
from factorio_optimizer.core.objects import Position
from factorio_optimizer.validation.static_validator import ValidationResult


def validate_plan_structure(plan: BlueprintPlan) -> ValidationResult:
    result = ValidationResult()
    _validate_unique_object_ids(plan, result)
    _validate_bounds(plan, result)
    _validate_overlaps(plan, result)
    _validate_flows(plan, result)
    return result


def _validate_unique_object_ids(plan: BlueprintPlan, result: ValidationResult) -> None:
    seen: set[str] = set()
    for obj in plan.objects:
        if obj.object_id in seen:
            result.add_error(f"Duplicate object id: {obj.object_id}.")
        seen.add(obj.object_id)


def _validate_bounds(plan: BlueprintPlan, result: ValidationResult) -> None:
    for obj in plan.objects:
        for tile in obj.occupied_tiles():
            if tile.x < 0 or tile.y < 0 or tile.x >= plan.width or tile.y >= plan.height:
                result.add_error(
                    f"Object {obj.object_id} is outside grid at ({tile.x}, {tile.y})."
                )


def _validate_overlaps(plan: BlueprintPlan, result: ValidationResult) -> None:
    occupied: dict[Position, str] = {}

    for obj in plan.objects:
        if obj.object_type in {"input_interface", "output_interface"}:
            continue

        for tile in obj.occupied_tiles():
            if tile in occupied:
                result.add_error(
                    f"Overlap at ({tile.x}, {tile.y}): "
                    f"{occupied[tile]} and {obj.object_id}."
                )
            else:
                occupied[tile] = obj.object_id


def _validate_flows(plan: BlueprintPlan, result: ValidationResult) -> None:
    object_ids = {obj.object_id for obj in plan.objects}

    for flow in plan.flows:
        if flow.source_id not in object_ids:
            result.add_error(f"Flow {flow.flow_id} has unknown source {flow.source_id}.")

        if flow.target_id not in object_ids:
            result.add_error(f"Flow {flow.flow_id} has unknown target {flow.target_id}.")

        if not flow.path:
            result.add_error(f"Flow {flow.flow_id} has empty path.")

        for pos in flow.path:
            if pos.x < 0 or pos.y < 0 or pos.x >= plan.width or pos.y >= plan.height:
                result.add_error(
                    f"Flow {flow.flow_id} path leaves grid at ({pos.x}, {pos.y})."
                )
