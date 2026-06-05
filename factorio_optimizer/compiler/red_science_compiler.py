from __future__ import annotations

from dataclasses import dataclass
from math import ceil
from typing import Any

from factorio_optimizer.compiler.blueprint_blocks import (
    assembler,
    belt_line,
    compile_blueprint_artifacts,
    electric_pole,
    inserter,
)
from factorio_optimizer.core.blueprint_plan import BlueprintPlan
from factorio_optimizer.data.belts import get_belt
from factorio_optimizer.data.inserters import get_inserter
from factorio_optimizer.data.machines import get_machine
from factorio_optimizer.data.recipes import get_recipe


@dataclass(frozen=True)
class RedScienceBlockRequest:
    target_rate_per_second: float = 0.5
    era: str = "early"
    machine_name: str | None = None
    belt_name: str = "transport_belt"
    inserter_name: str = "inserter"
    include_power_poles: bool = True


@dataclass(frozen=True)
class RedScienceBlockReport:
    valid: bool
    validation_errors: list[str]
    validation_confidence: dict[str, object]
    blueprint_string: str
    blueprint_json: dict[str, Any]
    ascii: str
    summary: dict[str, Any]
    build_list: dict[str, Any]
    diagnostics: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "valid": self.valid,
            "validation_errors": self.validation_errors,
            "validation_confidence": self.validation_confidence,
            "blueprint_string": self.blueprint_string,
            "blueprint_json": self.blueprint_json,
            "ascii": self.ascii,
            "summary": self.summary,
            "build_list": self.build_list,
            "diagnostics": self.diagnostics,
        }


def compile_red_science_block(request: RedScienceBlockRequest) -> RedScienceBlockReport:
    if request.target_rate_per_second <= 0:
        raise ValueError("target_rate_per_second must be greater than zero.")

    machine_name = request.machine_name or _default_machine_for_era(request.era)
    machine = get_machine(machine_name)
    belt = get_belt(request.belt_name)
    inserter_data = get_inserter(request.inserter_name)
    science_recipe = get_recipe("automation_science_pack")
    gear_recipe = get_recipe("iron_gear_wheel")

    science_rate_each = _recipe_output_rate(
        science_recipe.outputs["automation_science_pack"],
        science_recipe.crafting_time_seconds,
        machine.crafting_speed,
    )
    gear_rate_each = _recipe_output_rate(
        gear_recipe.outputs["iron_gear_wheel"],
        gear_recipe.crafting_time_seconds,
        machine.crafting_speed,
    )
    science_assemblers = max(1, ceil(request.target_rate_per_second / science_rate_each))
    gear_required = request.target_rate_per_second * science_recipe.inputs["iron_gear_wheel"]
    gear_assemblers = max(1, ceil(gear_required / gear_rate_each))

    plan = _build_plan(
        science_assemblers=science_assemblers,
        gear_assemblers=gear_assemblers,
        machine_name=machine_name,
        belt_name=request.belt_name,
        inserter_name=request.inserter_name,
        include_power_poles=request.include_power_poles,
    )
    artifacts = compile_blueprint_artifacts(plan)
    capacity_per_second = science_assemblers * science_rate_each
    iron_for_gears_per_second = gear_required * gear_recipe.inputs["iron_plate"]

    summary = {
        "item": "automation_science_pack",
        "target_rate_per_second": round(request.target_rate_per_second, 6),
        "target_rate_per_minute": round(request.target_rate_per_second * 60.0, 4),
        "capacity_per_second": round(capacity_per_second, 6),
        "capacity_per_minute": round(capacity_per_second * 60.0, 4),
        "science_assembler_count": science_assemblers,
        "gear_assembler_count": gear_assemblers,
    }
    build_list = {
        "assemblers": science_assemblers + gear_assemblers,
        "transport_belts": sum(1 for obj in plan.objects if obj.object_type == "belt"),
        "inserters": sum(1 for obj in plan.objects if obj.object_type == "inserter"),
        "small_electric_poles": sum(1 for obj in plan.objects if obj.object_type == "electric_pole"),
    }
    diagnostics = {
        "belt_capacity_per_second": belt.items_per_second,
        "inserter_capacity_per_second": inserter_data.estimated_items_per_second,
        "external_inputs": {
            "copper_plate": round(request.target_rate_per_second, 6),
            "iron_plate": round(iron_for_gears_per_second, 6),
        },
        "intermediate": {
            "iron_gear_wheel": round(gear_required, 6),
        },
        "output_item": "automation_science_pack",
        "include_power_poles": request.include_power_poles,
    }

    return RedScienceBlockReport(
        valid=artifacts.valid,
        validation_errors=artifacts.validation_errors,
        validation_confidence=artifacts.validation.to_dict(),
        blueprint_string=artifacts.blueprint_string,
        blueprint_json=artifacts.blueprint_json,
        ascii=artifacts.ascii,
        summary=summary,
        build_list=build_list,
        diagnostics=diagnostics,
    )


def _build_plan(
    science_assemblers: int,
    gear_assemblers: int,
    machine_name: str,
    belt_name: str,
    inserter_name: str,
    include_power_poles: bool,
) -> BlueprintPlan:
    science_cell_width = 6
    science_start_x = 8
    width = science_start_x + science_assemblers * science_cell_width + 1
    height = 13
    objects = []

    objects.extend(belt_line("iron_input_belt", 0, 1, width, "iron_plate", "east", belt_name))
    objects.append(inserter("gear_iron_input_inserter", 3, 2, "south", "iron_plate", "ingredient_transfer", inserter_name))
    objects.append(assembler("gear_assembler_0", 2, 3, "iron_gear_wheel", machine_name))
    objects.append(inserter("gear_output_inserter", 5, 4, "east", "iron_gear_wheel", "product_transfer", inserter_name))
    objects.extend(belt_line("gear_output_belt", 6, 4, width - 6, "iron_gear_wheel", "east", belt_name))

    if include_power_poles:
        objects.append(electric_pole("gear_power_pole", 5, 6))

    for science_index in range(science_assemblers):
        x_base = science_start_x + science_index * science_cell_width
        objects.append(inserter(f"science_{science_index}_gear_input_inserter", x_base + 1, 5, "south", "iron_gear_wheel", "ingredient_transfer", inserter_name))
        objects.append(assembler(f"science_{science_index}_assembler", x_base, 6, "automation_science_pack", machine_name))
        objects.extend(belt_line(f"science_{science_index}_copper_input_belt", x_base + 2, 12, 3, "copper_plate", "north", belt_name))
        objects.append(inserter(f"science_{science_index}_copper_input_inserter", x_base + 2, 9, "north", "copper_plate", "ingredient_transfer", inserter_name))
        objects.append(inserter(f"science_{science_index}_output_inserter", x_base + 3, 7, "east", "automation_science_pack", "product_transfer", inserter_name))
        objects.extend(belt_line(f"science_{science_index}_output_belt", x_base + 4, 7, height - 7, "automation_science_pack", "south", belt_name))
        if include_power_poles:
            objects.append(electric_pole(f"science_{science_index}_power_pole", x_base + 3, 6))

    return BlueprintPlan(
        plan_id="red_science_block_v1",
        width=width,
        height=height,
        objects=objects,
    )


def _default_machine_for_era(era: str) -> str:
    if era == "early":
        return "assembling_machine_1"
    if era == "mid":
        return "assembling_machine_2"
    if era == "end":
        return "assembling_machine_3"
    raise ValueError(f"Unsupported era: {era!r}")


def _recipe_output_rate(output_amount: float, crafting_time: float, crafting_speed: float) -> float:
    return output_amount * crafting_speed / crafting_time
