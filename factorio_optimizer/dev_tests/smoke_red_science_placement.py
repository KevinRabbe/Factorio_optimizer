from __future__ import annotations

from factorio_optimizer.layout.placement_plan import format_layout_placement_plan
from factorio_optimizer.layout.simple_placer import build_simple_placement_plan
from factorio_optimizer.layout.chain_to_layout import chain_to_layout_request
from factorio_optimizer.rates.chain_solver import build_production_chain


def main() -> None:
    print("# Red science placement smoke test")

    chain = build_production_chain("automation_science_pack", 1.0, era="early")
    request = chain_to_layout_request(chain)
    plan = build_simple_placement_plan(request)

    assert plan.placements, "expected block placements"
    assert plan.width > 0, "expected positive width"
    assert plan.height > 0, "expected positive height"

    block_items = {block.item for block in plan.placements}
    assert "iron_plate" in block_items, "expected iron plate block"
    assert "copper_plate" in block_items, "expected copper plate block"
    assert "iron_gear_wheel" in block_items, "expected gear block"
    assert "automation_science_pack" in block_items, "expected red science block"

    print(format_layout_placement_plan(plan))
    print("PASS red science placement")


if __name__ == "__main__":
    main()
