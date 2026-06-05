from __future__ import annotations

from dataclasses import dataclass
from math import ceil
from typing import Any

from factorio_optimizer.compiler.blueprint_blocks import (
    assembler,
    belt,
    chemical_plant,
    compile_blueprint_artifacts,
    electric_pole,
    furnace,
    inserter,
    io_lane,
    lab,
    pipe,
)
from factorio_optimizer.core.blueprint_plan import BlueprintPlan
from factorio_optimizer.core.objects import FactoryObject
from factorio_optimizer.data.belts import get_belt
from factorio_optimizer.data.inserters import get_inserter
from factorio_optimizer.data.recipes import Recipe, get_recipe


_FLUID_ITEMS = {
    "water",
    "crude_oil",
    "petroleum_gas",
    "heavy_oil",
    "light_oil",
    "lubricant",
    "sulfuric_acid",
}

_MID_BLOCK_ITEMS = {
    "steel_plate",
    "advanced_circuit",
    "engine_unit",
    "plastic_bar",
    "sulfur",
    "sulfuric_acid",
    "battery",
    "piercing_rounds_magazine",
    "grenade",
    "stone_wall",
    "fast_inserter",
    "fast_transport_belt",
    "logistic_science_pack",
    "military_science_pack",
    "electric_engine_unit",
    "flying_robot_frame",
}


@dataclass(frozen=True)
class FactoryBlueprintReport:
    valid: bool
    validation_errors: list[str]
    validation_confidence: dict[str, object]
    blueprint_string: str
    blueprint_json: dict[str, Any]
    ascii: str
    summary: dict[str, Any]
    build_list: dict[str, int]
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


@dataclass(frozen=True)
class MidBlockRequest:
    item: str
    target_rate_per_second: float = 0.5
    machine_tier: str = "mid"
    transport_tier: str = "mid"
    fluid_mode: str = "external"
    include_power_poles: bool = True


@dataclass(frozen=True)
class ScienceSliceRequest:
    target_rate_per_second: float = 0.5
    machine_tier: str = "mid"
    transport_tier: str = "mid"
    fluid_mode: str = "external"
    include_power_poles: bool = True


@dataclass(frozen=True)
class MidTierSliceRequest:
    item: str
    target_rate_per_second: float = 0.5
    machine_tier: str = "mid"
    transport_tier: str = "mid"
    fluid_mode: str = "external"
    strategy: str = "readable"
    include_power_poles: bool = True


def compile_mid_block(request: MidBlockRequest) -> FactoryBlueprintReport:
    if request.target_rate_per_second <= 0:
        raise ValueError("target_rate_per_second must be greater than zero.")
    if request.fluid_mode != "external":
        raise ValueError("Only fluid_mode='external' is supported for mid-tier v1.")
    if request.item not in _MID_BLOCK_ITEMS:
        raise ValueError(f"Unsupported mid-tier block item: {request.item!r}.")

    recipe = get_recipe(request.item)
    machine_name = _machine_for_recipe(recipe, request.machine_tier)
    machine_speed = _machine_speed(machine_name)
    output_amount = recipe.outputs.get(request.item, next(iter(recipe.outputs.values())))
    rate_each = output_amount * machine_speed / recipe.crafting_time_seconds
    machine_count = max(1, ceil(request.target_rate_per_second / rate_each))

    plan = _build_cell_plan(
        plan_id=f"{request.item}_mid_block_v1",
        cells=[(request.item, machine_count)],
        target_item=request.item,
        machine_tier=request.machine_tier,
        transport_tier=request.transport_tier,
        include_power_poles=request.include_power_poles,
        include_lab=False,
    )
    return _report_from_plan(
        plan=plan,
        item=request.item,
        target_rate_per_second=request.target_rate_per_second,
        capacity_per_second=machine_count * rate_each,
        machine_count=machine_count,
        transport_tier=request.transport_tier,
        fluid_mode=request.fluid_mode,
        external_inputs=_estimate_recipe_external_inputs(recipe, request.target_rate_per_second, request.item),
    )


def compile_early_science_slice(request: ScienceSliceRequest) -> FactoryBlueprintReport:
    if request.target_rate_per_second <= 0:
        raise ValueError("target_rate_per_second must be greater than zero.")

    cells = [
        ("iron_gear_wheel", 1),
        ("electronic_circuit", 1),
        ("transport_belt", 1),
        ("inserter", 1),
        ("automation_science_pack", max(1, ceil(request.target_rate_per_second / _recipe_rate("automation_science_pack", request.machine_tier)))),
        ("logistic_science_pack", max(1, ceil(request.target_rate_per_second / _recipe_rate("logistic_science_pack", request.machine_tier)))),
    ]
    plan = _build_cell_plan(
        plan_id="early_science_connected_slice_v1",
        cells=cells,
        target_item="logistic_science_pack",
        machine_tier=request.machine_tier,
        transport_tier=request.transport_tier,
        include_power_poles=request.include_power_poles,
        include_lab=True,
    )
    return _report_from_plan(
        plan=plan,
        item="early_science_slice",
        target_rate_per_second=request.target_rate_per_second,
        capacity_per_second=request.target_rate_per_second,
        machine_count=sum(count for _, count in cells),
        transport_tier=request.transport_tier,
        fluid_mode=request.fluid_mode,
        external_inputs=_estimate_slice_external_inputs(cells, request.target_rate_per_second),
    )


def compile_blue_science_slice(request: ScienceSliceRequest) -> FactoryBlueprintReport:
    if request.target_rate_per_second <= 0:
        raise ValueError("target_rate_per_second must be greater than zero.")
    if request.fluid_mode != "external":
        raise ValueError("Only fluid_mode='external' is supported for blue science v1.")

    cells = [
        ("plastic_bar", 1),
        ("sulfur", 1),
        ("sulfuric_acid", 1),
        ("advanced_circuit", 1),
        ("engine_unit", 1),
        ("chemical_science_pack", max(1, ceil(request.target_rate_per_second / _recipe_rate("chemical_science_pack", request.machine_tier)))),
    ]
    science_count = max(1, ceil(request.target_rate_per_second / _recipe_rate("chemical_science_pack", request.machine_tier)))
    plan = _build_blue_science_connected_plan(
        science_assemblers=science_count,
        machine_tier=request.machine_tier,
        transport_tier=request.transport_tier,
        include_power_poles=request.include_power_poles,
    )
    report = _report_from_plan(
        plan=plan,
        item="chemical_science_pack",
        target_rate_per_second=request.target_rate_per_second,
        capacity_per_second=request.target_rate_per_second,
        machine_count=sum(count for _, count in cells),
        transport_tier=request.transport_tier,
        fluid_mode=request.fluid_mode,
        external_inputs=_estimate_slice_external_inputs(cells, request.target_rate_per_second),
    )
    report.diagnostics["lane_labels"] = {
        "advanced_circuit_input_lane": "feed advanced circuits into the left-side science assembler input belts",
        "engine_unit_input_lane": "feed engines onto the lower shared science input belt",
        "sulfuric_acid_taps": "connect sulfuric acid to each pipe tap beside science assemblers",
        "science_output_lane": "shared belt fed by every science assembler, with a lab drop and right-edge exit",
    }
    report.diagnostics["external_input_lanes"] = {
        "petroleum_gas": [{"x": 7, "y": 3}, {"x": 15, "y": 3}],
        "water": [{"x": 15, "y": 4}, {"x": 23, "y": 3}],
        "iron_plate": [{"x": 21, "y": 1}],
        "sulfur": [{"x": 18, "y": 4}],
        "copper_cable": [{"x": 5, "y": 10}],
        "electronic_circuit": [{"x": 4, "y": 16}],
        "plastic_bar": [{"x": 2, "y": 13}],
        "steel_plate": [{"x": 15, "y": 10}],
        "iron_gear_wheel": [{"x": 14, "y": 16}],
        "pipe": [{"x": 12, "y": 13}],
        "advanced_circuit": [{"x": 32, "y": 11}],
        "engine_unit": [{"x": 34, "y": 14}],
        "sulfuric_acid": [{"pattern": "chemical_science_{index}_acid_tap"}],
    }
    report.diagnostics["output_lanes"] = {
        "chemical_science_pack": {
            "main_bus_start": {"x": 36, "y": 8},
            "exits_right": True,
            "feeds_lab": True,
        }
    }
    return report


def compile_mid_tier_slice(request: MidTierSliceRequest) -> FactoryBlueprintReport:
    if request.target_rate_per_second <= 0:
        raise ValueError("target_rate_per_second must be greater than zero.")
    if request.strategy not in {"readable", "compact", "external_fluids", "external_plates", "include_smelting"}:
        raise ValueError("strategy must be one of: readable, compact, external_fluids, external_plates, include_smelting.")

    if request.item == "chemical_science_pack":
        report = compile_blue_science_slice(
            ScienceSliceRequest(
                target_rate_per_second=request.target_rate_per_second,
                machine_tier=request.machine_tier,
                transport_tier=request.transport_tier,
                fluid_mode=request.fluid_mode,
                include_power_poles=request.include_power_poles,
            )
        )
        report.diagnostics["planner_mode"] = "connected_blue_science_slice"
    elif request.item in {"automation_science_pack", "logistic_science_pack"}:
        report = compile_early_science_slice(
            ScienceSliceRequest(
                target_rate_per_second=request.target_rate_per_second,
                machine_tier=request.machine_tier,
                transport_tier=request.transport_tier,
                fluid_mode=request.fluid_mode,
                include_power_poles=request.include_power_poles,
            )
        )
        report.diagnostics["planner_mode"] = "connected_early_science_slice"
    else:
        report = compile_mid_block(
            MidBlockRequest(
                item=request.item,
                target_rate_per_second=request.target_rate_per_second,
                machine_tier=request.machine_tier,
                transport_tier=request.transport_tier,
                fluid_mode=request.fluid_mode,
                include_power_poles=request.include_power_poles,
            )
        )
        report.diagnostics["planner_mode"] = "single_mid_block"

    report.diagnostics["strategy"] = request.strategy
    report.diagnostics["planner_supported_scope"] = "vanilla_mid_tier_external_fluids"
    return report


def _build_cell_plan(
    plan_id: str,
    cells: list[tuple[str, int]],
    target_item: str,
    machine_tier: str,
    transport_tier: str,
    include_power_poles: bool,
    include_lab: bool,
) -> BlueprintPlan:
    objects: list[FactoryObject] = []
    cursor_x = 4
    max_height = 13
    for recipe_name, count in cells:
        for index in range(count):
            cell_id = f"{recipe_name}_{index}"
            objects.extend(
                _machine_cell(
                    prefix=cell_id,
                    x=cursor_x,
                    y=4,
                    recipe_name=recipe_name,
                    machine_tier=machine_tier,
                    transport_tier=transport_tier,
                    include_power_poles=include_power_poles,
                )
            )
            cursor_x += 8

    if include_lab:
        objects.append(lab("science_lab_0", cursor_x, 4))
        objects.append(belt("science_input_belt_0", cursor_x - 2, 5, target_item, "east", _belt_for_tier(transport_tier)))
        objects.append(inserter("science_lab_input_inserter_0", cursor_x - 1, 5, "east", target_item, "ingredient_transfer", _inserter_for_tier(transport_tier)))
        if include_power_poles:
            objects.append(electric_pole("science_lab_power_pole", cursor_x + 3, 5, _pole_for_tier(machine_tier)))
        cursor_x += 5

    width = max(cursor_x + 2, 12)
    objects.append(io_lane("external_inputs", 0, 0, "external_inputs", "input_interface"))
    objects.append(io_lane("main_output", width - 1, max_height - 1, target_item, "output_interface"))
    return BlueprintPlan(plan_id=plan_id, width=width, height=max_height, objects=objects)


def _build_blue_science_connected_plan(
    science_assemblers: int,
    machine_tier: str,
    transport_tier: str,
    include_power_poles: bool,
) -> BlueprintPlan:
    belt_name = _belt_for_tier(transport_tier)
    inserter_name = _inserter_for_tier(transport_tier)
    pole_name = _pole_for_tier(machine_tier)
    machine_name = "assembling_machine_2"
    science_start_x = 34
    science_spacing = 6
    width = science_start_x + science_assemblers * science_spacing + 8
    height = 22
    objects: list[FactoryObject] = [
        io_lane("external_inputs", 0, 0, "external_inputs", "input_interface"),
        io_lane("main_output", width - 1, height - 1, "chemical_science_pack", "output_interface"),
        chemical_plant("plastic_bar_plant", 4, 3, "plastic_bar"),
        pipe("plastic_petroleum_input", 7, 3, "petroleum_gas", "south"),
        chemical_plant("sulfur_plant", 12, 3, "sulfur"),
        pipe("sulfur_petroleum_input", 15, 3, "petroleum_gas", "south"),
        pipe("sulfur_water_input", 15, 4, "water", "south"),
        chemical_plant("sulfuric_acid_plant", 20, 3, "sulfuric_acid"),
        pipe("acid_water_input", 23, 3, "water", "south"),
        pipe("acid_output_pipe", 23, 4, "sulfuric_acid", "south"),
        belt("acid_iron_input_belt", 21, 1, "iron_plate", "south", belt_name, role="input_lane_endpoint"),
        inserter("acid_iron_input_inserter", 21, 2, "south", "iron_plate", "ingredient_transfer", inserter_name),
        belt("acid_sulfur_input_belt", 18, 4, "sulfur", "east", belt_name, role="input_lane_endpoint"),
        inserter("acid_sulfur_input_inserter", 19, 4, "east", "sulfur", "ingredient_transfer", inserter_name),
        assembler("advanced_circuit_assembler", 4, 12, "advanced_circuit", machine_name),
        belt("advanced_copper_cable_input_belt", 5, 10, "copper_cable", "south", belt_name, role="input_lane_endpoint"),
        inserter("advanced_copper_cable_input_inserter", 5, 11, "south", "copper_cable", "ingredient_transfer", inserter_name),
        belt("advanced_ec_input_belt", 4, 16, "electronic_circuit", "north", belt_name, role="input_lane_endpoint"),
        inserter("advanced_ec_input_inserter", 4, 15, "north", "electronic_circuit", "ingredient_transfer", inserter_name),
        belt("advanced_plastic_input_belt", 2, 13, "plastic_bar", "east", belt_name, role="input_lane_endpoint"),
        inserter("advanced_plastic_input_inserter", 3, 13, "east", "plastic_bar", "ingredient_transfer", inserter_name),
        inserter("advanced_output_inserter", 6, 15, "south", "advanced_circuit", "product_transfer", inserter_name),
        belt("advanced_output_belt_0", 6, 16, "advanced_circuit", "south", belt_name),
        belt("advanced_output_belt_1", 6, 17, "advanced_circuit", "south", belt_name),
        assembler("engine_unit_assembler", 14, 12, "engine_unit", machine_name),
        belt("engine_steel_input_belt", 15, 10, "steel_plate", "south", belt_name, role="input_lane_endpoint"),
        inserter("engine_steel_input_inserter", 15, 11, "south", "steel_plate", "ingredient_transfer", inserter_name),
        belt("engine_gear_input_belt", 14, 16, "iron_gear_wheel", "north", belt_name, role="input_lane_endpoint"),
        inserter("engine_gear_input_inserter", 14, 15, "north", "iron_gear_wheel", "ingredient_transfer", inserter_name),
        belt("engine_pipe_input_belt", 12, 13, "pipe", "east", belt_name, role="input_lane_endpoint"),
        inserter("engine_pipe_input_inserter", 13, 13, "east", "pipe", "ingredient_transfer", inserter_name),
        inserter("engine_output_inserter", 16, 15, "south", "engine_unit", "product_transfer", inserter_name),
        belt("engine_output_belt_0", 16, 16, "engine_unit", "south", belt_name),
        belt("engine_output_belt_1", 16, 17, "engine_unit", "south", belt_name),
    ]

    objects.extend(
        belt(f"advanced_output_stub_{y}", 6, y, "advanced_circuit", "south", belt_name)
        for y in range(18, height)
    )
    objects.extend(
        belt(f"engine_output_stub_{y}", 16, y, "engine_unit", "south", belt_name)
        for y in range(18, height)
    )

    engine_lane_length = science_assemblers * science_spacing
    objects.extend(
        belt(
            object_id=f"engine_unit_shared_lane_{index}",
            x=science_start_x + index,
            y=14,
            item="engine_unit",
            direction="east",
            belt_name=belt_name,
            role="input_lane_endpoint" if index == engine_lane_length - 1 else "transport",
        )
        for index in range(engine_lane_length)
    )

    for index in range(science_assemblers):
        x = science_start_x + index * science_spacing
        objects.append(assembler(f"chemical_science_assembler_{index}", x, 10, "chemical_science_pack", machine_name))
        objects.append(belt(f"chemical_science_{index}_advanced_input_belt", x - 2, 11, "advanced_circuit", "east", belt_name, role="input_lane_endpoint"))
        objects.append(inserter(f"chemical_science_{index}_advanced_input", x - 1, 11, "east", "advanced_circuit", "ingredient_transfer", inserter_name))
        objects.append(pipe(f"chemical_science_{index}_acid_tap", x, 13, "sulfuric_acid", "east"))
        objects.append(inserter(f"chemical_science_{index}_engine_input", x + 1, 13, "north", "engine_unit", "ingredient_transfer", inserter_name))
        objects.append(inserter(f"chemical_science_{index}_output", x + 2, 9, "north", "chemical_science_pack", "product_transfer", inserter_name))
        if include_power_poles:
            objects.append(electric_pole(f"chemical_science_{index}_power_pole", x + 4, 10, pole_name))

    output_lane_y = 8
    output_lane_start_x = science_start_x + 2
    output_lane_end_x = width - 1
    for lane_x in range(output_lane_start_x, output_lane_end_x + 1):
        objects.append(belt(f"chemical_science_output_lane_{lane_x}", lane_x, output_lane_y, "chemical_science_pack", "east", belt_name))
    lab_drop_x = width - 4
    for drop_y in range(output_lane_y + 1, 13):
        objects.append(belt(f"chemical_science_lab_drop_{drop_y}", lab_drop_x, drop_y, "chemical_science_pack", "south", belt_name))
    objects.append(belt("chemical_science_lab_drop_input", lab_drop_x, 13, "chemical_science_pack", "south", belt_name))

    objects.append(lab("science_lab_0", width - 5, 15))
    objects.append(inserter("science_lab_input_inserter", width - 4, 14, "south", "chemical_science_pack", "ingredient_transfer", inserter_name))

    if include_power_poles:
        for pole_index, (x, y) in enumerate([(8, 5), (16, 5), (24, 5), (8, 14), (18, 14), (width - 2, 16)]):
            objects.append(electric_pole(f"blue_slice_power_pole_{pole_index}", x, y, pole_name))

    return BlueprintPlan(plan_id="blue_science_connected_slice_v2", width=width, height=height, objects=objects)


def _machine_cell(
    prefix: str,
    x: int,
    y: int,
    recipe_name: str,
    machine_tier: str,
    transport_tier: str,
    include_power_poles: bool,
) -> list[FactoryObject]:
    recipe = get_recipe(recipe_name)
    machine_name = _machine_for_recipe(recipe, machine_tier)
    belt_name = _belt_for_tier(transport_tier)
    inserter_name = _inserter_for_tier(transport_tier)
    objects: list[FactoryObject] = []

    if recipe.category == "smelting":
        machine = furnace(f"{prefix}_machine", x, y, recipe_name, machine_name)
    elif recipe.category == "chemistry":
        machine = chemical_plant(f"{prefix}_machine", x, y, recipe_name)
    else:
        machine = assembler(f"{prefix}_machine", x, y, recipe_name, machine_name)
    objects.append(machine)

    solid_inputs = [item for item in recipe.inputs if item not in _FLUID_ITEMS]
    fluid_inputs = [item for item in recipe.inputs if item in _FLUID_ITEMS]
    input_slots = [
        (x + 1, y - 2, "south", x + 1, y - 1),
        (x, y + 4, "north", x, y + 3),
        (x - 2, y + 1, "east", x - 1, y + 1),
    ]
    for slot_index, item in enumerate(solid_inputs[:3]):
        belt_x, belt_y, direction, inserter_x, inserter_y = input_slots[slot_index]
        objects.append(belt(f"{prefix}_{item}_input_belt", belt_x, belt_y, item, direction, belt_name))
        objects.append(inserter(f"{prefix}_{item}_input_inserter", inserter_x, inserter_y, direction, item, "ingredient_transfer", inserter_name))

    for fluid_index, item in enumerate(fluid_inputs):
        objects.append(pipe(f"{prefix}_{item}_fluid_pipe", x + 3, y + fluid_index, item, "south"))

    output_item = next(iter(recipe.outputs))
    output_x = x + min(2, machine.width - 1)
    output_inserter_y = y + machine.height
    objects.append(inserter(f"{prefix}_{output_item}_output_inserter", output_x, output_inserter_y, "south", output_item, "product_transfer", inserter_name))
    output_belt_count = max(1, 12 - output_inserter_y)
    for output_index in range(output_belt_count):
        objects.append(belt(f"{prefix}_{output_item}_output_belt_{output_index}", output_x, output_inserter_y + 1 + output_index, output_item, "south", belt_name))

    if include_power_poles:
        objects.append(electric_pole(f"{prefix}_power_pole", x + 4, y + 1, _pole_for_tier(machine_tier)))
    return objects


def _report_from_plan(
    plan: BlueprintPlan,
    item: str,
    target_rate_per_second: float,
    capacity_per_second: float,
    machine_count: int,
    transport_tier: str,
    fluid_mode: str,
    external_inputs: dict[str, float] | None = None,
) -> FactoryBlueprintReport:
    artifacts = compile_blueprint_artifacts(plan)
    external_inputs = external_inputs or _external_inputs_for_plan(plan)
    build_list: dict[str, int] = {}
    for obj in plan.objects:
        if obj.object_type in {"input_interface", "output_interface"}:
            continue
        key = (obj.entity_name or obj.object_type).replace("-", "_") + "s"
        build_list[key] = build_list.get(key, 0) + 1
    diagnostics = {
        "external_inputs": external_inputs,
        "fluid_mode": fluid_mode,
        "transport_tier": transport_tier,
        "belt_capacity_per_second": get_belt(_belt_for_tier(transport_tier)).items_per_second,
        "inserter_capacity_per_second": get_inserter(_inserter_for_tier(transport_tier)).estimated_items_per_second,
        "warnings": [] if artifacts.valid else ["Blueprint failed practical validation."],
    }
    return FactoryBlueprintReport(
        valid=artifacts.valid,
        validation_errors=artifacts.validation_errors,
        validation_confidence=artifacts.validation.to_dict(),
        blueprint_string=artifacts.blueprint_string,
        blueprint_json=artifacts.blueprint_json,
        ascii=artifacts.ascii,
        summary={
            "item": item,
            "target_rate_per_second": round(target_rate_per_second, 6),
            "target_rate_per_minute": round(target_rate_per_second * 60.0, 4),
            "capacity_per_second": round(capacity_per_second, 6),
            "capacity_per_minute": round(capacity_per_second * 60.0, 4),
            "machine_count": machine_count,
        },
        build_list=build_list,
        diagnostics=diagnostics,
    )


def _external_inputs_for_plan(plan: BlueprintPlan) -> dict[str, float]:
    inputs: dict[str, float] = {}
    for obj in plan.objects:
        if obj.role in {"ingredient_transfer", "fluid_transport"} and obj.item:
            inputs.setdefault(obj.item, 0.0)
    return inputs


def _estimate_recipe_external_inputs(recipe: Recipe, target_rate_per_second: float, output_item: str) -> dict[str, float]:
    output_amount = recipe.outputs.get(output_item, next(iter(recipe.outputs.values())))
    crafts_per_second = target_rate_per_second / output_amount
    return {
        item: round(amount * crafts_per_second, 6)
        for item, amount in recipe.inputs.items()
    }


def _estimate_slice_external_inputs(cells: list[tuple[str, int]], target_rate_per_second: float) -> dict[str, float]:
    produced_items = {recipe_name for recipe_name, _ in cells}
    inputs: dict[str, float] = {}
    for recipe_name, _ in cells:
        recipe = get_recipe(recipe_name)
        output_amount = next(iter(recipe.outputs.values()))
        crafts_per_second = target_rate_per_second / output_amount
        for item, amount in recipe.inputs.items():
            if item in produced_items:
                continue
            inputs[item] = round(inputs.get(item, 0.0) + amount * crafts_per_second, 6)
    return inputs


def _machine_for_recipe(recipe: Recipe, machine_tier: str) -> str:
    if recipe.category == "smelting":
        return "steel_furnace" if machine_tier == "mid" else "stone_furnace"
    if recipe.category == "chemistry":
        return "chemical_plant"
    if recipe.category == "oil_processing":
        return "oil_refinery"
    if recipe.category == "crafting-with-fluid":
        return "assembling_machine_2"
    return "assembling_machine_2" if machine_tier == "mid" else "assembling_machine_1"


def _machine_speed(machine_name: str) -> float:
    speeds = {
        "assembling_machine_1": 0.5,
        "assembling_machine_2": 0.75,
        "stone_furnace": 1.0,
        "steel_furnace": 2.0,
        "electric_furnace": 2.0,
        "chemical_plant": 1.25,
        "oil_refinery": 1.0,
    }
    return speeds[machine_name]


def _recipe_rate(recipe_name: str, machine_tier: str) -> float:
    recipe = get_recipe(recipe_name)
    machine_name = _machine_for_recipe(recipe, machine_tier)
    output_amount = next(iter(recipe.outputs.values()))
    return output_amount * _machine_speed(machine_name) / recipe.crafting_time_seconds


def _belt_for_tier(transport_tier: str) -> str:
    return "fast_transport_belt" if transport_tier == "mid" else "transport_belt"


def _inserter_for_tier(transport_tier: str) -> str:
    return "fast_inserter" if transport_tier == "mid" else "inserter"


def _pole_for_tier(machine_tier: str) -> str:
    return "medium_electric_pole" if machine_tier == "mid" else "small_electric_pole"
