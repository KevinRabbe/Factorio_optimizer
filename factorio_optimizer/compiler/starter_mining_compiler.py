from __future__ import annotations

from dataclasses import dataclass

from factorio_optimizer.compiler.blueprint_blocks import (
    belt_line,
    build_entity_counts,
    compile_blueprint_artifacts,
    electric_pole,
    io_lane,
    miner,
)
from factorio_optimizer.compiler.connectors import belt_output
from factorio_optimizer.compiler.mid_tier_compiler import FactoryBlueprintReport
from factorio_optimizer.core.blueprint_plan import BlueprintPlan
from factorio_optimizer.core.objects import FactoryObject
from factorio_optimizer.data.items import get_item
from factorio_optimizer.data.machines import get_machine


STARTER_MINING_ITEMS = {"iron_ore", "copper_ore", "coal"}
STARTER_MINING_SIZE_MODES = {"bootstrap_12": 12, "half_yellow_15": 15, "full_yellow_30": 30}
_DEFAULT_MINERS_PER_ROW = {
    "bootstrap_12": 6,
    "half_yellow_15": 8,
    "full_yellow_30": 15,
}
_RESOURCE_YIELDS_PER_SECOND = {
    "burner_mining_drill": 0.25,
    "electric_mining_drill": 0.5,
}
_TARGET_BELT_ITEMS_PER_SECOND = {
    "bootstrap_12": 6.0,
    "half_yellow_15": 7.5,
    "full_yellow_30": 15.0,
}


@dataclass(frozen=True)
class StarterMiningRequest:
    item: str
    miner_name: str = "electric_mining_drill"
    belt_name: str = "transport_belt"
    include_power_poles: bool = True
    size_mode: str = "full_yellow_30"


def compile_starter_mining_block(request: StarterMiningRequest) -> FactoryBlueprintReport:
    if request.item not in STARTER_MINING_ITEMS:
        raise ValueError(f"Starter mining block does not support item {request.item!r}.")
    if request.size_mode not in STARTER_MINING_SIZE_MODES:
        raise ValueError("Starter mining size_mode must be one of: bootstrap_12, half_yellow_15, full_yellow_30.")

    machine = get_machine(request.miner_name)
    if machine.machine_type != "miner":
        raise ValueError(f"Machine {request.miner_name!r} is not a mining drill.")

    item_meta = get_item(request.item)
    miner_count = STARTER_MINING_SIZE_MODES[request.size_mode]
    miners_per_row = _DEFAULT_MINERS_PER_ROW[request.size_mode]
    row_count = 2
    rate_per_miner = _RESOURCE_YIELDS_PER_SECOND[request.miner_name]
    estimated_output_per_second = miner_count * rate_per_miner
    power_required_kw = machine.power_kw * miner_count if machine.energy_source == "electric" else 0.0
    target_belt_items_per_second = _TARGET_BELT_ITEMS_PER_SECOND[request.size_mode]
    intended_feed = (
        "one full yellow smelter line"
        if request.size_mode == "full_yellow_30"
        else "half of a full yellow smelter line"
        if request.size_mode == "half_yellow_15"
        else "starter bootstrap expansion"
    )

    plan = _build_plan(
        item=request.item,
        machine_name=request.miner_name,
        belt_name=request.belt_name,
        include_power_poles=request.include_power_poles,
        miner_count=miner_count,
        miners_per_row=miners_per_row,
    )
    artifacts = compile_blueprint_artifacts(plan)

    connectors = [
        belt_output(
            f"{request.item}_output",
            request.item,
            side="right",
            direction="east",
            rate_per_second=estimated_output_per_second,
            belt_tier=request.belt_name,
            description=f"Main {request.item} output belt; {intended_feed}.",
            connects_to=(f"{request.item}_input",),
        )
    ]

    diagnostics = {
        "external_inputs": {},
        "connectors": connectors,
        "ore_output_rate": round(estimated_output_per_second * 60.0, 4),
        "estimated_output_per_second": round(estimated_output_per_second, 6),
        "target_belt_items_per_second": target_belt_items_per_second,
        "target_belt_tier": "yellow",
        "belt_output_side": "right",
        "power_requirement_kw": round(power_required_kw, 4),
        "power_mode": machine.energy_source,
        "intended_feed": intended_feed,
        "patch_use_note": "Repeat this chunk along the patch edge, then merge ore belts into your smelting backbone.",
        "layout_shape": "two_row_center_output_lane",
        "output_lanes": {
            request.item: {
                "main_bus_start": {"x": 0, "y": 4},
                "exits_right": True,
                "pattern": "center ore output belt",
            },
        },
        "external_input_lanes": {
            request.item: [{"pattern": "miners feed inward toward the center output belt"}],
        },
        "warnings": (
            ["Electric miners need poles built before the chunk will run."]
            if machine.energy_source == "electric" and not request.include_power_poles
            else []
        ),
    }
    summary = {
        "item": request.item,
        "display_name": item_meta.display_name,
        "block_mode": request.size_mode,
        "miner_count": miner_count,
        "miners_per_row": miners_per_row,
        "row_count": row_count,
        "capacity_per_second": round(estimated_output_per_second, 6),
        "capacity_per_minute": round(estimated_output_per_second * 60.0, 4),
        "machine_count": miner_count,
    }

    return FactoryBlueprintReport(
        valid=artifacts.valid,
        validation_errors=artifacts.validation_errors,
        validation_confidence=artifacts.validation.to_dict(),
        blueprint_string=artifacts.blueprint_string,
        blueprint_json=artifacts.blueprint_json,
        ascii=artifacts.ascii,
        summary=summary,
        build_list=build_entity_counts(plan),
        diagnostics=diagnostics,
    )


def _build_plan(
    item: str,
    machine_name: str,
    belt_name: str,
    include_power_poles: bool,
    miner_count: int,
    miners_per_row: int,
) -> BlueprintPlan:
    top_row_count = (miner_count + 1) // 2
    bottom_row_count = miner_count - top_row_count
    max_row_count = max(top_row_count, bottom_row_count)
    width = 1 + max_row_count * 4 + 2
    height = 9
    output_y = 4
    top_y = 1
    bottom_y = 5
    objects: list[FactoryObject] = []

    objects.extend(belt_line("ore_output_belt", 0, output_y, width, item, "east", belt_name))

    for index in range(top_row_count):
        x_base = 1 + index * 4
        objects.append(miner(f"top_miner_{index}", x_base, top_y, item, machine_name, "south"))
    for index in range(bottom_row_count):
        x_base = 1 + index * 4
        objects.append(miner(f"bottom_miner_{index}", x_base, bottom_y, item, machine_name, "north"))

    if include_power_poles and machine_name == "electric_mining_drill":
        pole_positions = [4 + index * 8 for index in range((max_row_count + 1) // 2)]
        for pole_index, x in enumerate(pole_positions):
            objects.append(electric_pole(f"top_power_pole_{pole_index}", x, 0))
            objects.append(electric_pole(f"bottom_power_pole_{pole_index}", x, 8))

    objects.append(io_lane(f"{item}_output_interface", width - 1, output_y, item, "output_interface"))

    return BlueprintPlan(
        plan_id=f"starter_{item}_mining_chunk",
        width=width,
        height=height,
        objects=objects,
    )
