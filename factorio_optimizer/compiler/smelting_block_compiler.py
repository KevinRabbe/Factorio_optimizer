from __future__ import annotations

from dataclasses import dataclass
from math import ceil
from typing import Any

from factorio_optimizer.core.blueprint_plan import BlueprintPlan
from factorio_optimizer.core.objects import FactoryObject, Position
from factorio_optimizer.data.machines import get_machine
from factorio_optimizer.data.recipes import get_recipe
from factorio_optimizer.export.blueprint_json_exporter import export_plan_to_blueprint_json
from factorio_optimizer.export.blueprint_string_encoder import encode_blueprint_string
from factorio_optimizer.render.ascii_renderer import render_ascii
from factorio_optimizer.validation.structure_validator import validate_plan_structure


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
    height = 2 + row_count * 5

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
    )

    structure = validate_plan_structure(plan)
    blueprint_json = export_plan_to_blueprint_json(plan)
    blueprint_string = encode_blueprint_string(blueprint_json)

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
        structure_valid=structure.passed,
        validation_errors=structure.errors,
        ascii=render_ascii(plan),
        blueprint_json=blueprint_json,
        blueprint_string=blueprint_string,
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
) -> BlueprintPlan:
    objects: list[FactoryObject] = []
    furnace_index = 0

    for row in range(row_count):
        y_base = 1 + row * 5
        row_remaining = machine_count - furnace_index
        row_furnaces = min(furnaces_per_row, row_remaining)

        for x in range(width):
            objects.append(_belt(f"row_{row}_input_belt_{x}", x, y_base, input_item))
            objects.append(_belt(f"row_{row}_output_belt_{x}", x, y_base + 4, output_item))

        for col in range(row_furnaces):
            x_base = 2 + col * 3
            objects.append(
                FactoryObject(
                    object_id=f"furnace_{furnace_index}",
                    object_type="furnace",
                    position=Position(x_base, y_base + 1),
                    direction="north",
                    width=2,
                    height=2,
                    recipe=recipe_name,
                    role="producer",
                    entity_name=machine_name.replace("_", "-"),
                )
            )
            objects.append(
                FactoryObject(
                    object_id=f"furnace_{furnace_index}_input_inserter",
                    object_type="inserter",
                    position=Position(x_base, y_base),
                    direction="south",
                    item=input_item,
                    role="ingredient_transfer",
                    entity_name="inserter",
                )
            )
            objects.append(
                FactoryObject(
                    object_id=f"furnace_{furnace_index}_output_inserter",
                    object_type="inserter",
                    position=Position(x_base, y_base + 3),
                    direction="south",
                    item=output_item,
                    role="product_transfer",
                    entity_name="inserter",
                )
            )
            furnace_index += 1

    return BlueprintPlan(
        plan_id=f"central_{recipe_name}_smelting_block",
        width=width,
        height=height,
        objects=objects,
    )


def _belt(object_id: str, x: int, y: int, item: str) -> FactoryObject:
    return FactoryObject(
        object_id=object_id,
        object_type="belt",
        position=Position(x, y),
        direction="east",
        item=item,
        entity_name="transport-belt",
    )


def _single_item(items: dict[str, float]) -> str:
    if len(items) != 1:
        raise ValueError("Smelting block compiler currently supports exactly one input/output item.")
    return next(iter(items.keys()))
