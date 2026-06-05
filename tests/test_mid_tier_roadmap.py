from __future__ import annotations

import pytest

pytest.importorskip("flask")

from factorio_optimizer.compiler.blueprint_blocks import (
    assembler,
    chemical_plant,
    compile_blueprint_artifacts,
    decode_blueprint_string,
    electric_pole,
    pipe,
)
from factorio_optimizer.compiler.mid_tier_compiler import (
    MidBlockRequest,
    MidTierSliceRequest,
    ScienceSliceRequest,
    compile_blue_science_slice,
    compile_early_science_slice,
    compile_mid_block,
    compile_mid_tier_slice,
    _build_blue_science_connected_plan,
)
from factorio_optimizer.core.blueprint_plan import BlueprintPlan
from factorio_optimizer.data.entities import get_entity_spec
from factorio_optimizer.web.app import app


def test_mid_tier_entity_metadata_is_present() -> None:
    expected = [
        "chemical-plant",
        "oil-refinery",
        "pipe",
        "pipe-to-ground",
        "fast-transport-belt",
        "fast-inserter",
        "steel-furnace",
        "electric-furnace",
        "lab",
        "medium-electric-pole",
    ]

    for entity_name in expected:
        spec = get_entity_spec(entity_name)
        assert spec.width >= 1
        assert spec.height >= 1


def test_recipe_machine_compatibility_rejects_chemistry_in_assembler() -> None:
    plan = BlueprintPlan(
        plan_id="bad_recipe_machine",
        width=8,
        height=8,
        objects=[
            assembler("bad_plastic_assembler", 2, 2, "plastic_bar", "assembling_machine_2"),
            electric_pole("power", 5, 3, "medium_electric_pole"),
        ],
    )

    artifacts = compile_blueprint_artifacts(plan)

    assert artifacts.valid is False
    assert any("cannot craft plastic_bar" in error for error in artifacts.validation_errors)


def test_pipe_and_chemical_plant_blueprint_round_trip() -> None:
    plan = BlueprintPlan(
        plan_id="chemical_fixture",
        width=8,
        height=8,
        objects=[
            chemical_plant("sulfur_plant", 2, 2, "sulfur"),
            pipe("water_pipe", 5, 3, "water"),
            electric_pole("power", 6, 3, "medium_electric_pole"),
        ],
    )

    artifacts = compile_blueprint_artifacts(plan)
    decoded = decode_blueprint_string(artifacts.blueprint_string)
    entities = decoded["blueprint"]["entities"]

    assert artifacts.valid is True
    assert any(entity["name"] == "chemical-plant" and entity["recipe"] == "sulfur" for entity in entities)
    assert any(entity["name"] == "pipe" for entity in entities)


def test_all_supported_mid_blocks_are_valid() -> None:
    supported_items = [
        "steel_plate",
        "advanced_circuit",
        "engine_unit",
        "plastic_bar",
        "sulfur",
        "sulfuric_acid",
        "battery",
        "piercing_rounds_magazine",
        "grenade",
        "stone_wall",
        "fast_inserter",
        "fast_transport_belt",
        "logistic_science_pack",
        "electric_engine_unit",
        "flying_robot_frame",
    ]

    for item in supported_items:
        report = compile_mid_block(MidBlockRequest(item=item, target_rate_per_second=0.25))
        assert report.valid is True, f"{item}: {report.validation_errors}"
        assert report.blueprint_string.startswith("0")


def test_connected_science_slices_are_valid() -> None:
    early = compile_early_science_slice(ScienceSliceRequest(target_rate_per_second=0.5))
    blue = compile_blue_science_slice(ScienceSliceRequest(target_rate_per_second=0.5))

    assert early.valid is True
    assert early.build_list["labs"] == 1
    assert blue.valid is True
    assert blue.blueprint_json["blueprint"]["label"] == "blue_science_connected_slice_v2"
    assert blue.summary["item"] == "chemical_science_pack"
    assert blue.build_list["labs"] == 1
    assert blue.build_list["chemical_plants"] >= 3
    assert blue.build_list["fast_transport_belts"] > 100
    assert blue.diagnostics["lane_labels"]["engine_unit_input_lane"]
    assert blue.diagnostics["lane_labels"]["sulfuric_acid_taps"]
    assert blue.diagnostics["lane_labels"]["science_output_lane"]
    assert blue.diagnostics["external_inputs"]["petroleum_gas"] > 0
    assert blue.diagnostics["external_inputs"]["water"] > 0
    assert blue.diagnostics["external_input_lanes"]["advanced_circuit"][0] == {"x": 32, "y": 11}
    assert blue.diagnostics["external_input_lanes"]["engine_unit"][0] == {"x": 34, "y": 14}
    assert blue.diagnostics["external_input_lanes"]["sulfuric_acid"][0]["pattern"] == "chemical_science_{index}_acid_tap"
    assert blue.diagnostics["output_lanes"]["chemical_science_pack"]["exits_right"] is True
    assert blue.diagnostics["output_lanes"]["chemical_science_pack"]["feeds_lab"] is True
    entities = blue.blueprint_json["blueprint"]["entities"]
    output_lane_tiles = [
        entity for entity in entities
        if entity["name"] == "fast-transport-belt"
        and entity["position"]["y"] == 8.0
    ]
    assert len(output_lane_tiles) >= 40


def test_blue_science_external_feed_tiles_are_marked_as_lane_endpoints() -> None:
    plan = _build_blue_science_connected_plan(
        science_assemblers=2,
        machine_tier="mid",
        transport_tier="mid",
        include_power_poles=True,
    )
    endpoints = {
        obj.object_id: obj
        for obj in plan.objects
        if obj.role == "input_lane_endpoint"
    }

    assert endpoints["acid_iron_input_belt"].item == "iron_plate"
    assert endpoints["engine_steel_input_belt"].item == "steel_plate"
    assert endpoints["chemical_science_0_advanced_input_belt"].item == "advanced_circuit"
    assert endpoints["engine_unit_shared_lane_11"].item == "engine_unit"


def test_unpowered_mid_block_fails_game_practical_validation() -> None:
    report = compile_mid_block(
        MidBlockRequest(
            item="advanced_circuit",
            target_rate_per_second=0.25,
            include_power_poles=False,
        )
    )

    assert report.valid is False
    assert report.validation_confidence["structure"]["passed"] is True
    assert report.validation_confidence["placement"]["passed"] is True
    assert report.validation_confidence["game_practical"]["passed"] is False


def test_mid_tier_planner_routes_targets_to_best_available_shape() -> None:
    blue = compile_mid_tier_slice(
        MidTierSliceRequest(item="chemical_science_pack", target_rate_per_second=0.5)
    )
    logistics = compile_mid_tier_slice(
        MidTierSliceRequest(item="logistic_science_pack", target_rate_per_second=0.5)
    )
    block = compile_mid_tier_slice(
        MidTierSliceRequest(item="advanced_circuit", target_rate_per_second=0.5)
    )
    military = compile_mid_tier_slice(
        MidTierSliceRequest(item="military_science_pack", target_rate_per_second=0.5)
    )

    assert blue.valid is True
    assert blue.diagnostics["planner_mode"] == "connected_blue_science_slice"
    assert logistics.valid is True
    assert logistics.diagnostics["planner_mode"] == "connected_early_science_slice"
    assert block.valid is True
    assert block.diagnostics["planner_mode"] == "single_mid_block"
    assert block.diagnostics["external_inputs"] == {
        "copper_cable": 2.0,
        "electronic_circuit": 1.0,
        "plastic_bar": 1.0,
    }
    assert military.valid is True
    assert military.diagnostics["planner_mode"] == "single_mid_block"
    assert military.diagnostics["external_inputs"] == {
        "piercing_rounds_magazine": 0.25,
        "grenade": 0.25,
        "stone_wall": 0.5,
    }


def test_new_blueprint_generation_api_routes() -> None:
    client = app.test_client()
    endpoints = [
        ("/api/generate-early-science-slice", {"rate": 30, "unit": "per_minute"}),
        ("/api/generate-mid-block", {"item": "advanced_circuit", "rate": 30, "unit": "per_minute"}),
        ("/api/generate-blue-science-slice", {"rate": 30, "unit": "per_minute"}),
        ("/api/generate-mid-tier-slice", {"item": "chemical_science_pack", "rate": 30, "unit": "per_minute"}),
        ("/api/generate-mid-tier-slice", {"item": "military_science_pack", "rate": 30, "unit": "per_minute"}),
    ]

    for endpoint, payload in endpoints:
        response = client.post(endpoint, json=payload)
        assert response.status_code == 200, response.data
        data = response.get_json()
        assert data["valid"] is True
        assert data["blueprint_string"].startswith("0")


def test_new_blueprint_generation_api_rejects_bad_inputs() -> None:
    client = app.test_client()
    bad_requests = [
        ("/api/generate-early-science-slice", {"rate": -1}),
        ("/api/generate-mid-block", {"item": "production_science_pack"}),
        ("/api/generate-mid-block", {"item": "advanced_circuit", "fluid_mode": "full_oil"}),
        ("/api/generate-blue-science-slice", {"machine_tier": "end"}),
        ("/api/generate-mid-tier-slice", {"item": "advanced_circuit", "strategy": "chaos"}),
    ]

    for endpoint, payload in bad_requests:
        response = client.post(endpoint, json=payload)
        assert response.status_code == 400
        assert response.get_json()["error"]
