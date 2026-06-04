from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from math import ceil
from typing import Any

from factorio_optimizer.compiler.transport_diagnostics import (
    BELT_CAPACITY_ITEMS_PER_SECOND,
    ERA_BELT,
    ERA_INSERTER,
    INSERTER_CAPACITY_ITEMS_PER_SECOND,
)


@dataclass(frozen=True)
class BuildListItem:
    entity: str
    display_name: str
    count: int
    category: str
    note: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "entity": self.entity,
            "display_name": self.display_name,
            "count": self.count,
            "category": self.category,
            "note": self.note,
        }


DISPLAY_NAMES = {
    "assembling_machine_1": "Assembling Machine 1",
    "assembling_machine_2": "Assembling Machine 2",
    "assembling_machine_3": "Assembling Machine 3",
    "stone_furnace": "Stone Furnace",
    "steel_furnace": "Steel Furnace",
    "electric_furnace": "Electric Furnace",
    "transport_belt": "Yellow Belt",
    "fast_transport_belt": "Red Belt",
    "express_transport_belt": "Blue Belt",
    "burner_inserter": "Burner Inserter",
    "inserter": "Inserter",
    "fast_inserter": "Fast Inserter",
    "stack_inserter": "Stack Inserter",
    "steam_engine": "Steam Engine",
    "boiler": "Boiler",
    "burner_mining_drill": "Burner Mining Drill",
}


def build_factory_build_list(
    best_plan: dict,
    era: str,
    belt_name: str | None = None,
    inserter_name: str | None = None,
) -> dict[str, Any]:
    chain = best_plan.get("chain") if best_plan else None
    if not chain:
        return {"items": [], "raw_inputs": {}}

    selected_belt = _resolve_belt(era, belt_name)
    selected_inserter = _resolve_inserter(era, inserter_name)
    counts: dict[tuple[str, str, str], int] = defaultdict(int)

    _collect_machine_counts(chain, counts)
    _collect_transport_counts(chain, counts, selected_belt, selected_inserter)
    _collect_power_counts(best_plan, counts)

    items = [
        BuildListItem(
            entity=entity,
            display_name=DISPLAY_NAMES.get(entity, entity.replace("_", " ").title()),
            count=count,
            category=category,
            note=note,
        ).to_dict()
        for (category, entity, note), count in sorted(counts.items(), key=lambda entry: (entry[0][0], entry[0][1]))
        if count > 0
    ]

    return {
        "items": items,
        "selected_belt": selected_belt,
        "selected_inserter": selected_inserter,
        "raw_inputs": best_plan.get("raw_inputs", {}),
    }


def _collect_machine_counts(node: dict, counts: dict[tuple[str, str, str], int]) -> None:
    if node.get("is_raw"):
        return

    machine_name = str(node.get("machine_name", ""))
    built = int(node.get("machine_count_ceil", 0) or 0)
    item_name = str(node.get("display_name", node.get("item", "item")))

    if machine_name and built > 0:
        counts[("machines", machine_name, f"Produces {item_name}")] += built

    for child in node.get("children", []) or []:
        _collect_machine_counts(child, counts)


def _collect_transport_counts(
    node: dict,
    counts: dict[tuple[str, str, str], int],
    belt_name: str,
    inserter_name: str,
) -> None:
    if node.get("is_raw"):
        return

    belt_capacity = BELT_CAPACITY_ITEMS_PER_SECOND[belt_name]
    inserter_capacity = INSERTER_CAPACITY_ITEMS_PER_SECOND[inserter_name]

    # One transport segment per child edge: estimate lanes and inserters needed by throughput.
    for child in node.get("children", []) or []:
        required = float(child.get("target_per_second", 0.0) or 0.0)
        child_name = str(child.get("display_name", child.get("item", "item")))
        target_name = str(node.get("display_name", node.get("item", "recipe")))
        if required > 0:
            belts = max(1, ceil(required / belt_capacity))
            inserters = max(1, ceil(required / inserter_capacity))
            counts[("transport", belt_name, f"Move {child_name} into {target_name}")] += belts
            counts[("inserters", inserter_name, f"Insert {child_name} into {target_name}")] += inserters
        _collect_transport_counts(child, counts, belt_name, inserter_name)

    # Output extraction from this machine/module.
    output_required = float(node.get("target_per_second", 0.0) or 0.0)
    node_name = str(node.get("display_name", node.get("item", "item")))
    if output_required > 0:
        output_inserters = max(1, ceil(output_required / inserter_capacity))
        counts[("inserters", inserter_name, f"Extract {node_name} output")] += output_inserters


def _collect_power_counts(best_plan: dict, counts: dict[tuple[str, str, str], int]) -> None:
    energy_plan = best_plan.get("energy_plan", {}) if best_plan else {}
    steam = energy_plan.get("steam", {}) or {}
    engines = int(steam.get("steam_engines", 0) or 0)
    boilers = int(steam.get("boilers", 0) or 0)
    if engines > 0:
        counts[("power", "steam_engine", "Steam power for factory demand")] += engines
    if boilers > 0:
        counts[("power", "boiler", "Steam power for factory demand")] += boilers


def _resolve_belt(era: str, belt_name: str | None) -> str:
    if belt_name in BELT_CAPACITY_ITEMS_PER_SECOND:
        return belt_name
    return ERA_BELT.get(era, "transport_belt")


def _resolve_inserter(era: str, inserter_name: str | None) -> str:
    if inserter_name in INSERTER_CAPACITY_ITEMS_PER_SECOND:
        return inserter_name
    return ERA_INSERTER.get(era, "inserter")
