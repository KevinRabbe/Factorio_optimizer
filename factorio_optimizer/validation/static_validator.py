from __future__ import annotations

from factorio_optimizer.core.blueprint_plan import BlueprintPlan
from factorio_optimizer.validation.blueprint_validator import (
    RecipeValidationSpec,
    ValidationResult,
    validate_blueprint_plan,
)


def validate_plan(plan: BlueprintPlan) -> ValidationResult:
    result = validate_blueprint_plan(
        plan,
        recipe_spec=RecipeValidationSpec(
            recipe="iron_gear_wheel",
            input_items=("iron_plate",),
            output_item="iron_gear_wheel",
        ),
        check_placement=True,
    )
    _validate_legacy_iron_gear_flow_ids(plan, result)
    return result


def _validate_legacy_iron_gear_flow_ids(plan: BlueprintPlan, result: ValidationResult) -> None:
    input_flow = next((flow for flow in plan.flows if flow.flow_id == "iron_to_assembler"), None)
    if input_flow is None:
        result.add_error("Missing iron_to_assembler flow.")
    elif input_flow.item != "iron_plate":
        result.add_error("iron_to_assembler flow carries wrong item.")

    output_flow = next((flow for flow in plan.flows if flow.flow_id == "gear_to_output"), None)
    if output_flow is None:
        result.add_error("Missing gear_to_output flow.")
    elif output_flow.item != "iron_gear_wheel":
        result.add_error("gear_to_output flow carries wrong item.")
