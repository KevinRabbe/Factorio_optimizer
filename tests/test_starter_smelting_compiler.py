from __future__ import annotations

import pytest

from factorio_optimizer.compiler.blueprint_blocks import decode_blueprint_string
from factorio_optimizer.compiler.starter_smelting_compiler import (
    StarterSmeltingRequest,
    compile_starter_smelting_block,
)


def test_starter_smelting_rate_based_mode_still_works() -> None:
    report = compile_starter_smelting_block(
        StarterSmeltingRequest(recipe_name="iron_plate", target_rate_per_second=0.5)
    )

    assert report.valid is True
    assert report.summary["item"] == "iron_plate"
    assert report.summary["block_mode"] == "rate_based"
    assert report.summary["furnace_count"] >= 1


@pytest.mark.parametrize(
    ("size_mode", "expected_count"),
    [
        ("starter_12", 12),
        ("compact_16", 16),
        ("brick_24", 24),
        ("standard_32", 32),
        ("full_belt_48", 48),
    ],
)
def test_starter_smelting_size_modes_produce_expected_furnace_counts(
    size_mode: str,
    expected_count: int,
) -> None:
    report = compile_starter_smelting_block(
        StarterSmeltingRequest(
            recipe_name="iron_plate",
            target_rate_per_second=0.5,
            size_mode=size_mode,
        )
    )

    assert report.valid is True
    assert report.summary["block_mode"] == size_mode
    assert report.summary["furnace_count"] == expected_count
    assert report.summary["machine_count"] == expected_count
    assert report.diagnostics["coal_support"] == "one local coal chest per furnace"


def test_starter_smelting_default_standard_32_reports_honest_diagnostics() -> None:
    report = compile_starter_smelting_block(
        StarterSmeltingRequest(
            recipe_name="copper_plate",
            target_rate_per_second=0.5,
            size_mode="standard_32",
        )
    )

    assert report.summary["furnace_count"] == 32
    assert report.diagnostics["ore_input_rate"] == 600.0
    assert report.diagnostics["output_rate"] == 600.0
    assert report.diagnostics["upgrade_note"] == (
        "Good default for large starting patches; scales toward a full yellow-belt line later."
    )
    assert report.diagnostics["external_inputs"]["copper_ore"] == 10.0


def test_starter_smelting_full_belt_48_uses_24_per_side_layout() -> None:
    report = compile_starter_smelting_block(
        StarterSmeltingRequest(
            recipe_name="iron_plate",
            target_rate_per_second=0.5,
            size_mode="full_belt_48",
        )
    )

    assert report.valid is True
    assert report.summary["block_mode"] == "full_belt_48"
    assert report.summary["furnace_count"] == 48
    assert report.summary["row_count"] == 2
    assert report.summary["furnaces_per_row"] == 24
    assert report.summary["furnaces_per_side"] == 24
    assert report.diagnostics["layout_shape"] == "mirrored_double_row_24_per_side"
    assert report.diagnostics["furnaces_per_side"] == 24
    assert "24 furnaces per side" in report.diagnostics["upgrade_note"]


def test_starter_smelting_full_belt_48_reports_full_yellow_plate_rate() -> None:
    report = compile_starter_smelting_block(
        StarterSmeltingRequest(
            recipe_name="iron_plate",
            target_rate_per_second=0.5,
            size_mode="full_belt_48",
        )
    )

    assert report.summary["capacity_per_second"] == 15.0
    assert report.summary["capacity_per_minute"] == 900.0
    assert report.diagnostics["target_output_belt_items_per_second"] == 15.0


def test_full_belt_48_can_upgrade_to_steel_furnaces_on_same_layout() -> None:
    report = compile_starter_smelting_block(
        StarterSmeltingRequest(
            recipe_name="iron_plate",
            target_rate_per_second=1.0,
            size_mode="full_belt_48",
            machine_name="steel_furnace",
        )
    )

    assert report.valid is True
    assert report.summary["capacity_per_second"] == 30.0
    assert report.summary["capacity_per_minute"] == 1800.0
    assert report.diagnostics["target_belt_tier"] == "red"
    assert report.diagnostics["target_output_belt_items_per_second"] == 30.0


def test_brick_24_reports_half_yellow_brick_rate() -> None:
    report = compile_starter_smelting_block(
        StarterSmeltingRequest(
            recipe_name="stone_brick",
            target_rate_per_second=0.5,
            size_mode="brick_24",
        )
    )

    assert report.valid is True
    assert report.summary["furnace_count"] == 24
    assert report.summary["furnaces_per_side"] == 12
    assert report.summary["capacity_per_second"] == 7.5
    assert report.summary["capacity_per_minute"] == 450.0
    assert report.diagnostics["external_inputs"]["stone"] == 15.0
    assert report.diagnostics["target_output_belt_items_per_second"] == 7.5


def test_starter_steel_12_reports_iron_plate_demand() -> None:
    report = compile_starter_smelting_block(
        StarterSmeltingRequest(
            recipe_name="steel_plate",
            target_rate_per_second=0.5,
            size_mode="starter_12",
        )
    )

    assert report.valid is True
    assert report.summary["furnace_count"] == 12
    assert report.summary["furnaces_per_side"] == 6
    assert report.summary["capacity_per_second"] == 0.75
    assert report.summary["capacity_per_minute"] == 45.0
    assert report.diagnostics["external_inputs"]["iron_plate"] == 3.75
    assert report.diagnostics["upstream_plate_demand_per_minute"] == 225.0
    assert "steel support block" in report.diagnostics["upgrade_note"]


def test_starter_smelting_full_belt_48_mirrors_inserter_directions() -> None:
    report = compile_starter_smelting_block(
        StarterSmeltingRequest(
            recipe_name="iron_plate",
            target_rate_per_second=0.5,
            size_mode="full_belt_48",
        )
    )
    decoded = decode_blueprint_string(report.blueprint_string)
    entities = decoded["blueprint"]["entities"]

    north_facing = [entity for entity in entities if entity["name"] == "burner-inserter" and entity["direction"] == 0]
    south_facing = [entity for entity in entities if entity["name"] == "burner-inserter" and entity["direction"] == 4]

    assert north_facing
    assert south_facing


def test_starter_smelting_blueprint_contains_burner_feed_parts() -> None:
    report = compile_starter_smelting_block(
        StarterSmeltingRequest(
            recipe_name="copper_plate",
            target_rate_per_second=1.0,
            size_mode="standard_32",
        )
    )
    decoded = decode_blueprint_string(report.blueprint_string)
    entities = decoded["blueprint"]["entities"]

    assert any(entity["name"] == "stone-furnace" and entity["recipe"] == "copper_plate" for entity in entities)
    assert sum(1 for entity in entities if entity["name"] == "stone-furnace") == 32
    assert any(entity["name"] == "burner-inserter" for entity in entities)
    assert any(entity["name"] == "iron-chest" for entity in entities)
    assert any(entity["name"] == "transport-belt" for entity in entities)
