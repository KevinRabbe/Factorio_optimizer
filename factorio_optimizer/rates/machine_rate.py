from __future__ import annotations

from dataclasses import dataclass

from factorio_optimizer.data.machines import Machine
from factorio_optimizer.data.recipes import Recipe


@dataclass(frozen=True)
class ItemRate:
    item: str
    per_second: float

    @property
    def per_minute(self) -> float:
        return self.per_second * 60.0

    @property
    def per_hour(self) -> float:
        return self.per_second * 3600.0


@dataclass(frozen=True)
class MachineRecipeRate:
    recipe_name: str
    machine_name: str
    machine_count: int
    crafts_per_second: float
    inputs: dict[str, ItemRate]
    outputs: dict[str, ItemRate]


def calculate_machine_recipe_rate(
    recipe: Recipe,
    machine: Machine,
    machine_count: int = 1,
) -> MachineRecipeRate:
    if machine_count < 1:
        raise ValueError("machine_count must be at least 1.")

    if recipe.category not in machine.allowed_categories:
        raise ValueError(
            f"Machine {machine.name} cannot craft recipe {recipe.name} "
            f"with category {recipe.category}."
        )

    crafts_per_second = (machine.crafting_speed / recipe.crafting_time_seconds) * machine_count

    input_rates = {
        item: ItemRate(item=item, per_second=amount * crafts_per_second)
        for item, amount in recipe.inputs.items()
    }
    output_rates = {
        item: ItemRate(item=item, per_second=amount * crafts_per_second)
        for item, amount in recipe.outputs.items()
    }

    return MachineRecipeRate(
        recipe_name=recipe.name,
        machine_name=machine.name,
        machine_count=machine_count,
        crafts_per_second=crafts_per_second,
        inputs=input_rates,
        outputs=output_rates,
    )
