from __future__ import annotations

from factorio_optimizer.compiler.blueprint_blocks import decode_blueprint_string
from factorio_optimizer.compiler.red_science_compiler import (
    RedScienceBlockRequest,
    compile_red_science_block,
)


def test_red_science_block_for_30_per_minute_is_valid() -> None:
    report = compile_red_science_block(RedScienceBlockRequest(target_rate_per_second=0.5))

    assert report.valid is True
    assert report.validation_errors == []
    assert report.summary["target_rate_per_minute"] == 30.0
    assert report.summary["science_assembler_count"] == 5
    assert report.summary["gear_assembler_count"] == 1
    assert report.build_list == {
        "assemblers": 6,
        "transport_belts": 117,
        "inserters": 17,
        "small_electric_poles": 6,
    }


def test_red_science_blueprint_round_trip_entities() -> None:
    report = compile_red_science_block(RedScienceBlockRequest(target_rate_per_second=0.5))
    decoded = decode_blueprint_string(report.blueprint_string)
    entities = decoded["blueprint"]["entities"]

    assert sum(1 for entity in entities if entity["name"] == "assembling-machine-1") == 6
    assert sum(1 for entity in entities if entity["name"] == "transport-belt") == 117
    assert sum(1 for entity in entities if entity["name"] == "inserter") == 17
    assert sum(1 for entity in entities if entity["name"] == "small-electric-pole") == 6
    assert any(entity["recipe"] == "iron_gear_wheel" for entity in entities if entity["name"] == "assembling-machine-1")
    assert any(entity["recipe"] == "automation_science_pack" for entity in entities if entity["name"] == "assembling-machine-1")


def test_red_science_without_power_poles_fails_game_practical_validation() -> None:
    report = compile_red_science_block(
        RedScienceBlockRequest(target_rate_per_second=0.5, include_power_poles=False)
    )

    assert report.valid is False
    assert report.validation_confidence["structure"]["passed"] is True
    assert report.validation_confidence["placement"]["passed"] is True
    assert report.validation_confidence["game_practical"]["passed"] is False
    assert any("requires power" in error for error in report.validation_errors)
