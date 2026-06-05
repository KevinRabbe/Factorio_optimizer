from __future__ import annotations

from factorio_optimizer.compiler.module_blueprint_compiler import (
    ModuleBlueprintRequest,
    compile_module_blueprint,
)
from factorio_optimizer.compiler.smelting_block_compiler import (
    SmeltingBlockRequest,
    compile_smelting_block,
)
from factorio_optimizer.core.blueprint_plan import BlueprintPlan
from factorio_optimizer.core.flows import Flow
from factorio_optimizer.core.objects import FactoryObject, Position
from factorio_optimizer.validation.blueprint_validator import (
    RecipeValidationSpec,
    validate_blueprint_plan,
)


def test_generated_plans_pass_unified_validation() -> None:
    module = compile_module_blueprint(ModuleBlueprintRequest(recipe_name="iron_gear_wheel"))
    smelting = compile_smelting_block(
        SmeltingBlockRequest(recipe_name="iron_plate", target_rate_per_second=1.0)
    )

    assert module.structure_valid is True
    assert module.recipe_valid is True
    assert module.connection_valid is True
    assert smelting.structure_valid is True


def test_duplicate_ids_and_overlap_are_reported() -> None:
    plan = BlueprintPlan(
        plan_id="bad_overlap",
        width=5,
        height=5,
        objects=[
            FactoryObject("belt_a", "belt", Position(1, 1), "east", item="iron_plate"),
            FactoryObject("belt_a", "belt", Position(1, 1), "east", item="iron_plate"),
        ],
    )

    result = validate_blueprint_plan(plan)

    assert result.passed is False
    assert any("Duplicate object id" in error for error in result.errors)
    assert any("Overlap" in error for error in result.errors)


def test_out_of_bounds_object_is_reported() -> None:
    plan = BlueprintPlan(
        plan_id="bad_bounds",
        width=2,
        height=2,
        objects=[
            FactoryObject("assembler", "assembler", Position(1, 1), "north", width=3, height=3),
        ],
    )

    result = validate_blueprint_plan(plan)

    assert result.passed is False
    assert any("outside grid" in error for error in result.errors)


def test_missing_recipe_interfaces_are_reported() -> None:
    plan = BlueprintPlan(
        plan_id="missing_recipe_bits",
        width=5,
        height=5,
        objects=[
            FactoryObject(
                "gear_maker",
                "assembler",
                Position(1, 1),
                "north",
                width=3,
                height=3,
                recipe="iron_gear_wheel",
            ),
        ],
    )

    result = validate_blueprint_plan(
        plan,
        RecipeValidationSpec(
            recipe="iron_gear_wheel",
            input_items=("iron_plate",),
            output_item="iron_gear_wheel",
        ),
        check_placement=False,
    )

    assert result.passed is False
    assert any("Missing input interface for iron_plate" in error for error in result.errors)
    assert any("Missing output interface for iron_gear_wheel" in error for error in result.errors)


def test_broken_belt_continuity_is_reported() -> None:
    plan = BlueprintPlan(
        plan_id="broken_belt",
        width=5,
        height=5,
        objects=[
            FactoryObject("belt", "belt", Position(1, 1), "east", item="iron_plate"),
        ],
    )

    result = validate_blueprint_plan(plan)

    assert result.passed is False
    assert any("no forward continuation" in error for error in result.errors)


def test_invalid_inserter_adjacency_is_reported() -> None:
    plan = BlueprintPlan(
        plan_id="bad_inserter",
        width=5,
        height=5,
        objects=[
            FactoryObject("inserter", "inserter", Position(2, 2), "east", item="iron_plate"),
        ],
    )

    result = validate_blueprint_plan(plan)

    assert result.passed is False
    assert any("no pickup target" in error for error in result.errors)
    assert any("no dropoff target" in error for error in result.errors)


def test_flow_validation_reports_unknown_objects() -> None:
    plan = BlueprintPlan(
        plan_id="bad_flow",
        width=5,
        height=5,
        flows=[
            Flow(
                flow_id="missing",
                item="iron_plate",
                source_id="source",
                target_id="target",
                method="test",
                path=[Position(0, 0)],
            )
        ],
    )

    result = validate_blueprint_plan(plan, check_placement=False)

    assert result.passed is False
    assert any("unknown source" in error for error in result.errors)
    assert any("unknown target" in error for error in result.errors)
