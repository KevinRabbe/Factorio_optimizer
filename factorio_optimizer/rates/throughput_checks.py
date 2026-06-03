from __future__ import annotations

from factorio_optimizer.data.belts import get_belt
from factorio_optimizer.data.inserters import get_inserter
from factorio_optimizer.data.machines import get_machine
from factorio_optimizer.data.recipes import get_recipe
from factorio_optimizer.rates.bottleneck_report import BottleneckCheck, BottleneckReport, build_bottleneck_report
from factorio_optimizer.rates.machine_rate import calculate_machine_recipe_rate


def build_transport_belt_v0_throughput_report() -> BottleneckReport:
    recipe = get_recipe("transport_belt")
    machine = get_machine("assembling_machine_1")
    rate = calculate_machine_recipe_rate(recipe, machine)

    basic_belt = get_belt("transport_belt")
    basic_inserter = get_inserter("inserter")

    checks: list[BottleneckCheck] = []

    for item_rate in rate.inputs.values():
        checks.append(
            BottleneckCheck(
                name=f"{item_rate.item}_input_belt",
                item=item_rate.item,
                kind="belt",
                required_per_second=item_rate.per_second,
                capacity_per_second=basic_belt.items_per_second,
            )
        )
        checks.append(
            BottleneckCheck(
                name=f"{item_rate.item}_input_inserter",
                item=item_rate.item,
                kind="inserter",
                required_per_second=item_rate.per_second,
                capacity_per_second=basic_inserter.estimated_items_per_second,
            )
        )

    for item_rate in rate.outputs.values():
        checks.append(
            BottleneckCheck(
                name=f"{item_rate.item}_output_inserter",
                item=item_rate.item,
                kind="inserter",
                required_per_second=item_rate.per_second,
                capacity_per_second=basic_inserter.estimated_items_per_second,
            )
        )
        checks.append(
            BottleneckCheck(
                name=f"{item_rate.item}_output_belt",
                item=item_rate.item,
                kind="belt",
                required_per_second=item_rate.per_second,
                capacity_per_second=basic_belt.items_per_second,
            )
        )

    return build_bottleneck_report(checks)
