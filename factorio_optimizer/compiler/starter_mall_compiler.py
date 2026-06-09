from __future__ import annotations

from dataclasses import dataclass

from factorio_optimizer.compiler.blueprint_blocks import (
    assembler,
    chest,
    compile_blueprint_artifacts,
    electric_pole,
    io_lane,
    inserter,
)
from factorio_optimizer.compiler.connectors import belt_input, chest_output, manual_input
from factorio_optimizer.compiler.mid_tier_compiler import FactoryBlueprintReport
from factorio_optimizer.core.blueprint_plan import BlueprintPlan
from factorio_optimizer.core.objects import FactoryObject
from factorio_optimizer.data.recipes import get_recipe


_STARTER_MALL_ITEMS = [
    "transport_belt",
    "underground_belt",
    "splitter",
    "inserter",
    "small_electric_pole",
    "pipe",
    "pipe_to_ground",
    "assembling_machine_1",
    "electric_mining_drill",
    "lab",
    "boiler",
    "steam_engine",
    "stone_furnace",
]

_INTERMEDIATE_ITEMS = [
    "iron_gear_wheel",
    "copper_cable",
    "electronic_circuit",
    "iron_stick",
    "transport_belt",
    "pipe",
    "stone_furnace",
]

_BOOTSTRAP_ITEMS = {"stone", "wood"}
_PLATE_ITEMS = {"iron_plate", "copper_plate"}


@dataclass(frozen=True)
class StarterMallRequest:
    include_power_poles: bool = True
    machine_name: str = "assembling_machine_1"
    chest_name: str = "iron_chest"


def compile_starter_mall(request: StarterMallRequest) -> FactoryBlueprintReport:
    plan = _build_starter_mall_plan(request)
    artifacts = compile_blueprint_artifacts(plan)
    build_list: dict[str, int] = {}
    for obj in plan.objects:
        if obj.object_type in {"input_interface", "output_interface"}:
            continue
        key = (obj.entity_name or obj.object_type).replace("-", "_") + "s"
        build_list[key] = build_list.get(key, 0) + 1

    output_chests = {
        obj.item: {"x": obj.position.x, "y": obj.position.y, "chest_id": obj.object_id}
        for obj in plan.objects
        if obj.object_type == "chest" and obj.role == "output_buffer" and obj.item
    }
    intermediate_load = _build_intermediate_load()
    external_inputs = _aggregate_external_inputs(_STARTER_MALL_ITEMS)
    bootstrap_inputs = _aggregate_bootstrap_inputs(_STARTER_MALL_ITEMS)
    diagnostics = {
        "external_inputs": external_inputs,
        "bootstrap_inputs": bootstrap_inputs,
        "connectors": _build_connectors(external_inputs, bootstrap_inputs),
        "output_chests": output_chests,
        "intermediate_load": intermediate_load,
        "build_stage_note": (
            "Starter mall v1 is low-throughput and chest-fed. Feed it from your iron/copper smelting lines, "
            "and seed wood/stone manually for poles, furnaces, and boilers."
        ),
        "feed_from_smelting_note": (
            "Use this after your main iron/copper smelting backbone is online; the mall assumes steady external plates."
        ),
        "warnings": [
            "Starter mall v1 uses local ingredient chests instead of a shared internal bus.",
            "Wood and stone are manual bootstrap inputs in this first version.",
        ],
    }
    summary = {
        "item": "starter_mall",
        "output_count": len(_STARTER_MALL_ITEMS),
        "machine_count": sum(1 for obj in plan.objects if obj.object_type == "assembler"),
        "capacity_per_second": 0.0,
        "capacity_per_minute": float(len(_STARTER_MALL_ITEMS)),
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


def _build_connectors(external_inputs: dict[str, float], bootstrap_inputs: dict[str, float]) -> list[dict[str, object]]:
    connectors: list[dict[str, object]] = []
    for item in sorted(external_inputs):
        connectors.append(
            belt_input(
                f"{item}_input",
                item,
                side="left",
                direction="east",
                rate_per_second=0.0,
                description=f"Chest-fed mall input for {item}; feed from smelting backbone output.",
                connects_to=(f"{item}_output",),
            )
        )
    for item in sorted(bootstrap_inputs):
        connectors.append(
            manual_input(
                f"{item}_manual_input",
                item,
                description=f"Manual bootstrap input for starter mall recipes that need {item}.",
            )
        )
    for item in _STARTER_MALL_ITEMS:
        connectors.append(
            chest_output(
                f"{item}_chest_output",
                item,
                description=f"Mall output chest for {item}.",
            )
        )
    return connectors


def _build_starter_mall_plan(request: StarterMallRequest) -> BlueprintPlan:
    width = 84
    height = 48
    objects: list[FactoryObject] = []

    objects.extend(_build_intermediate_yard(request, x=1, y=1))
    objects.extend(_build_output_block(request, x=1, y=18, items=_STARTER_MALL_ITEMS[:7]))
    objects.extend(_build_output_block(request, x=43, y=18, items=_STARTER_MALL_ITEMS[7:]))

    for item in _PLATE_ITEMS:
        objects.append(io_lane(f"{item}_input_interface", 0, 0 if item == "iron_plate" else 1, item, "input_interface"))
    for item in _BOOTSTRAP_ITEMS:
        objects.append(io_lane(f"{item}_input_interface", 0, 2 if item == "stone" else 3, item, "input_interface"))
    for index, item in enumerate(_STARTER_MALL_ITEMS):
        objects.append(io_lane(f"{item}_output_interface", width - 1, index, item, "output_interface"))

    return BlueprintPlan(
        plan_id="starter_mall_v1",
        width=width,
        height=height,
        objects=objects,
    )


def _build_intermediate_yard(request: StarterMallRequest, x: int, y: int) -> list[FactoryObject]:
    objects: list[FactoryObject] = []
    cols = 4
    for index, item in enumerate(_INTERMEDIATE_ITEMS):
        cell_x = x + (index % cols) * 20
        cell_y = y + (index // cols) * 8
        objects.extend(_build_recipe_cell(request, cell_x, cell_y, item, output_role="intermediate_buffer"))
    return objects


def _build_output_block(request: StarterMallRequest, x: int, y: int, items: list[str]) -> list[FactoryObject]:
    objects: list[FactoryObject] = []
    for index, item in enumerate(items):
        cell_y = y + index * 4
        objects.extend(_build_recipe_cell(request, x, cell_y, item, output_role="output_buffer"))
    return objects


def _build_recipe_cell(
    request: StarterMallRequest,
    x: int,
    y: int,
    recipe_name: str,
    output_role: str,
) -> list[FactoryObject]:
    recipe = get_recipe(recipe_name)
    objects: list[FactoryObject] = []
    cell_id = f"{recipe_name}_{x}_{y}"
    assembler_id = f"{cell_id}_assembler"
    chest_prefix = "output" if output_role == "output_buffer" else "intermediate"

    objects.append(assembler(assembler_id, x + 6, y, recipe_name, request.machine_name))
    objects.append(inserter(f"{cell_id}_{chest_prefix}_out", x + 9, y + 1, "east", recipe_name, "product_transfer"))
    objects.append(chest(f"{cell_id}_{chest_prefix}_chest", x + 10, y + 1, recipe_name, output_role, request.chest_name))

    input_rows = [y, y + 1, y + 2]
    for slot, (ingredient, _amount) in enumerate(recipe.inputs.items()):
        if slot >= 3:
            break
        row = input_rows[slot]
        source_role = "bootstrap_input" if ingredient in _BOOTSTRAP_ITEMS else "ingredient_buffer"
        chest_id = f"{cell_id}_{ingredient}_input_{slot}"
        objects.append(chest(chest_id, x + 4, row, ingredient, source_role, request.chest_name))
        objects.append(inserter(f"{cell_id}_{ingredient}_feed_{slot}", x + 5, row, "east", ingredient, "ingredient_transfer"))

    if request.include_power_poles:
        objects.append(electric_pole(f"{cell_id}_power_pole", x + 9, y + 3))
    return objects


def _aggregate_external_inputs(items: list[str]) -> dict[str, float]:
    totals = {item: 0.0 for item in _PLATE_ITEMS}
    for item in items:
        _accumulate_leaf_inputs(item, 1.0, totals, allowed_leafs=_PLATE_ITEMS)
    return {item: round(amount, 6) for item, amount in totals.items() if amount > 0}


def _aggregate_bootstrap_inputs(items: list[str]) -> dict[str, float]:
    totals = {item: 0.0 for item in _BOOTSTRAP_ITEMS}
    recursive_items = set(_STARTER_MALL_ITEMS) | set(_INTERMEDIATE_ITEMS)
    for item in items:
        _accumulate_leaf_inputs(item, 1.0, totals, allowed_leafs=_BOOTSTRAP_ITEMS, recursive_items=recursive_items)
    return {item: round(amount, 6) for item, amount in totals.items() if amount > 0}


def _build_intermediate_load() -> dict[str, float]:
    loads: dict[str, float] = {item: 0.0 for item in ("iron_gear_wheel", "electronic_circuit", "iron_stick", "copper_cable")}
    for item in _STARTER_MALL_ITEMS:
        recipe = get_recipe(item)
        for ingredient, amount in recipe.inputs.items():
            if ingredient in loads:
                loads[ingredient] += amount
    return {item: round(amount, 6) for item, amount in loads.items()}


def _accumulate_leaf_inputs(
    item: str,
    amount: float,
    totals: dict[str, float],
    *,
    allowed_leafs: set[str],
    recursive_items: set[str] | None = None,
) -> None:
    recursive_items = recursive_items or (set(_STARTER_MALL_ITEMS) | set(_INTERMEDIATE_ITEMS))
    if item in allowed_leafs:
        totals[item] += amount
        return
    if item in _BOOTSTRAP_ITEMS:
        if item in totals:
            totals[item] += amount
        return
    if item not in recursive_items:
        return

    recipe = get_recipe(item)
    for ingredient, ingredient_amount in recipe.inputs.items():
        _accumulate_leaf_inputs(
            ingredient,
            amount * ingredient_amount,
            totals,
            allowed_leafs=allowed_leafs,
            recursive_items=recursive_items,
        )
