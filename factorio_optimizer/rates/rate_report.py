from __future__ import annotations

from factorio_optimizer.data.machines import get_machine
from factorio_optimizer.data.recipes import get_recipe
from factorio_optimizer.rates.machine_rate import calculate_machine_recipe_rate


def build_machine_rate_report(recipe_name: str, machine_name: str, machine_count: int = 1) -> str:
    recipe = get_recipe(recipe_name)
    machine = get_machine(machine_name)
    rate = calculate_machine_recipe_rate(
        recipe=recipe,
        machine=machine,
        machine_count=machine_count,
    )

    lines = [
        f"Recipe: {rate.recipe_name}",
        f"Machine: {rate.machine_name}",
        f"Machine count: {rate.machine_count}",
        f"Crafts/s: {rate.crafts_per_second:.3f}",
        "Inputs:",
    ]

    for item_rate in rate.inputs.values():
        lines.append(
            f"- {item_rate.item}: "
            f"{item_rate.per_second:.3f}/s, "
            f"{item_rate.per_minute:.1f}/min, "
            f"{item_rate.per_hour:.1f}/hour"
        )

    lines.append("Outputs:")
    for item_rate in rate.outputs.values():
        lines.append(
            f"- {item_rate.item}: "
            f"{item_rate.per_second:.3f}/s, "
            f"{item_rate.per_minute:.1f}/min, "
            f"{item_rate.per_hour:.1f}/hour"
        )

    return "\n".join(lines)
