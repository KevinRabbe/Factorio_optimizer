from __future__ import annotations

import pytest

from factorio_optimizer.compiler.scaling_planner import (
    ScaledEarlyScienceRequest,
    ScaledGreenCircuitRequest,
    plan_scaled_early_science,
    plan_scaled_green_circuits,
)


def test_scaled_early_science_plan_repeats_block_counts() -> None:
    report = plan_scaled_early_science(
        ScaledEarlyScienceRequest(
            target_rate_per_second=5.0,
            block_rate_per_second=0.5,
        )
    )

    assert report.valid is True
    assert report.summary["block_count"] == 10
    assert report.summary["capacity_per_minute"] == 300.0
    assert report.summary["block_rate_per_minute"] == 30.0
    assert report.diagnostics["planner_mode"] == "scaled_repeatable_early_science"
    assert report.diagnostics["repeatable_blocks"] == 10
    assert report.diagnostics["train_readiness"]["recommended"] is False
    assert report.diagnostics["input_lanes"]["iron_plate"]["minimum_belts"] >= 1
    assert report.diagnostics["external_input_lanes"]["iron_plate"][0]["pattern"]
    assert len(report.diagnostics["sections"]) == 10


def test_scaled_early_science_plan_rejects_invalid_block_rate() -> None:
    with pytest.raises(ValueError, match="block_rate_per_second"):
        plan_scaled_early_science(
            ScaledEarlyScienceRequest(
                target_rate_per_second=1.0,
                block_rate_per_second=2.0,
            )
        )


def test_scaled_green_circuit_plan_repeats_block_counts() -> None:
    report = plan_scaled_green_circuits(
        ScaledGreenCircuitRequest(
            target_rate_per_second=5.0,
            block_rate_per_second=1.0,
        )
    )

    assert report.valid is True
    assert report.summary["block_count"] == 4
    assert report.summary["capacity_per_minute"] == 360.0
    assert report.summary["block_rate_per_minute"] == 90.0
    assert report.diagnostics["planner_mode"] == "scaled_repeatable_green_circuits"
    assert report.diagnostics["repeatable_blocks"] == 4
    assert report.diagnostics["train_readiness"]["recommended"] is False
    assert report.diagnostics["input_lanes"]["copper_plate"]["minimum_belts"] >= 1
    assert report.diagnostics["external_input_lanes"]["copper_plate"][0]["pattern"]
    assert len(report.diagnostics["sections"]) == 4
    assert "Capacity is rounded up" in report.diagnostics["warnings"][0]


def test_scaled_green_circuit_plan_rejects_invalid_block_rate() -> None:
    with pytest.raises(ValueError, match="block_rate_per_second"):
        plan_scaled_green_circuits(
            ScaledGreenCircuitRequest(
                target_rate_per_second=1.0,
                block_rate_per_second=2.0,
            )
        )
