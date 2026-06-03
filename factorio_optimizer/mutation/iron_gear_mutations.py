from __future__ import annotations

from factorio_optimizer.core.blueprint_plan import BlueprintPlan
from factorio_optimizer.planner.iron_gear_builder import build_iron_gear_plan_with_layout
from factorio_optimizer.validation.static_validator import validate_plan


def generate_iron_gear_variants(base_plan: BlueprintPlan) -> list[BlueprintPlan]:
    del base_plan  # The current variant set is layout-template based.

    variants: list[BlueprintPlan] = []

    layouts = [
        {
            "name": "center",
            "assembler_x": 4,
            "assembler_y": 2,
            "input_y": 3,
            "output_y": 3,
        },
        {
            "name": "up",
            "assembler_x": 4,
            "assembler_y": 1,
            "input_y": 2,
            "output_y": 2,
        },
        {
            "name": "down",
            "assembler_x": 4,
            "assembler_y": 3,
            "input_y": 4,
            "output_y": 4,
        },
        {
            "name": "left",
            "assembler_x": 3,
            "assembler_y": 2,
            "input_y": 3,
            "output_y": 3,
        },
        {
            "name": "right",
            "assembler_x": 5,
            "assembler_y": 2,
            "input_y": 3,
            "output_y": 3,
        },
    ]

    for layout in layouts:
        variant = build_iron_gear_plan_with_layout(
            plan_id=f"iron_gear_{layout['name']}",
            assembler_x=layout["assembler_x"],
            assembler_y=layout["assembler_y"],
            input_y=layout["input_y"],
            output_y=layout["output_y"],
        )

        if validate_plan(variant).passed:
            variants.append(variant)

    return variants
