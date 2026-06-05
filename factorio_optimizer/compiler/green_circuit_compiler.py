from __future__ import annotations

from dataclasses import dataclass
from math import ceil
from typing import Any

from factorio_optimizer.core.blueprint_plan import BlueprintPlan
from factorio_optimizer.compiler.blueprint_blocks import (
    assembler,
    belt_line,
    compile_blueprint_artifacts,
    electric_pole,
    inserter,
)
from factorio_optimizer.data.belts import get_belt
from factorio_optimizer.data.inserters import get_inserter
from factorio_optimizer.data.machines import get_machine
from factorio_optimizer.data.recipes import get_recipe


@dataclass(frozen=True)
class GreenCircuitBlockRequest:
    target_rate_per_second: float = 1.0
    era: str = "mid"
    machine_name: str | None = None
    belt_name: str = "transport_belt"
    inserter_name: str = "inserter"
    include_power_poles: bool = True


@dataclass(frozen=True)
class GreenCircuitBlockReport:
    target_rate_per_second: float
    target_rate_per_minute: float
    era: str
    machine_name: str
    belt_name: str
    inserter_name: str
    green_assembler_count: int
    cable_assembler_count: int
    capacity_per_second: float
    valid: bool
    validation_errors: list[str]
    validation_confidence: dict[str, object]
    ascii: str
    blueprint_json: dict[str, Any]
    blueprint_string: str
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


def compile_green_circuit_block(request: GreenCircuitBlockRequest) -> GreenCircuitBlockReport:
    if request.target_rate_per_second <= 0:
        raise ValueError("target_rate_per_second must be greater than zero.")

    machine_name = request.machine_name or _default_machine_for_era(request.era)
    machine = get_machine(machine_name)
    belt = get_belt(request.belt_name)
    inserter = get_inserter(request.inserter_name)
    green_recipe = get_recipe("electronic_circuit")
    cable_recipe = get_recipe("copper_cable")

    green_rate_each = _recipe_output_rate(green_recipe.outputs["electronic_circuit"], green_recipe.crafting_time_seconds, machine.crafting_speed)
    cable_rate_each = _recipe_output_rate(cable_recipe.outputs["copper_cable"], cable_recipe.crafting_time_seconds, machine.crafting_speed)
    green_assemblers = max(1, ceil(request.target_rate_per_second / green_rate_each))
    cable_required = request.target_rate_per_second * green_recipe.inputs["copper_cable"]
    cable_assemblers = max(1, ceil(cable_required / cable_rate_each))
    cell_count = max(green_assemblers, cable_assemblers)
    capacity_per_second = green_assemblers * green_rate_each

    plan = _build_plan(
        cell_count=cell_count,
        green_assemblers=green_assemblers,
        cable_assemblers=cable_assemblers,
        machine_name=machine_name,
        belt_name=request.belt_name,
        inserter_name=request.inserter_name,
        include_power_poles=request.include_power_poles,
    )
    artifacts = compile_blueprint_artifacts(plan)

    summary = {
        "item": "electronic_circuit",
        "target_rate_per_second": round(request.target_rate_per_second, 6),
        "target_rate_per_minute": round(request.target_rate_per_second * 60.0, 4),
        "capacity_per_second": round(capacity_per_second, 6),
        "capacity_per_minute": round(capacity_per_second * 60.0, 4),
        "green_assembler_count": green_assemblers,
        "cable_assembler_count": cable_assemblers,
    }
    build_list = {
        "assemblers": green_assemblers + cable_assemblers,
        "transport_belts": sum(1 for obj in plan.objects if obj.object_type == "belt"),
        "inserters": sum(1 for obj in plan.objects if obj.object_type == "inserter"),
        "small_electric_poles": sum(1 for obj in plan.objects if obj.object_type == "electric_pole"),
    }
    diagnostics = {
        "belt_capacity_per_second": belt.items_per_second,
        "inserter_capacity_per_second": inserter.estimated_items_per_second,
        "external_inputs": {
            "iron_plate": round(request.target_rate_per_second, 6),
            "copper_plate": round(cable_required / 2.0, 6),
        },
        "output_item": "electronic_circuit",
        "include_power_poles": request.include_power_poles,
    }

    return GreenCircuitBlockReport(
        target_rate_per_second=request.target_rate_per_second,
        target_rate_per_minute=request.target_rate_per_second * 60.0,
        era=request.era,
        machine_name=machine_name,
        belt_name=request.belt_name,
        inserter_name=request.inserter_name,
        green_assembler_count=green_assemblers,
        cable_assembler_count=cable_assemblers,
        capacity_per_second=capacity_per_second,
        valid=artifacts.valid,
        validation_errors=artifacts.validation_errors,
        validation_confidence=artifacts.validation.to_dict(),
        ascii=artifacts.ascii,
        blueprint_json=artifacts.blueprint_json,
        blueprint_string=artifacts.blueprint_string,
        summary=summary,
        build_list=build_list,
        diagnostics=diagnostics,
    )


def _build_plan(
    cell_count: int,
    green_assemblers: int,
    cable_assemblers: int,
    machine_name: str,
    belt_name: str,
    inserter_name: str,
    include_power_poles: bool,
) -> BlueprintPlan:
    cell_width = 8
    width = cell_count * cell_width + 1
    height = 13
    objects = []

    objects.extend(belt_line("copper_input_belt", 0, 0, width, "copper_plate", "east", belt_name))

    for cell in range(cell_count):
        x_base = cell * cell_width
        active_cable = cell < cable_assemblers
        active_green = cell < green_assemblers

        objects.extend(belt_line(f"cell_{cell}_iron_input_belt", x_base, 6, height - 6, "iron_plate", "south", belt_name))
        objects.extend(belt_line(f"cell_{cell}_output_belt", x_base + 6, 7, height - 7, "electronic_circuit", "south", belt_name))

        if active_cable:
            objects.append(inserter(f"cell_{cell}_copper_input_inserter", x_base + 3, 1, "south", "copper_plate", "ingredient_transfer", inserter_name))
            objects.append(assembler(f"cell_{cell}_copper_cable_assembler", x_base + 2, 2, "copper_cable", machine_name))

        if active_green:
            objects.append(inserter(f"cell_{cell}_cable_to_green_inserter", x_base + 3, 5, "south", "copper_cable", "ingredient_transfer", inserter_name))
            objects.append(assembler(f"cell_{cell}_green_circuit_assembler", x_base + 2, 6, "electronic_circuit", machine_name))
            objects.append(inserter(f"cell_{cell}_iron_input_inserter", x_base + 1, 7, "east", "iron_plate", "ingredient_transfer", inserter_name))
            objects.append(inserter(f"cell_{cell}_output_inserter", x_base + 5, 7, "east", "electronic_circuit", "product_transfer", inserter_name))

        if include_power_poles:
            objects.append(electric_pole(f"cell_{cell}_cable_power_pole", x_base + 5, 3))
            objects.append(electric_pole(f"cell_{cell}_green_power_pole", x_base + 5, 9))

    return BlueprintPlan(
        plan_id="green_circuit_block_v1",
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
