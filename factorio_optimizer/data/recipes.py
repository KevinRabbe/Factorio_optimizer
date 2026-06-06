from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Recipe:
    name: str
    inputs: dict[str, float]
    outputs: dict[str, float]
    crafting_time_seconds: float
    category: str = "crafting"


RECIPES: dict[str, Recipe] = {
    # ═══════════════════════════════════════════════════════════════════════
    # EARLY GAME — SMELTING
    # ═══════════════════════════════════════════════════════════════════════
    "iron_plate": Recipe(
        name="iron_plate",
        inputs={"iron_ore": 1},
        outputs={"iron_plate": 1},
        crafting_time_seconds=3.2,
        category="smelting",
    ),
    "copper_plate": Recipe(
        name="copper_plate",
        inputs={"copper_ore": 1},
        outputs={"copper_plate": 1},
        crafting_time_seconds=3.2,
        category="smelting",
    ),
    "stone_brick": Recipe(
        name="stone_brick",
        inputs={"stone": 2},
        outputs={"stone_brick": 1},
        crafting_time_seconds=3.2,
        category="smelting",
    ),

    # ═══════════════════════════════════════════════════════════════════════
    # MID GAME — SMELTING
    # ═══════════════════════════════════════════════════════════════════════
    "steel_plate": Recipe(
        name="steel_plate",
        inputs={"iron_plate": 5},
        outputs={"steel_plate": 1},
        crafting_time_seconds=16.0,
        category="smelting",
    ),

    # ═══════════════════════════════════════════════════════════════════════
    # EARLY GAME — CRAFTING
    # ═══════════════════════════════════════════════════════════════════════
    "iron_gear_wheel": Recipe(
        name="iron_gear_wheel",
        inputs={"iron_plate": 2},
        outputs={"iron_gear_wheel": 1},
        crafting_time_seconds=0.5,
    ),
    "copper_cable": Recipe(
        name="copper_cable",
        inputs={"copper_plate": 1},
        outputs={"copper_cable": 2},
        crafting_time_seconds=0.5,
    ),
    "electronic_circuit": Recipe(
        name="electronic_circuit",
        inputs={"iron_plate": 1, "copper_cable": 3},
        outputs={"electronic_circuit": 1},
        crafting_time_seconds=0.5,
    ),
    "transport_belt": Recipe(
        name="transport_belt",
        inputs={"iron_plate": 1, "iron_gear_wheel": 1},
        outputs={"transport_belt": 2},
        crafting_time_seconds=0.5,
    ),
    "underground_belt": Recipe(
        name="underground_belt",
        inputs={"iron_plate": 10, "transport_belt": 5},
        outputs={"underground_belt": 2},
        crafting_time_seconds=1.0,
    ),
    "splitter": Recipe(
        name="splitter",
        inputs={"iron_plate": 5, "electronic_circuit": 5, "transport_belt": 4},
        outputs={"splitter": 1},
        crafting_time_seconds=1.0,
    ),
    "inserter": Recipe(
        name="inserter",
        inputs={"iron_plate": 1, "iron_gear_wheel": 1, "electronic_circuit": 1},
        outputs={"inserter": 1},
        crafting_time_seconds=0.5,
    ),
    "pipe": Recipe(
        name="pipe",
        inputs={"iron_plate": 1},
        outputs={"pipe": 1},
        crafting_time_seconds=0.5,
    ),
    "pipe_to_ground": Recipe(
        name="pipe_to_ground",
        inputs={"pipe": 10, "iron_plate": 5},
        outputs={"pipe_to_ground": 2},
        crafting_time_seconds=0.5,
    ),
    "stone_wall": Recipe(
        name="stone_wall",
        inputs={"stone_brick": 5},
        outputs={"stone_wall": 1},
        crafting_time_seconds=0.5,
    ),
    "small_electric_pole": Recipe(
        name="small_electric_pole",
        inputs={"copper_cable": 2, "wood": 1},
        outputs={"small_electric_pole": 2},
        crafting_time_seconds=0.5,
    ),
    "medium_electric_pole": Recipe(
        name="medium_electric_pole",
        inputs={"copper_plate": 2, "steel_plate": 2, "iron_stick": 4},
        outputs={"medium_electric_pole": 1},
        crafting_time_seconds=0.5,
    ),
    "iron_stick": Recipe(
        name="iron_stick",
        inputs={"iron_plate": 1},
        outputs={"iron_stick": 2},
        crafting_time_seconds=0.5,
    ),
    "firearm_magazine": Recipe(
        name="firearm_magazine",
        inputs={"iron_plate": 4},
        outputs={"firearm_magazine": 1},
        crafting_time_seconds=1.0,
    ),
    "grenade": Recipe(
        name="grenade",
        inputs={"coal": 1, "iron_plate": 5},
        outputs={"grenade": 1},
        crafting_time_seconds=8.0,
    ),

    # ═══════════════════════════════════════════════════════════════════════
    # MID GAME — CRAFTING
    # ═══════════════════════════════════════════════════════════════════════
    "fast_inserter": Recipe(
        name="fast_inserter",
        inputs={"electronic_circuit": 2, "iron_plate": 2, "inserter": 1},
        outputs={"fast_inserter": 1},
        crafting_time_seconds=0.5,
    ),
    "fast_transport_belt": Recipe(
        name="fast_transport_belt",
        inputs={"iron_gear_wheel": 5, "transport_belt": 1},
        outputs={"fast_transport_belt": 1},
        crafting_time_seconds=0.5,
    ),
    "engine_unit": Recipe(
        name="engine_unit",
        inputs={"steel_plate": 1, "iron_gear_wheel": 1, "pipe": 2},
        outputs={"engine_unit": 1},
        crafting_time_seconds=10.0,
    ),
    "electric_engine_unit": Recipe(
        name="electric_engine_unit",
        inputs={"engine_unit": 1, "electronic_circuit": 2, "lubricant": 15},
        outputs={"electric_engine_unit": 1},
        crafting_time_seconds=10.0,
        category="crafting-with-fluid",
    ),
    "flying_robot_frame": Recipe(
        name="flying_robot_frame",
        inputs={
            "electric_engine_unit": 1,
            "battery": 2,
            "electronic_circuit": 3,
            "steel_plate": 1,
        },
        outputs={"flying_robot_frame": 1},
        crafting_time_seconds=20.0,
    ),
    "advanced_circuit": Recipe(
        name="advanced_circuit",
        inputs={"copper_cable": 4, "electronic_circuit": 2, "plastic_bar": 2},
        outputs={"advanced_circuit": 1},
        crafting_time_seconds=6.0,
    ),
    "battery": Recipe(
        name="battery",
        inputs={"copper_plate": 1, "iron_plate": 1, "sulfuric_acid": 20},
        outputs={"battery": 1},
        crafting_time_seconds=5.0,
        category="chemistry",
    ),
    "piercing_rounds_magazine": Recipe(
        name="piercing_rounds_magazine",
        inputs={"copper_plate": 5, "steel_plate": 1, "firearm_magazine": 1},
        outputs={"piercing_rounds_magazine": 1},
        crafting_time_seconds=3.0,
    ),
    "assembling_machine_1": Recipe(
        name="assembling_machine_1",
        inputs={"iron_plate": 9, "iron_gear_wheel": 5, "electronic_circuit": 3},
        outputs={"assembling_machine_1": 1},
        crafting_time_seconds=0.5,
    ),
    "assembling_machine_2": Recipe(
        name="assembling_machine_2",
        inputs={
            "steel_plate": 2,
            "iron_gear_wheel": 5,
            "electronic_circuit": 3,
            "assembling_machine_1": 1,
        },
        outputs={"assembling_machine_2": 1},
        crafting_time_seconds=0.5,
    ),
    "electric_mining_drill": Recipe(
        name="electric_mining_drill",
        inputs={"iron_plate": 10, "iron_gear_wheel": 5, "electronic_circuit": 3},
        outputs={"electric_mining_drill": 1},
        crafting_time_seconds=2.0,
    ),
    "lab": Recipe(
        name="lab",
        inputs={"iron_gear_wheel": 10, "electronic_circuit": 10, "transport_belt": 4},
        outputs={"lab": 1},
        crafting_time_seconds=2.0,
    ),
    "stone_furnace": Recipe(
        name="stone_furnace",
        inputs={"stone": 5},
        outputs={"stone_furnace": 1},
        crafting_time_seconds=0.5,
    ),
    "boiler": Recipe(
        name="boiler",
        inputs={"pipe": 4, "stone_furnace": 1},
        outputs={"boiler": 1},
        crafting_time_seconds=0.5,
    ),
    "steam_engine": Recipe(
        name="steam_engine",
        inputs={"iron_plate": 10, "iron_gear_wheel": 8, "pipe": 5},
        outputs={"steam_engine": 1},
        crafting_time_seconds=0.5,
    ),

    # ═══════════════════════════════════════════════════════════════════════
    # CHEMISTRY
    # ═══════════════════════════════════════════════════════════════════════
    "plastic_bar": Recipe(
        name="plastic_bar",
        inputs={"coal": 1, "petroleum_gas": 20},
        outputs={"plastic_bar": 2},
        crafting_time_seconds=1.0,
        category="chemistry",
    ),
    "sulfur": Recipe(
        name="sulfur",
        inputs={"petroleum_gas": 30, "water": 30},
        outputs={"sulfur": 2},
        crafting_time_seconds=1.0,
        category="chemistry",
    ),
    "sulfuric_acid": Recipe(
        name="sulfuric_acid",
        inputs={"iron_plate": 1, "sulfur": 5, "water": 100},
        outputs={"sulfuric_acid": 50},
        crafting_time_seconds=1.0,
        category="chemistry",
    ),
    "lubricant": Recipe(
        name="lubricant",
        inputs={"heavy_oil": 10},
        outputs={"lubricant": 10},
        crafting_time_seconds=1.0,
        category="chemistry",
    ),

    # ═══════════════════════════════════════════════════════════════════════
    # OIL PROCESSING
    # ═══════════════════════════════════════════════════════════════════════
    "basic_oil_processing": Recipe(
        name="basic_oil_processing",
        inputs={"crude_oil": 100},
        outputs={"petroleum_gas": 45},
        crafting_time_seconds=5.0,
        category="oil_processing",
    ),
    "advanced_oil_processing": Recipe(
        name="advanced_oil_processing",
        inputs={"crude_oil": 100, "water": 50},
        outputs={"heavy_oil": 25, "light_oil": 45, "petroleum_gas": 55},
        crafting_time_seconds=5.0,
        category="oil_processing",
    ),

    # ═══════════════════════════════════════════════════════════════════════
    # SCIENCE PACKS
    # ═══════════════════════════════════════════════════════════════════════
    "automation_science_pack": Recipe(
        name="automation_science_pack",
        inputs={"copper_plate": 1, "iron_gear_wheel": 1},
        outputs={"automation_science_pack": 1},
        crafting_time_seconds=5.0,
    ),
    "logistic_science_pack": Recipe(
        name="logistic_science_pack",
        inputs={"transport_belt": 1, "inserter": 1},
        outputs={"logistic_science_pack": 1},
        crafting_time_seconds=6.0,
    ),
    "military_science_pack": Recipe(
        name="military_science_pack",
        inputs={
            "piercing_rounds_magazine": 1,
            "grenade": 1,
            "stone_wall": 2,
        },
        outputs={"military_science_pack": 2},
        crafting_time_seconds=10.0,
    ),
    "chemical_science_pack": Recipe(
        name="chemical_science_pack",
        inputs={
            "advanced_circuit": 3,
            "engine_unit": 2,
            "sulfuric_acid": 40,
        },
        outputs={"chemical_science_pack": 2},
        crafting_time_seconds=24.0,
        category="crafting-with-fluid",
    ),
    "production_science_pack": Recipe(
        name="production_science_pack",
        inputs={
            "rail": 30,
            "electric_furnace": 1,
            "productivity_module_1": 1,
        },
        outputs={"production_science_pack": 3},
        crafting_time_seconds=21.0,
    ),
    "utility_science_pack": Recipe(
        name="utility_science_pack",
        inputs={
            "flying_robot_frame": 1,
            "advanced_circuit": 3,
            "low_density_structure": 3,
        },
        outputs={"utility_science_pack": 3},
        crafting_time_seconds=21.0,
    ),
    # ── Utility science sub-components ────────────────────────────────────
    "low_density_structure": Recipe(
        name="low_density_structure",
        inputs={"copper_plate": 20, "steel_plate": 2, "plastic_bar": 5},
        outputs={"low_density_structure": 1},
        crafting_time_seconds=20.0,
    ),
    "rail": Recipe(
        name="rail",
        inputs={"steel_plate": 1, "stone": 1, "iron_stick": 1},
        outputs={"rail": 2},
        crafting_time_seconds=0.5,
    ),
}


def get_recipe(recipe_name: str) -> Recipe:
    try:
        return RECIPES[recipe_name]
    except KeyError as exc:
        raise ValueError(f"Unknown recipe: {recipe_name!r}") from exc


def has_recipe(item_name: str) -> bool:
    return item_name in RECIPES
