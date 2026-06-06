from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EntitySpec:
    name: str
    width: int
    height: int
    supports_recipe: bool = False
    requires_power: bool = False
    supply_area_distance: float = 0.0
    machine_type: str | None = None
    recipe_categories: tuple[str, ...] = ()


ENTITY_SPECS: dict[str, EntitySpec] = {
    "transport-belt": EntitySpec(name="transport-belt", width=1, height=1),
    "fast-transport-belt": EntitySpec(name="fast-transport-belt", width=1, height=1),
    "inserter": EntitySpec(name="inserter", width=1, height=1, requires_power=True),
    "fast-inserter": EntitySpec(name="fast-inserter", width=1, height=1, requires_power=True),
    "burner-inserter": EntitySpec(name="burner-inserter", width=1, height=1),
    "assembling-machine-1": EntitySpec(
        name="assembling-machine-1",
        width=3,
        height=3,
        supports_recipe=True,
        requires_power=True,
        machine_type="assembler",
        recipe_categories=("crafting",),
    ),
    "assembling-machine-2": EntitySpec(
        name="assembling-machine-2",
        width=3,
        height=3,
        supports_recipe=True,
        requires_power=True,
        machine_type="assembler",
        recipe_categories=("crafting", "crafting-with-fluid"),
    ),
    "stone-furnace": EntitySpec(
        name="stone-furnace",
        width=2,
        height=2,
        supports_recipe=True,
        machine_type="furnace",
        recipe_categories=("smelting",),
    ),
    "steel-furnace": EntitySpec(
        name="steel-furnace",
        width=2,
        height=2,
        supports_recipe=True,
        machine_type="furnace",
        recipe_categories=("smelting",),
    ),
    "electric-furnace": EntitySpec(
        name="electric-furnace",
        width=3,
        height=3,
        supports_recipe=True,
        requires_power=True,
        machine_type="furnace",
        recipe_categories=("smelting",),
    ),
    "burner-mining-drill": EntitySpec(
        name="burner-mining-drill",
        width=3,
        height=3,
        machine_type="miner",
    ),
    "electric-mining-drill": EntitySpec(
        name="electric-mining-drill",
        width=3,
        height=3,
        requires_power=True,
        machine_type="miner",
    ),
    "splitter": EntitySpec(name="splitter", width=2, height=1),
    "iron-chest": EntitySpec(name="iron-chest", width=1, height=1),
    "pipe": EntitySpec(name="pipe", width=1, height=1),
    "pipe-to-ground": EntitySpec(name="pipe-to-ground", width=1, height=1),
    "chemical-plant": EntitySpec(
        name="chemical-plant",
        width=3,
        height=3,
        supports_recipe=True,
        requires_power=True,
        machine_type="chemical_plant",
        recipe_categories=("chemistry",),
    ),
    "oil-refinery": EntitySpec(
        name="oil-refinery",
        width=5,
        height=5,
        supports_recipe=True,
        requires_power=True,
        machine_type="refinery",
        recipe_categories=("oil_processing",),
    ),
    "lab": EntitySpec(name="lab", width=3, height=3, requires_power=True, machine_type="lab"),
    "small-electric-pole": EntitySpec(
        name="small-electric-pole",
        width=1,
        height=1,
        supply_area_distance=2.5,
    ),
    "medium-electric-pole": EntitySpec(
        name="medium-electric-pole",
        width=1,
        height=1,
        supply_area_distance=3.5,
    ),
}


def get_entity_spec(entity_name: str) -> EntitySpec:
    try:
        return ENTITY_SPECS[entity_name]
    except KeyError as exc:
        raise ValueError(f"Unknown Factorio entity: {entity_name!r}") from exc


def entity_center(x: int, y: int, width: int, height: int) -> tuple[float, float]:
    return (x + (width - 1) / 2.0, y + (height - 1) / 2.0)
