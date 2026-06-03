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
    "iron_gear_wheel": Recipe(
        name="iron_gear_wheel",
        inputs={"iron_plate": 2},
        outputs={"iron_gear_wheel": 1},
        crafting_time_seconds=0.5,
    ),
    "transport_belt": Recipe(
        name="transport_belt",
        inputs={"iron_plate": 1, "iron_gear_wheel": 1},
        outputs={"transport_belt": 2},
        crafting_time_seconds=0.5,
    ),
    "iron_plate": Recipe(
        name="iron_plate",
        inputs={"iron_ore": 1},
        outputs={"iron_plate": 1},
        crafting_time_seconds=3.2,
        category="smelting",
    ),
}


def get_recipe(recipe_name: str) -> Recipe:
    try:
        return RECIPES[recipe_name]
    except KeyError as exc:
        raise ValueError(f"Unknown recipe: {recipe_name}") from exc
