from __future__ import annotations

from factorio_optimizer.config.generation_config import GenerationConfig
from factorio_optimizer.core.objects import Position
from factorio_optimizer.data.machines import Machine, get_best_machine_for_category, get_machine, get_machines_for_era
from factorio_optimizer.data.recipes import get_recipe
from factorio_optimizer.modules.generic_assembler_module import build_generic_assembler_module
from factorio_optimizer.modules.module_base import FactoryModule


class UnsupportedRecipeModuleError(ValueError):
    pass


def create_module_for_recipe(
    recipe_name: str,
    module_id: str | None = None,
    origin: Position | None = None,
    config: GenerationConfig | None = None,
    machine_name: str | None = None,
) -> FactoryModule:
    config = config or GenerationConfig()
    recipe = get_recipe(recipe_name)
    selected_machine = _select_machine_for_recipe(
        category=recipe.category,
        config=config,
        machine_name=machine_name,
    )

    if recipe.category in {"crafting", "crafting-with-fluid"}:
        return build_generic_assembler_module(
            recipe_name=recipe_name,
            module_id=module_id,
            origin=origin,
            machine_name=selected_machine.name,
        )

    raise UnsupportedRecipeModuleError(
        f"Recipe {recipe_name!r} with category {recipe.category!r} is not supported by ModuleFactory yet."
    )


def _select_machine_for_recipe(
    category: str,
    config: GenerationConfig,
    machine_name: str | None,
) -> Machine:
    if machine_name is not None:
        machine = get_machine(machine_name)
        if category not in machine.allowed_categories:
            raise UnsupportedRecipeModuleError(
                f"Machine {machine_name!r} cannot craft category {category!r}."
            )
        return machine

    if config.machine_preference == "fastest_available":
        machine = get_best_machine_for_category(category, config.era)
        if machine is not None:
            return machine

    candidates = [
        machine
        for machine in get_machines_for_era(config.era)
        if category in machine.allowed_categories
    ]
    if not candidates:
        raise UnsupportedRecipeModuleError(
            f"No machine available for category {category!r} in era {config.era!r}."
        )

    if config.machine_preference == "lowest_tier":
        return min(candidates, key=lambda machine: machine.crafting_speed)

    return max(candidates, key=lambda machine: machine.crafting_speed)
