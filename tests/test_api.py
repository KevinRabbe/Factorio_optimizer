from __future__ import annotations

import pytest

pytest.importorskip("flask")

from factorio_optimizer.web.app import app


def _assert_ok(response, endpoint: str) -> dict | list:
    assert response.status_code == 200, f"{endpoint}: {response.data!r}"
    payload = response.get_json()
    assert payload is not None
    return payload


def test_static_api_endpoints() -> None:
    client = app.test_client()

    items = _assert_ok(client.get("/api/items"), "/api/items")
    assert items

    modules = _assert_ok(client.get("/api/modules"), "/api/modules")
    assert isinstance(modules, dict)

    layouts = _assert_ok(client.get("/api/layouts"), "/api/layouts")
    assert isinstance(layouts, list)


def test_optimize_endpoint() -> None:
    client = app.test_client()
    payload = {
        "item": "electronic_circuit",
        "rate": 60,
        "unit": "per_minute",
        "era": "mid",
        "modules": [],
    }

    optimized = _assert_ok(client.post("/api/optimize", json=payload), "/api/optimize")

    assert optimized["item"] == "electronic_circuit"
    assert optimized["plans"]
    assert optimized["best_plan"]
    assert optimized["summary"]
    assert optimized["diagnostics"]["report_schema_version"] == 7


def test_blueprint_generation_endpoints() -> None:
    client = app.test_client()

    module = _assert_ok(
        client.post("/api/generate-module-blueprint", json={"recipe_name": "iron_gear_wheel"}),
        "/api/generate-module-blueprint",
    )
    assert module["valid"] is True
    assert module["blueprint_string"].startswith("0")

    smelting = _assert_ok(
        client.post(
            "/api/generate-smelting-block",
            json={"recipe_name": "iron_plate", "rate": 60, "unit": "per_minute"},
        ),
        "/api/generate-smelting-block",
    )
    assert smelting["valid"] is True
    assert smelting["blueprint_string"].startswith("0")

    green = _assert_ok(
        client.post(
            "/api/generate-green-circuit-block",
            json={"rate": 60, "unit": "per_minute", "era": "mid"},
        ),
        "/api/generate-green-circuit-block",
    )
    assert green["valid"] is True
    assert green["blueprint_string"].startswith("0")

    red = _assert_ok(
        client.post(
            "/api/generate-red-science-block",
            json={"rate": 30, "unit": "per_minute", "era": "early"},
        ),
        "/api/generate-red-science-block",
    )
    assert red["valid"] is True
    assert red["blueprint_string"].startswith("0")

    scaled = _assert_ok(
        client.post(
            "/api/generate-scaled-early-science-plan",
            json={"rate": 300, "unit": "per_minute"},
        ),
        "/api/generate-scaled-early-science-plan",
    )
    assert scaled["valid"] is True
    assert scaled["summary"]["block_count"] == 5
    assert scaled["diagnostics"]["selection_mode"] == "auto"
    assert scaled["diagnostics"]["selected_block_rate_per_minute"] == 60.0
    assert scaled["diagnostics"]["planner_mode"] == "scaled_repeatable_early_science"

    scaled_green = _assert_ok(
        client.post(
            "/api/generate-scaled-green-circuit-plan",
            json={"rate": 300, "unit": "per_minute"},
        ),
        "/api/generate-scaled-green-circuit-plan",
    )
    assert scaled_green["valid"] is True
    assert scaled_green["summary"]["block_count"] == 4
    assert scaled_green["summary"]["capacity_per_minute"] == 360.0
    assert scaled_green["summary"]["block_rate_per_minute"] == 90.0
    assert scaled_green["diagnostics"]["selection_mode"] == "auto"
    assert scaled_green["diagnostics"]["planner_mode"] == "scaled_repeatable_green_circuits"


def test_optimize_rejects_bad_inputs() -> None:
    client = app.test_client()
    bad_payloads = [
        {"rate": "abc"},
        {"rate": -1},
        {"era": "banana"},
        {"unit": "per_week"},
        {"modules": "not-list"},
        {"item": "does_not_exist"},
    ]

    for payload in bad_payloads:
        response = client.post("/api/optimize", json=payload)
        assert response.status_code == 400
        assert response.get_json()["error"]


def test_blueprint_routes_reject_bad_rates() -> None:
    client = app.test_client()
    endpoints = [
        "/api/generate-smelting-block",
        "/api/generate-green-circuit-block",
        "/api/generate-red-science-block",
        "/api/generate-scaled-early-science-plan",
        "/api/generate-scaled-green-circuit-plan",
    ]

    for endpoint in endpoints:
        response = client.post(endpoint, json={"recipe_name": "iron_plate", "rate": "abc"})
        assert response.status_code == 400
        assert response.get_json()["error"]

        response = client.post(endpoint, json={"recipe_name": "iron_plate", "rate": -1})
        assert response.status_code == 400
        assert response.get_json()["error"]


def test_scaled_early_science_route_rejects_invalid_block_rate() -> None:
    client = app.test_client()

    response = client.post(
        "/api/generate-scaled-early-science-plan",
        json={"rate": 30, "unit": "per_minute", "block_rate": 60, "block_unit": "per_minute"},
    )

    assert response.status_code == 400
    assert "block_rate" in response.get_json()["error"]


def test_scaled_green_circuit_route_rejects_invalid_block_rate() -> None:
    client = app.test_client()

    response = client.post(
        "/api/generate-scaled-green-circuit-plan",
        json={"rate": 60, "unit": "per_minute", "block_rate": 120, "block_unit": "per_minute"},
    )

    assert response.status_code == 400
    assert "block_rate" in response.get_json()["error"]
