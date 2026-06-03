from __future__ import annotations

from dataclasses import dataclass

from factorio_optimizer.core.blueprint_plan import BlueprintPlan
from factorio_optimizer.validation.static_validator import ValidationResult


@dataclass(frozen=True)
class RecipeValidationSpec:
    recipe: str
    input_items: tuple[str, ...]
    output_item: str


def validate_recipe_plan(plan: BlueprintPlan, spec: RecipeValidationSpec) -> ValidationResult:
    result = ValidationResult()

    _validate_recipe_assembler(plan, spec, result)
    _validate_input_interfaces(plan, spec, result)
    _validate_output_interface(plan, spec, result)
    _validate_recipe_flows(plan, spec, result)

    return result


def _validate_recipe_assembler(
    plan: BlueprintPlan,
    spec: RecipeValidationSpec,
    result: ValidationResult,
) -> None:
    matching_assemblers = [
        obj
        for obj in plan.objects
        if obj.object_type == "assembler" and obj.recipe == spec.recipe
    ]

    if not matching_assemblers:
        result.add_error(f"Missing assembler with recipe {spec.recipe}.")


def _validate_input_interfaces(
    plan: BlueprintPlan,
    spec: RecipeValidationSpec,
    result: ValidationResult,
) -> None:
    for item in spec.input_items:
        matching_inputs = [
            obj
            for obj in plan.objects
            if obj.object_type == "input_interface" and obj.item == item
        ]

        if not matching_inputs:
            result.add_error(f"Missing input interface for {item}.")


def _validate_output_interface(
    plan: BlueprintPlan,
    spec: RecipeValidationSpec,
    result: ValidationResult,
) -> None:
    matching_outputs = [
        obj
        for obj in plan.objects
        if obj.object_type == "output_interface" and obj.item == spec.output_item
    ]

    if not matching_outputs:
        result.add_error(f"Missing output interface for {spec.output_item}.")


def _validate_recipe_flows(
    plan: BlueprintPlan,
    spec: RecipeValidationSpec,
    result: ValidationResult,
) -> None:
    flow_items = {flow.item for flow in plan.flows}

    for item in spec.input_items:
        if item not in flow_items:
            result.add_error(f"Missing flow for input item {item}.")

    if spec.output_item not in flow_items:
        result.add_error(f"Missing flow for output item {spec.output_item}.")
