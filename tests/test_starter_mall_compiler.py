from __future__ import annotations

from factorio_optimizer.compiler.blueprint_blocks import decode_blueprint_string
from factorio_optimizer.compiler.starter_mall_compiler import (
    StarterMallRequest,
    compile_starter_mall,
)


def test_starter_mall_report_contains_expected_outputs() -> None:
    report = compile_starter_mall(StarterMallRequest())

    assert report.valid is True
    assert report.summary["item"] == "starter_mall"
    assert report.summary["output_count"] == 13
    assert set(report.diagnostics["external_inputs"]) == {"iron_plate", "copper_plate"}
    assert set(report.diagnostics["bootstrap_inputs"]) == {"stone", "wood"}
    assert "iron_gear_wheel" in report.diagnostics["intermediate_load"]
    assert "electronic_circuit" in report.diagnostics["intermediate_load"]
    assert "iron_stick" in report.diagnostics["intermediate_load"]
    assert len(report.diagnostics["output_chests"]) == 13
    assert "smelting lines" in report.diagnostics["build_stage_note"]
    assert "steady external plates" in report.diagnostics["feed_from_smelting_note"]


def test_starter_mall_blueprint_contains_output_chests_and_assemblers() -> None:
    report = compile_starter_mall(StarterMallRequest())
    decoded = decode_blueprint_string(report.blueprint_string)
    entities = decoded["blueprint"]["entities"]

    assert any(entity["name"] == "iron-chest" for entity in entities)
    assert any(entity["name"] == "assembling-machine-1" for entity in entities)
    assert sum(1 for entity in entities if entity["name"] == "small-electric-pole") > 0


def test_starter_mall_without_power_poles_fails_validation() -> None:
    report = compile_starter_mall(StarterMallRequest(include_power_poles=False))

    assert report.valid is False
    assert any("requires power" in error for error in report.validation_errors)
