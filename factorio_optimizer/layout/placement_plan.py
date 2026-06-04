from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class BlockPlacement:
    item: str
    recipe_name: str
    machine_name: str
    machine_count: int
    x: int
    y: int
    width: int
    height: int


@dataclass(frozen=True)
class LayoutPlacementPlan:
    target_item: str
    target_per_second: float
    placements: tuple[BlockPlacement, ...] = field(default_factory=tuple)

    @property
    def width(self) -> int:
        if not self.placements:
            return 0
        return max(block.x + block.width for block in self.placements)

    @property
    def height(self) -> int:
        if not self.placements:
            return 0
        return max(block.y + block.height for block in self.placements)


def format_layout_placement_plan(plan: LayoutPlacementPlan) -> str:
    lines = [
        f"Placement plan for {plan.target_item}: {plan.target_per_second:.3f}/s",
        f"Footprint estimate: {plan.width}x{plan.height}",
        "Blocks:",
    ]

    if not plan.placements:
        lines.append("- none")
        return "\n".join(lines)

    for block in plan.placements:
        lines.append(
            f"- {block.item}: {block.machine_count}x {block.machine_name} "
            f"at ({block.x}, {block.y}) size={block.width}x{block.height}"
        )

    return "\n".join(lines)
