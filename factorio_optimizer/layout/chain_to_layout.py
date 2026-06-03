from __future__ import annotations

from collections import defaultdict

from factorio_optimizer.data.fuels import get_fuel
from factorio_optimizer.data.machines import get_machine
from factorio_optimizer.layout.chain_layout_request import (
    ChainLayoutRequest,
    LayoutBurnerInput,
    LayoutExternalInput,
    LayoutExternalOutput,
    LayoutModuleRequest,
)
from factorio_optimizer.rates.chain_solver import ChainNode, ProductionChain


DEFAULT_BURNER_ITEM = "coal"


def chain_to_layout_request(chain: ProductionChain) -> ChainLayoutRequest:
    modules: dict[tuple[str, str, str], LayoutModuleRequest] = {}
    external_inputs: defaultdict[str, float] = defaultdict(float)
    burner_inputs: defaultdict[tuple[str, str], tuple[int, float]] = defaultdict(lambda: (0, 0.0))

    def add_burner_input(node: ChainNode) -> None:
        if not node.machine_name:
            return

        machine = get_machine(node.machine_name)
        if machine.energy_source != "burner":
            return

        fuel = get_fuel(DEFAULT_BURNER_ITEM)
        required_per_second = node.effective_power_kw / 1000.0 / fuel.energy_mj
        key = (DEFAULT_BURNER_ITEM, machine.name)
        count, rate = burner_inputs[key]
        burner_inputs[key] = (count + node.machine_count_ceil, rate + required_per_second)
        external_inputs[DEFAULT_BURNER_ITEM] += required_per_second

    def upsert_module(node: ChainNode) -> None:
        key = (node.item, node.recipe_name, node.machine_name)
        if key in modules:
            existing = modules[key]
            modules[key] = LayoutModuleRequest(
                item=existing.item,
                recipe_name=existing.recipe_name,
                machine_name=existing.machine_name,
                machine_count=existing.machine_count + node.machine_count_ceil,
                target_per_second=existing.target_per_second + node.target_per_second,
                capacity_per_second=existing.capacity_per_second + node.capacity_per_second,
            )
        else:
            modules[key] = LayoutModuleRequest(
                item=node.item,
                recipe_name=node.recipe_name,
                machine_name=node.machine_name,
                machine_count=node.machine_count_ceil,
                target_per_second=node.target_per_second,
                capacity_per_second=node.capacity_per_second,
            )

    def visit(node: ChainNode) -> None:
        if node.is_raw:
            external_inputs[node.item] += node.target_per_second
            return

        if node.is_blackbox:
            upsert_module(node)
            for raw_item, raw_rate in node.blackbox_raw_inputs.items():
                external_inputs[raw_item] += raw_rate
            return

        upsert_module(node)
        add_burner_input(node)

        for child in node.children:
            visit(child)

    visit(chain.root)

    return ChainLayoutRequest(
        target_item=chain.target_item,
        target_per_second=chain.target_per_second,
        modules=tuple(modules.values()),
        external_inputs=tuple(
            LayoutExternalInput(item=item, required_per_second=rate)
            for item, rate in sorted(external_inputs.items())
        ),
        burner_inputs=tuple(
            LayoutBurnerInput(
                item=fuel_item,
                consumer_machine_name=machine_name,
                consumer_count=count,
                required_per_second=rate,
            )
            for (fuel_item, machine_name), (count, rate) in sorted(burner_inputs.items())
        ),
        external_outputs=(
            LayoutExternalOutput(
                item=chain.target_item,
                target_per_second=chain.target_per_second,
            ),
        ),
    )
