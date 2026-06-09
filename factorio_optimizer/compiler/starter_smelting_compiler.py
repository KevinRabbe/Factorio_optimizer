from __future__ import annotations

from dataclasses import dataclass
from math import ceil

from factorio_optimizer.compiler.blueprint_blocks import (
    belt_line,
    build_entity_counts,
    chest,
    compile_blueprint_artifacts,
    furnace,
    inserter,
    io_lane,
)
from factorio_optimizer.compiler.connectors import belt_input, belt_output, manual_input
from factorio_optimizer.compiler.mid_tier_compiler import FactoryBlueprintReport
from factorio_optimizer.core.blueprint_plan import BlueprintPlan
from factorio_optimizer.core.objects import FactoryObject
from factorio_optimizer.data.entities import get_entity_spec
from factorio_optimizer.data.machines import get_machine
from factorio_optimizer.data.recipes import get_recipe


STARTER_SMELTING_RECIPES = {"iron_plate", "copper_plate", "steel_plate", "stone_brick"}
STARTER_SMELTING_SIZE_MODES = {
    "starter_12": 12,
    "compact_16": 16,
    "brick_24": 24,
    "standard_32": 32,
    "full_belt_48": 48,
}
_DEFAULT_FURNACES_PER_ROW = {
    "starter_12": 6,
    "compact_16": 16,
    "brick_24": 12,
    "standard_32": 16,
    "full_belt_48": 24,
}


@dataclass(frozen=True)
class StarterSmeltingRequest:
    recipe_name: str
    target_rate_per_second: float
    size_mode: str | None = None
    machine_name: str = "stone_furnace"
    belt_name: str = "transport_belt"
    ore_inserter_name: str = "burner_inserter"
    fuel_inserter_name: str = "burner_inserter"
    output_inserter_name: str = "burner_inserter"
    fuel_item: str = "coal"
    fuel_buffer_name: str = "iron_chest"
    max_furnaces_per_row: int = 8


def compile_starter_smelting_block(request: StarterSmeltingRequest) -> FactoryBlueprintReport:
    recipe = get_recipe(request.recipe_name)
    machine = get_machine(request.machine_name)

    if request.recipe_name not in STARTER_SMELTING_RECIPES or recipe.category != "smelting":
        raise ValueError(f"Recipe {request.recipe_name!r} is not supported by the starter smelting compiler.")
    if "smelting" not in machine.allowed_categories:
        raise ValueError(f"Machine {request.machine_name!r} cannot smelt.")
    if request.target_rate_per_second <= 0:
        raise ValueError("target_rate_per_second must be greater than zero.")
    if machine.energy_source != "burner":
        raise ValueError("Starter smelting block currently supports burner furnaces only.")
    if request.size_mode is not None and request.size_mode not in STARTER_SMELTING_SIZE_MODES:
        raise ValueError(
            "Starter smelting size_mode must be one of: starter_12, compact_16, brick_24, standard_32, full_belt_48."
        )

    input_item = _single_item(recipe.inputs)
    output_item = _single_item(recipe.outputs)
    output_per_craft = recipe.outputs[output_item]
    crafts_per_second_per_machine = machine.crafting_speed / recipe.crafting_time_seconds
    output_per_second_per_machine = crafts_per_second_per_machine * output_per_craft
    rate_based_exact = request.target_rate_per_second / output_per_second_per_machine
    rate_based_machine_count = max(1, ceil(rate_based_exact))
    machine_count = (
        STARTER_SMELTING_SIZE_MODES[request.size_mode]
        if request.size_mode is not None
        else rate_based_machine_count
    )
    selected_mode = request.size_mode or "rate_based"

    default_row_size = _DEFAULT_FURNACES_PER_ROW.get(request.size_mode or "", request.max_furnaces_per_row)
    furnaces_per_row = min(machine_count, max(1, default_row_size))
    row_count = ceil(machine_count / furnaces_per_row)
    width = 4 + furnaces_per_row * 4
    height = row_count * 7
    furnace_spec = get_entity_spec(request.machine_name.replace("_", "-"))

    plan = _build_plan(
        recipe_name=request.recipe_name,
        input_item=input_item,
        output_item=output_item,
        machine_name=request.machine_name,
        selected_mode=selected_mode,
        fuel_item=request.fuel_item,
        machine_count=machine_count,
        row_count=row_count,
        furnaces_per_row=furnaces_per_row,
        width=width,
        height=height,
        machine_width=furnace_spec.width,
        machine_height=furnace_spec.height,
        belt_name=request.belt_name,
        ore_inserter_name=request.ore_inserter_name,
        fuel_inserter_name=request.fuel_inserter_name,
        output_inserter_name=request.output_inserter_name,
        fuel_buffer_name=request.fuel_buffer_name,
    )
    artifacts = compile_blueprint_artifacts(plan)
    build_list = build_entity_counts(plan)
    capacity_per_second = machine_count * output_per_second_per_machine
    capacity_per_minute = capacity_per_second * 60.0
    input_per_craft = recipe.inputs[input_item]
    input_rate_per_second = machine_count * crafts_per_second_per_machine * input_per_craft
    input_rate_per_minute = input_rate_per_second * 60.0
    is_mirrored_layout = selected_mode in {"starter_12", "brick_24", "full_belt_48"}
    if selected_mode == "full_belt_48":
        upgrade_note = "Mainline iron/copper smelting backbone with 24 furnaces per side, sized for one full yellow belt and ready for later steel-furnace upgrades."
        intended_output = "one full yellow plate line"
        furnaces_per_side = 24
    elif selected_mode == "brick_24":
        upgrade_note = "Starter brick line sized for one yellow stone input and half a yellow belt of stone bricks."
        intended_output = "half of a yellow brick line"
        furnaces_per_side = 12
    elif selected_mode == "starter_12":
        upgrade_note = "Starter steel support block sized for early mall and science demand, not a full-belt steel backbone."
        intended_output = "starter steel support output"
        furnaces_per_side = 6
    elif selected_mode == "standard_32":
        upgrade_note = "Good default for large starting patches; scales toward a full yellow-belt line later."
        intended_output = "partial yellow plate line"
        furnaces_per_side = furnaces_per_row
    else:
        upgrade_note = "Starter burner smelting block sized for practical early expansion."
        intended_output = "starter burner smelting output"
        furnaces_per_side = furnaces_per_row

    output_belt_target = (
        30.0
        if request.machine_name == "steel_furnace" and selected_mode == "full_belt_48"
        else 15.0
        if selected_mode == "full_belt_48"
        else 7.5
        if selected_mode == "brick_24"
        else round(capacity_per_second, 6)
    )
    target_belt_tier = "yellow" if request.machine_name == "stone_furnace" else "red"
    diagnostics = {
        "external_inputs": {
            input_item: round(input_rate_per_second, 6),
        },
        "connectors": _build_connectors(
            input_item=input_item,
            output_item=output_item,
            fuel_item=request.fuel_item,
            input_rate_per_second=input_rate_per_second,
            output_rate_per_second=capacity_per_second,
            output_belt_target=output_belt_target,
            belt_name=request.belt_name,
            is_mirrored_layout=is_mirrored_layout,
        ),
        "fuel_delivery": "local_coal_chests",
        "fuel_buffers": machine_count,
        "ore_input_rate": round(input_rate_per_minute, 4),
        "output_rate": round(capacity_per_minute, 4),
        "coal_support": "one local coal chest per furnace",
        "upgrade_note": upgrade_note,
        "intended_output": intended_output,
        "target_belt_tier": target_belt_tier,
        "target_output_belt_items_per_second": output_belt_target,
        "layout_shape": f"mirrored_double_row_{furnaces_per_side}_per_side" if is_mirrored_layout else "single_or_compact_rows",
        "furnaces_per_side": furnaces_per_side,
        "input_lanes": {
            "ore_lane": input_item,
            "fuel_buffer_item": request.fuel_item,
            "output_lane": output_item,
        },
        "external_input_lanes": {
            input_item: (
                [{"pattern": "top ore belt feeds the upper row"}, {"pattern": "bottom ore belt feeds the lower row"}]
                if is_mirrored_layout
                else [{"pattern": "main ore belt along the top row"}]
            ),
        },
        **(
            {"upstream_plate_demand_per_minute": round(input_rate_per_minute, 4)}
            if request.recipe_name == "steel_plate"
            else {}
        ),
        "output_lanes": {
            output_item: {
                "main_bus_start": {"x": 0, "y": 5 if is_mirrored_layout else height - 1},
                "exits_right": True,
                "pattern": "center output belt" if is_mirrored_layout else "front output belt",
            },
        },
        "build_stage_note": (
            "Starter smelting uses stone furnaces with one local coal chest per furnace. "
            "Feed ore by belt, top up coal chests manually or from a nearby coal lane."
        ),
        "warnings": [
            "Coal fueling is local-buffer based in this first burner smelting pass.",
            "Use this as a bootstrap smelting upgrade before a cleaner shared fuel bus.",
        ],
    }
    summary = {
        "item": request.recipe_name,
        "furnace_count": machine_count,
        "block_mode": selected_mode,
        "machine_count": machine_count,
        "capacity_per_second": round(capacity_per_second, 6),
        "capacity_per_minute": round(capacity_per_minute, 4),
        "row_count": row_count,
        "furnaces_per_row": furnaces_per_row,
        "furnaces_per_side": furnaces_per_side,
        "fuel_buffers": machine_count,
    }

    return FactoryBlueprintReport(
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


def _build_connectors(
    *,
    input_item: str,
    output_item: str,
    fuel_item: str,
    input_rate_per_second: float,
    output_rate_per_second: float,
    output_belt_target: float,
    belt_name: str,
    is_mirrored_layout: bool,
) -> list[dict[str, object]]:
    lane_count = 2 if is_mirrored_layout else 1
    return [
        belt_input(
            f"{input_item}_input",
            input_item,
            side="left",
            direction="east",
            rate_per_second=input_rate_per_second,
            belt_tier=belt_name,
            lane_count=lane_count,
            description="Ore or plate input for the smelting block.",
            connects_to=(f"{input_item}_output",),
        ),
        manual_input(
            f"{fuel_item}_manual_fuel_input",
            fuel_item,
            description="Local fuel chest input for burner furnaces; replace with a fuel belt in a later connector version.",
        ),
        belt_output(
            f"{output_item}_output",
            output_item,
            side="right",
            direction="east",
            rate_per_second=min(output_rate_per_second, output_belt_target),
            belt_tier=belt_name,
            description="Main smelted output belt leaving toward the bus, mall, or next production block.",
            connects_to=(f"{output_item}_input",),
        ),
    ]


def _build_plan(
    recipe_name: str,
    input_item: str,
    output_item: str,
    machine_name: str,
    selected_mode: str,
    fuel_item: str,
    machine_count: int,
    row_count: int,
    furnaces_per_row: int,
    width: int,
    height: int,
    machine_width: int,
    machine_height: int,
    belt_name: str,
    ore_inserter_name: str,
    fuel_inserter_name: str,
    output_inserter_name: str,
    fuel_buffer_name: str,
) -> BlueprintPlan:
    if selected_mode in {"starter_12", "brick_24", "full_belt_48"}:
        return _build_mirrored_smelting_plan(
            recipe_name=recipe_name,
            input_item=input_item,
            output_item=output_item,
            machine_name=machine_name,
            fuel_item=fuel_item,
            belt_name=belt_name,
            ore_inserter_name=ore_inserter_name,
            fuel_inserter_name=fuel_inserter_name,
            output_inserter_name=output_inserter_name,
            fuel_buffer_name=fuel_buffer_name,
            machine_width=machine_width,
            machine_height=machine_height,
            furnaces_per_side=furnaces_per_row,
        )

    objects: list[FactoryObject] = []
    furnace_index = 0

    for row in range(row_count):
        y_base = row * 7
        row_remaining = machine_count - furnace_index
        row_furnaces = min(furnaces_per_row, row_remaining)

        objects.extend(belt_line(f"row_{row}_ore_belt", 0, y_base, width, input_item, "east", belt_name))
        objects.extend(belt_line(f"row_{row}_output_belt", 0, y_base + 5, width, output_item, "east", belt_name))

        for col in range(row_furnaces):
            x_base = 3 + col * 4
            fuel_chest_id = f"furnace_{furnace_index}_fuel_chest"
            objects.append(
                chest(
                    fuel_chest_id,
                    x_base - 2,
                    y_base + 2,
                    fuel_item,
                    "fuel_buffer",
                    fuel_buffer_name,
                )
            )
            objects.append(
                inserter(
                    f"furnace_{furnace_index}_fuel_inserter",
                    x_base - 1,
                    y_base + 2,
                    "east",
                    fuel_item,
                    "fuel_transfer",
                    fuel_inserter_name,
                )
            )
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
                    f"furnace_{furnace_index}_ore_inserter",
                    x_base,
                    y_base + 1,
                    "south",
                    input_item,
                    "ingredient_transfer",
                    ore_inserter_name,
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
                    output_inserter_name,
                )
            )
            furnace_index += 1

    objects.append(io_lane(f"{input_item}_input_interface", 0, 0, input_item, "input_interface"))
    objects.append(io_lane(f"{fuel_item}_input_interface", 0, 1, fuel_item, "input_interface"))
    objects.append(io_lane(f"{output_item}_output_interface", width - 1, height - 1, output_item, "output_interface"))

    return BlueprintPlan(
        plan_id=f"starter_{recipe_name}_smelting_block",
        width=width,
        height=height,
        objects=objects,
    )


def _single_item(items: dict[str, float]) -> str:
    if len(items) != 1:
        raise ValueError("Starter smelting compiler currently supports exactly one input/output item.")
    return next(iter(items.keys()))


def _build_mirrored_smelting_plan(
    recipe_name: str,
    input_item: str,
    output_item: str,
    machine_name: str,
    fuel_item: str,
    belt_name: str,
    ore_inserter_name: str,
    fuel_inserter_name: str,
    output_inserter_name: str,
    fuel_buffer_name: str,
    machine_width: int,
    machine_height: int,
    furnaces_per_side: int,
) -> BlueprintPlan:
    width = 4 + furnaces_per_side * 4
    height = 11
    center_output_y = 5
    bottom_ore_y = 10
    top_furnace_y = 2
    bottom_furnace_y = 7
    objects: list[FactoryObject] = []

    objects.extend(belt_line("top_ore_belt", 0, 0, width, input_item, "east", belt_name))
    objects.extend(belt_line("center_output_belt", 0, center_output_y, width, output_item, "east", belt_name))
    objects.extend(belt_line("bottom_ore_belt", 0, bottom_ore_y, width, input_item, "east", belt_name))

    for index in range(furnaces_per_side):
        x_base = 3 + index * 4

        top_prefix = f"top_furnace_{index}"
        objects.append(chest(f"{top_prefix}_fuel_chest", x_base - 2, top_furnace_y, fuel_item, "fuel_buffer", fuel_buffer_name))
        objects.append(
            inserter(
                f"{top_prefix}_fuel_inserter",
                x_base - 1,
                top_furnace_y,
                "east",
                fuel_item,
                "fuel_transfer",
                fuel_inserter_name,
            )
        )
        objects.append(
            furnace(
                top_prefix,
                x_base,
                top_furnace_y,
                recipe_name,
                machine_name,
                width=machine_width,
                height=machine_height,
            )
        )
        objects.append(
            inserter(
                f"{top_prefix}_ore_inserter",
                x_base,
                1,
                "south",
                input_item,
                "ingredient_transfer",
                ore_inserter_name,
            )
        )
        objects.append(
            inserter(
                f"{top_prefix}_output_inserter",
                x_base,
                4,
                "south",
                output_item,
                "product_transfer",
                output_inserter_name,
            )
        )

        bottom_prefix = f"bottom_furnace_{index}"
        objects.append(chest(f"{bottom_prefix}_fuel_chest", x_base - 2, bottom_furnace_y, fuel_item, "fuel_buffer", fuel_buffer_name))
        objects.append(
            inserter(
                f"{bottom_prefix}_fuel_inserter",
                x_base - 1,
                bottom_furnace_y,
                "east",
                fuel_item,
                "fuel_transfer",
                fuel_inserter_name,
            )
        )
        objects.append(
            furnace(
                bottom_prefix,
                x_base,
                bottom_furnace_y,
                recipe_name,
                machine_name,
                width=machine_width,
                height=machine_height,
            )
        )
        objects.append(
            inserter(
                f"{bottom_prefix}_ore_inserter",
                x_base,
                9,
                "north",
                input_item,
                "ingredient_transfer",
                ore_inserter_name,
            )
        )
        objects.append(
            inserter(
                f"{bottom_prefix}_output_inserter",
                x_base,
                6,
                "north",
                output_item,
                "product_transfer",
                output_inserter_name,
            )
        )

    objects.append(io_lane(f"{input_item}_input_interface", 0, 0, input_item, "input_interface"))
    objects.append(io_lane(f"{fuel_item}_input_interface", 0, 1, fuel_item, "input_interface"))
    objects.append(io_lane(f"{output_item}_output_interface", width - 1, center_output_y, output_item, "output_interface"))

    return BlueprintPlan(
        plan_id=f"starter_{recipe_name}_smelting_block",
        width=width,
        height=height,
        objects=objects,
    )
