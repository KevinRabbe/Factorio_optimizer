from __future__ import annotations

from factorio_optimizer.compiler.blueprint_blocks import (
    assembler,
    belt_line,
    compile_blueprint_artifacts,
    decode_blueprint_string,
    electric_pole,
    inserter,
)
from factorio_optimizer.core.blueprint_plan import BlueprintPlan


def test_shared_block_primitives_export_centered_entities() -> None:
    plan = BlueprintPlan(
        plan_id="primitive_test",
        width=8,
        height=8,
        objects=[
            *belt_line("iron_lane", 0, 3, 1, "iron_plate"),
            assembler("assembler", 2, 2, "iron_gear_wheel", "assembling_machine_1"),
            inserter("input_inserter", 1, 3, "east", "iron_plate", "ingredient_transfer"),
            electric_pole("power", 5, 3),
        ],
    )

    artifacts = compile_blueprint_artifacts(plan)
    decoded = decode_blueprint_string(artifacts.blueprint_string)
    entities = decoded["blueprint"]["entities"]

    assert any(entity["name"] == "assembling-machine-1" and entity["position"] == {"x": 3.0, "y": 3.0} for entity in entities)
    assert any(entity["name"] == "small-electric-pole" for entity in entities)
    assert artifacts.validation.to_dict()["structure"]["passed"] is True
    assert artifacts.valid is True


def test_validation_confidence_separates_power_failures() -> None:
    plan = BlueprintPlan(
        plan_id="unpowered",
        width=5,
        height=5,
        objects=[
            assembler("assembler", 1, 1, "iron_gear_wheel", "assembling_machine_1"),
        ],
    )

    artifacts = compile_blueprint_artifacts(plan)
    confidence = artifacts.validation.to_dict()

    assert confidence["structure"]["passed"] is True
    assert confidence["placement"]["passed"] is True
    assert confidence["game_practical"]["passed"] is False
    assert any("requires power" in error for error in confidence["game_practical"]["errors"])
