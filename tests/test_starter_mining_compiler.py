from __future__ import annotations

import pytest

from factorio_optimizer.compiler.blueprint_blocks import decode_blueprint_string
from factorio_optimizer.compiler.starter_mining_compiler import (
    StarterMiningRequest,
    compile_starter_mining_block,
)


@pytest.mark.parametrize(
    ("size_mode", "expected_count", "expected_per_row"),
    [
        ("bootstrap_12", 12, 6),
        ("half_yellow_15", 15, 8),
        ("full_yellow_30", 30, 15),
    ],
)
def test_starter_mining_size_modes_produce_expected_counts(
    size_mode: str,
    expected_count: int,
    expected_per_row: int,
) -> None:
    report = compile_starter_mining_block(
        StarterMiningRequest(item="iron_ore", size_mode=size_mode)
    )

    assert report.valid is True
    assert report.summary["block_mode"] == size_mode
    assert report.summary["miner_count"] == expected_count
    assert report.summary["miners_per_row"] == expected_per_row
    assert report.summary["row_count"] == 2


def test_starter_mining_default_chunk_reports_honest_diagnostics() -> None:
    report = compile_starter_mining_block(
        StarterMiningRequest(item="copper_ore")
    )

    assert report.valid is True
    assert report.summary["capacity_per_minute"] == 900.0
    assert report.diagnostics["ore_output_rate"] == 900.0
    assert report.diagnostics["estimated_output_per_second"] == 15.0
    assert report.diagnostics["target_belt_items_per_second"] == 15.0
    assert report.diagnostics["target_belt_tier"] == "yellow"
    assert report.diagnostics["belt_output_side"] == "right"
    assert report.diagnostics["power_requirement_kw"] == 2700.0
    assert report.diagnostics["intended_feed"] == "one full yellow smelter line"
    assert report.diagnostics["layout_shape"] == "two_row_center_output_lane"


def test_starter_mining_blueprint_contains_miners_belts_and_poles() -> None:
    report = compile_starter_mining_block(
        StarterMiningRequest(item="coal", size_mode="half_yellow_15")
    )
    decoded = decode_blueprint_string(report.blueprint_string)
    entities = decoded["blueprint"]["entities"]

    assert sum(1 for entity in entities if entity["name"] == "electric-mining-drill") == 15
    assert any(entity["name"] == "small-electric-pole" for entity in entities)
    assert any(entity["name"] == "transport-belt" for entity in entities)


def test_half_yellow_mining_chunk_reports_half_belt_throughput() -> None:
    report = compile_starter_mining_block(
        StarterMiningRequest(item="coal", size_mode="half_yellow_15")
    )

    assert report.valid is True
    assert report.summary["capacity_per_second"] == 7.5
    assert report.summary["capacity_per_minute"] == 450.0
    assert report.diagnostics["target_belt_items_per_second"] == 7.5
    assert report.diagnostics["intended_feed"] == "half of a full yellow smelter line"


def test_starter_mining_without_power_poles_fails_for_electric_drills() -> None:
    report = compile_starter_mining_block(
        StarterMiningRequest(item="iron_ore", include_power_poles=False)
    )

    assert report.valid is False
    assert any("requires power" in error for error in report.validation_errors)
