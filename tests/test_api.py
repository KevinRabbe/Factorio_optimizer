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
    ]

    for endpoint in endpoints:
        response = client.post(endpoint, json={"recipe_name": "iron_plate", "rate": "abc"})
        assert response.status_code == 400
        assert response.get_json()["error"]

        response = client.post(endpoint, json={"recipe_name": "iron_plate", "rate": -1})
        assert response.status_code == 400
        assert response.get_json()["error"]
