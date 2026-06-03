from __future__ import annotations

from dataclasses import dataclass

from factorio_optimizer.modules.module_base import FactoryModule
from factorio_optimizer.rates.machine_rate import MachineRecipeRate, calculate_machine_recipe_rate
from factorio_optimizer.data.machines import get_machine
from factorio_optimizer.data.recipes import get_recipe


@dataclass(frozen=True)
class ModuleRateSpec:
    module_type: str
    primary_recipe: str
    primary_machine: str
    machine_count: int = 1


MODULE_RATE_SPECS: dict[str, ModuleRateSpec] = {
    "iron_gear_module": ModuleRateSpec(
        module_type="iron_gear_module",
        primary_recipe="iron_gear_wheel",
        primary_machine="assembling_machine_1",
    ),
    "transport_belt_module_v0": ModuleRateSpec(
        module_type="transport_belt_module_v0",
        primary_recipe="transport_belt",
        primary_machine="assembling_machine_1",
    ),
    "transport_belt_module_v1": ModuleRateSpec(
        module_type="transport_belt_module_v1",
        primary_recipe="transport_belt",
        primary_machine="assembling_machine_1",
    ),
}


def calculate_module_theoretical_rate(module: FactoryModule) -> MachineRecipeRate:
    spec = MODULE_RATE_SPECS.get(module.module_type)
    if spec is None:
        raise ValueError(f"No module rate spec registered for module type {module.module_type}.")

    return calculate_machine_recipe_rate(
        recipe=get_recipe(spec.primary_recipe),
        machine=get_machine(spec.primary_machine),
        machine_count=spec.machine_count,
    )


def build_module_rate_report(module: FactoryModule) -> str:
    rate = calculate_module_theoretical_rate(module)

    lines = [
        f"Module: {module.module_id}",
        f"Module type: {module.module_type}",
        f"Primary recipe: {rate.recipe_name}",
        f"Primary machine: {rate.machine_name}",
        f"Machine count: {rate.machine_count}",
        f"Theoretical crafts/s: {rate.crafts_per_second:.3f}",
        "Required inputs at 100%:",
    ]

    for item_rate in rate.inputs.values():
        lines.append(
            f"- {item_rate.item}: "
            f"{item_rate.per_second:.3f}/s, "
            f"{item_rate.per_minute:.1f}/min, "
            f"{item_rate.per_hour:.1f}/hour"
        )

    lines.append("Theoretical outputs at 100%:")
    for item_rate in rate.outputs.values():
        lines.append(
            f"- {item_rate.item}: "
            f"{item_rate.per_second:.3f}/s, "
            f"{item_rate.per_minute:.1f}/min, "
            f"{item_rate.per_hour:.1f}/hour"
        )

    return "\n".join(lines)
