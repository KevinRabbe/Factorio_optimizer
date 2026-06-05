from __future__ import annotations

import base64
import json
import zlib
from typing import Any

from factorio_optimizer.compiler.green_circuit_compiler import (
    GreenCircuitBlockRequest,
    compile_green_circuit_block,
)


def _decode_blueprint_string(blueprint_string: str) -> dict[str, Any]:
    return json.loads(zlib.decompress(base64.b64decode(blueprint_string[1:])).decode("utf-8"))


def test_green_circuit_block_for_60_per_minute_is_valid() -> None:
    report = compile_green_circuit_block(GreenCircuitBlockRequest(target_rate_per_second=1.0))

    assert report.valid is True
    assert report.validation_errors == []
    assert report.summary["target_rate_per_minute"] == 60.0
    assert report.summary["green_assembler_count"] == 1
    assert report.summary["cable_assembler_count"] == 1
    assert report.build_list == {
        "assemblers": 2,
        "transport_belts": 22,
        "inserters": 4,
        "small_electric_poles": 2,
    }


def test_green_circuit_blueprint_round_trip_entities() -> None:
    report = compile_green_circuit_block(GreenCircuitBlockRequest(target_rate_per_second=1.0))
    decoded = _decode_blueprint_string(report.blueprint_string)
    entities = decoded["blueprint"]["entities"]

    assert sum(1 for entity in entities if entity["name"] == "assembling-machine-2") == 2
    assert sum(1 for entity in entities if entity["name"] == "transport-belt") == 22
    assert sum(1 for entity in entities if entity["name"] == "inserter") == 4
    assert sum(1 for entity in entities if entity["name"] == "small-electric-pole") == 2
    assert any(entity["recipe"] == "copper_cable" for entity in entities if entity["name"] == "assembling-machine-2")
    assert any(entity["recipe"] == "electronic_circuit" for entity in entities if entity["name"] == "assembling-machine-2")
    assert all("direction" in entity for entity in entities)


def test_green_circuit_without_power_poles_fails_validation() -> None:
    report = compile_green_circuit_block(
        GreenCircuitBlockRequest(target_rate_per_second=1.0, include_power_poles=False)
    )

    assert report.valid is False
    assert any("requires power" in error for error in report.validation_errors)
