from __future__ import annotations

from collections import defaultdict

from factorio_optimizer.layout.chain_layout_request import (
    ChainLayoutRequest,
    LayoutExternalInput,
    LayoutExternalOutput,
    LayoutModuleRequest,
)
from factorio_optimizer.rates.chain_solver import ChainNode, ProductionChain


def chain_to_layout_request(chain: ProductionChain) -> ChainLayoutRequest:
    modules: dict[tuple[str, str, str], LayoutModuleRequest] = {}
    external_inputs: defaultdict[str, float] = defaultdict(float)

    def visit(node: ChainNode) -> None:
        if node.is_raw:
            external_inputs[node.item] += node.target_per_second
            return

        if node.is_blackbox:
            modules[(node.item, node.recipe_name, node.machine_name)] = LayoutModuleRequest(
                item=node.item,
                recipe_name=node.recipe_name,
                machine_name=node.machine_name,
                machine_count=node.machine_count_ceil,
                target_per_second=node.target_per_second,
                capacity_per_second=node.capacity_per_second,
            )
            for raw_item, raw_rate in node.blackbox_raw_inputs.items():
                external_inputs[raw_item] += raw_rate
            return

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
        external_outputs=(
            LayoutExternalOutput(
                item=chain.target_item,
                target_per_second=chain.target_per_second,
            ),
        ),
    )
