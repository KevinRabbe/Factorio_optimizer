from __future__ import annotations

from factorio_optimizer.layout.chain_layout_request import ChainLayoutRequest, LayoutModuleRequest
from factorio_optimizer.layout.placement_plan import BlockPlacement, LayoutPlacementPlan


BLOCK_GAP_Y = 3
DEFAULT_BLOCK_WIDTH = 16


def build_simple_placement_plan(request: ChainLayoutRequest) -> LayoutPlacementPlan:
    ordered_modules = sorted(request.modules, key=_module_sort_key)

    placements: list[BlockPlacement] = []
    y_cursor = 0

    for module in ordered_modules:
        width = _estimate_block_width(module)
        height = _estimate_block_height(module)
        placements.append(
            BlockPlacement(
                item=module.item,
                recipe_name=module.recipe_name,
                machine_name=module.machine_name,
                machine_count=module.machine_count,
                x=0,
                y=y_cursor,
                width=width,
                height=height,
            )
        )
        y_cursor += height + BLOCK_GAP_Y

    return LayoutPlacementPlan(
        target_item=request.target_item,
        target_per_second=request.target_per_second,
        placements=tuple(placements),
    )


def _module_sort_key(module: LayoutModuleRequest) -> tuple[int, str]:
    if module.machine_name.endswith("furnace"):
        return (0, module.item)
    if module.item in ("iron_gear_wheel", "copper_cable"):
        return (1, module.item)
    return (2, module.item)


def _estimate_block_width(module: LayoutModuleRequest) -> int:
    if module.machine_name.endswith("furnace"):
        return max(DEFAULT_BLOCK_WIDTH, module.machine_count * 3 + 6)
    return max(DEFAULT_BLOCK_WIDTH, module.machine_count * 4 + 6)


def _estimate_block_height(module: LayoutModuleRequest) -> int:
    if module.machine_name.endswith("furnace"):
        return 6
    if module.machine_count <= 1:
        return 7
    return 8
