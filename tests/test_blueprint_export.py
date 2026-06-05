from __future__ import annotations

import base64
import json
import zlib
from typing import Any

from factorio_optimizer.compiler.module_blueprint_compiler import (
    ModuleBlueprintRequest,
    compile_module_blueprint,
)
from factorio_optimizer.compiler.smelting_block_compiler import (
    SmeltingBlockRequest,
    compile_smelting_block,
)
from factorio_optimizer.core.blueprint_plan import BlueprintPlan
from factorio_optimizer.core.objects import FactoryObject, Position
from factorio_optimizer.export.blueprint_json_exporter import DEFAULT_BLUEPRINT_VERSION
from factorio_optimizer.export.blueprint_json_exporter import export_plan_to_blueprint_json


def _decode_blueprint_string(blueprint_string: str) -> dict[str, Any]:
    assert blueprint_string.startswith("0")
    compressed = base64.b64decode(blueprint_string[1:])
    return json.loads(zlib.decompress(compressed).decode("utf-8"))


def test_module_blueprint_round_trip() -> None:
    report = compile_module_blueprint(ModuleBlueprintRequest(recipe_name="iron_gear_wheel"))

    decoded = _decode_blueprint_string(report.blueprint_string)
    blueprint = decoded["blueprint"]
    entities = blueprint["entities"]

    assert report.structure_valid is True
    assert report.recipe_valid is True
    assert report.connection_valid is True
    assert blueprint["version"] == DEFAULT_BLUEPRINT_VERSION
    assert any(entity["name"] == "assembling-machine-1" and entity["recipe"] == "iron_gear_wheel" for entity in entities)
    assert any(entity["name"] == "transport-belt" for entity in entities)
    assert any(entity["name"] == "inserter" for entity in entities)
    assert all("direction" in entity for entity in entities)


def test_smelting_block_blueprint_round_trip() -> None:
    report = compile_smelting_block(
        SmeltingBlockRequest(recipe_name="iron_plate", target_rate_per_second=1.0)
    )

    decoded = _decode_blueprint_string(report.blueprint_string)
    blueprint = decoded["blueprint"]
    entities = blueprint["entities"]

    assert report.structure_valid is True
    assert blueprint["version"] == DEFAULT_BLUEPRINT_VERSION
    assert sum(1 for entity in entities if entity["name"] == "stone-furnace") == report.machine_count
    assert any(entity["name"] == "stone-furnace" and entity["recipe"] == "iron_plate" for entity in entities)
    assert any(entity["name"] == "transport-belt" for entity in entities)
    assert any(entity["name"] == "inserter" for entity in entities)


def test_blueprint_export_uses_entity_centers() -> None:
    plan = BlueprintPlan(
        plan_id="center_test",
        width=8,
        height=8,
        objects=[
            FactoryObject("belt", "belt", Position(1, 1), "east", entity_name="transport-belt"),
            FactoryObject("furnace", "furnace", Position(2, 2), "north", width=2, height=2, entity_name="stone-furnace"),
            FactoryObject("assembler", "assembler", Position(4, 4), "north", width=3, height=3, entity_name="assembling-machine-1"),
        ],
    )

    entities = export_plan_to_blueprint_json(plan)["blueprint"]["entities"]
    by_name = {entity["name"]: entity["position"] for entity in entities}

    assert by_name["transport-belt"] == {"x": 1.0, "y": 1.0}
    assert by_name["stone-furnace"] == {"x": 2.5, "y": 2.5}
    assert by_name["assembling-machine-1"] == {"x": 5.0, "y": 5.0}
