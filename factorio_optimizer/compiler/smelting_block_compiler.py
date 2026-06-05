from __future__ import annotations

from dataclasses import dataclass
from math import ceil
from typing import Any

from factorio_optimizer.core.blueprint_plan import BlueprintPlan
from factorio_optimizer.compiler.blueprint_blocks import (
    belt_line,
    build_entity_counts,
    compile_blueprint_artifacts,
    furnace,
    inserter,
)
from factorio_optimizer.data.entities import get_entity_spec
from factorio_optimizer.data.machines import get_machine
from factorio_optimizer.data.recipes import get_recipe


SMELTING_RECIPES = {"iron_plate", "copper_plate", "steel_plate", "stone_brick"}


@dataclass(frozen=True)
class SmeltingBlockRequest:
    recipe_name: str
    target_rate_per_second: float
    machine_name: str = "stone_furnace"
    belt_name: str = "transport_belt"
    inserter_name: str = "inserter"
    max_furnaces_per_row: int = 12


@dataclass(frozen=True)
class SmeltingBlockReport:
    recipe_name: str
    input_item: str
    output_item: str
    target_rate_per_second: float
    target_rate_per_minute: float
    machine_name: str
    machine_count_exact: float
    machine_count: int
    row_count: int
    furnaces_per_row: int
    width: int
    height: int
    structure_valid: bool
    validation_errors: list[str]
    validation_confidence: dict[str, object]
    ascii: str
    blueprint_json: dict[str, Any]
    blueprint_string: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "recipe_name": self.recipe_name,
            "input_item": self.input_item,
            "output_item": self.output_item,
            "target_rate_per_second": round(self.target_rate_per_second, 6),
            "target_rate_per_minute": round(self.target_rate_per_minute, 4),
            "machine_name": self.machine_name,
            "machine_count_exact": round(self.machine_count_exact, 4),
            "machine_count": self.machine_count,
            "row_count": self.row_count,
            "furnaces_per_row": self.furnaces_per_row,
            "width": self.width,
            "height": self.height,
            "structure_valid": self.structure_valid,
            "valid": self.structure_valid,
            "validation_errors": self.validation_errors,
            "validation_confidence": self.validation_confidence,
            "ascii": self.ascii,
            "blueprint_json": self.blueprint_json,
            "blueprint_string": self.blueprint_string,
        }


def compile_smelting_block(request: SmeltingBlockRequest) -> SmeltingBlockReport:
    recipe = get_recipe(request.recipe_name)
    machine = get_machine(request.machine_name)

    if request.recipe_name not in SMELTING_RECIPES or recipe.category != "smelting":
        raise ValueError(f"Recipe {request.recipe_name!r} is not supported by the smelting block compiler.")
    if "smelting" not in machine.allowed_categories:
        raise ValueError(f"Machine {request.machine_name!r} cannot smelt.")
    if request.target_rate_per_second <= 0:
        raise ValueError("target_rate_per_second must be greater than zero.")

    input_item = _single_item(recipe.inputs)
    output_item = _single_item(recipe.outputs)
    output_per_craft = recipe.outputs[output_item]
    crafts_per_second_per_machine = machine.crafting_speed / recipe.crafting_time_seconds
    output_per_second_per_machine = crafts_per_second_per_machine * output_per_craft
    machine_count_exact = request.target_rate_per_second / output_per_second_per_machine
    machine_count = max(1, ceil(machine_count_exact))

    max_per_row = max(1, request.max_furnaces_per_row)
    row_count = ceil(machine_count / max_per_row)
    furnaces_per_row = min(machine_count, max_per_row)
    width = 4 + furnaces_per_row * 3
    height = row_count * 7
    machine_spec = get_entity_spec(request.machine_name.replace("_", "-"))

    plan = _build_plan(
        recipe_name=request.recipe_name,
        input_item=input_item,
        output_item=output_item,
        machine_name=request.machine_name,
        machine_count=machine_count,
        row_count=row_count,
        furnaces_per_row=furnaces_per_row,
        width=width,
        height=height,
        machine_width=machine_spec.width,
        machine_height=machine_spec.height,
        belt_name=request.belt_name,
        inserter_name=request.inserter_name,
    )

    artifacts = compile_blueprint_artifacts(plan)

    return SmeltingBlockReport(
        recipe_name=request.recipe_name,
        input_item=input_item,
        output_item=output_item,
        target_rate_per_second=request.target_rate_per_second,
        target_rate_per_minute=request.target_rate_per_second * 60.0,
        machine_name=request.machine_name,
        machine_count_exact=machine_count_exact,
        machine_count=machine_count,
        row_count=row_count,
        furnaces_per_row=furnaces_per_row,
        width=plan.width,
        height=plan.height,
        structure_valid=artifacts.valid,
        validation_errors=artifacts.validation_errors,
        validation_confidence=artifacts.validation.to_dict(),
        ascii=artifacts.ascii,
        blueprint_json=artifacts.blueprint_json,
        blueprint_string=artifacts.blueprint_string,
    )


def _build_plan(
    recipe_name: str,
    input_item: str,
    output_item: str,
    machine_name: str,
    machine_count: int,
    row_count: int,
    furnaces_per_row: int,
    width: int,
    height: int,
    machine_width: int,
    machine_height: int,
    belt_name: str,
    inserter_name: str,
) -> BlueprintPlan:
    objects = []
    furnace_index = 0

    for row in range(row_count):
        y_base = row * 7
        row_remaining = machine_count - furnace_index
        row_furnaces = min(furnaces_per_row, row_remaining)

        objects.extend(belt_line(f"row_{row}_input_belt", 0, y_base, width, input_item, "east", belt_name))
        objects.extend(belt_line(f"row_{row}_output_belt", 0, y_base + 5, width, output_item, "east", belt_name))

        for col in range(row_furnaces):
            x_base = 2 + col * 3
            objects.append(
                furnace(
                    f"furnace_{furnace_index}",
                    x_base,
                    y_base + 2,
                    recipe_name,
                    machine_name,
                    width=machine_width,
                    height=machine_height,
                )
            )
            objects.append(
                inserter(
                    f"furnace_{furnace_index}_input_inserter",
                    x_base,
                    y_base + 1,
                    "south",
                    input_item,
                    "ingredient_transfer",
                    inserter_name,
                )
            )
            objects.append(
                inserter(
                    f"furnace_{furnace_index}_output_inserter",
                    x_base,
                    y_base + 4,
                    "south",
                    output_item,
                    "product_transfer",
                    inserter_name,
                )
            )
            furnace_index += 1

    return BlueprintPlan(
        plan_id=f"central_{recipe_name}_smelting_block",
        width=width,
        height=height,
        objects=objects,
    )
def _single_item(items: dict[str, float]) -> str:
    if len(items) != 1:
        raise ValueError("Smelting block compiler currently supports exactly one input/output item.")
    return next(iter(items.keys()))
