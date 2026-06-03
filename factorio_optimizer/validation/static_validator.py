from __future__ import annotations

from factorio_optimizer.core.blueprint_plan import BlueprintPlan
from factorio_optimizer.core.objects import Position


class ValidationResult:
    def __init__(self) -> None:
        self.errors: list[str] = []

    @property
    def passed(self) -> bool:
        return len(self.errors) == 0

    def add_error(self, message: str) -> None:
        self.errors.append(message)


def validate_plan(plan: BlueprintPlan) -> ValidationResult:
    result = ValidationResult()

    _validate_required_objects(plan, result)
    _validate_bounds(plan, result)
    _validate_overlaps(plan, result)
    _validate_flows(plan, result)
    _validate_iron_gear_logic(plan, result)

    return result


def _validate_required_objects(plan: BlueprintPlan, result: ValidationResult) -> None:
    object_types = {obj.object_type for obj in plan.objects}

    if "input_interface" not in object_types:
        result.add_error("Missing input interface.")

    if "output_interface" not in object_types:
        result.add_error("Missing output interface.")

    if "assembler" not in object_types:
        result.add_error("Missing assembler.")

    if "inserter" not in object_types:
        result.add_error("Missing inserter.")


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
        # Interfaces are abstract ports during the planner stage.
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


def _validate_iron_gear_logic(plan: BlueprintPlan, result: ValidationResult) -> None:
    assembler = plan.get_object("gear_maker")
    if assembler is None:
        result.add_error("Missing gear_maker assembler.")
        return

    if assembler.recipe != "iron_gear_wheel":
        result.add_error("gear_maker has wrong recipe.")

    iron_input = plan.get_object("iron_input")
    if iron_input is None or iron_input.item != "iron_plate":
        result.add_error("Missing iron_plate input.")

    gear_output = plan.get_object("gear_output")
    if gear_output is None or gear_output.item != "iron_gear_wheel":
        result.add_error("Missing iron_gear_wheel output.")

    input_flow = next(
        (flow for flow in plan.flows if flow.flow_id == "iron_to_assembler"),
        None,
    )
    if input_flow is None:
        result.add_error("Missing iron_to_assembler flow.")
    elif input_flow.item != "iron_plate":
        result.add_error("iron_to_assembler flow carries wrong item.")

    output_flow = next(
        (flow for flow in plan.flows if flow.flow_id == "gear_to_output"),
        None,
    )
    if output_flow is None:
        result.add_error("Missing gear_to_output flow.")
    elif output_flow.item != "iron_gear_wheel":
        result.add_error("gear_to_output flow carries wrong item.")
