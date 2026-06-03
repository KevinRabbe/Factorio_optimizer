from __future__ import annotations

from factorio_optimizer.web.app import app


def _assert_ok(response, endpoint: str) -> dict | list:
    assert response.status_code == 200, f"{endpoint}: expected 200, got {response.status_code}: {response.data!r}"
    payload = response.get_json()
    assert payload is not None, f"{endpoint}: expected JSON response"
    return payload


def main() -> None:
    print("# Flask API smoke tests")

    client = app.test_client()

    items = _assert_ok(client.get("/api/items"), "/api/items")
    assert isinstance(items, list), "/api/items: expected list"
    assert items, "/api/items: expected at least one item"
    print(f"PASS /api/items: {len(items)} items")

    modules = _assert_ok(client.get("/api/modules"), "/api/modules")
    assert isinstance(modules, dict), "/api/modules: expected object"
    print(f"PASS /api/modules: eras={list(modules.keys())}")

    layouts = _assert_ok(client.get("/api/layouts"), "/api/layouts")
    assert isinstance(layouts, list), "/api/layouts: expected list"
    print(f"PASS /api/layouts: {len(layouts)} saved layouts")

    optimize_payload = {
        "item": "electronic_circuit",
        "rate": 60,
        "unit": "per_minute",
        "era": "mid",
        "modules": [],
    }
    optimized = _assert_ok(client.post("/api/optimize", json=optimize_payload), "/api/optimize")
    assert optimized["item"] == "electronic_circuit", "/api/optimize: wrong item returned"
    assert optimized["plans"], "/api/optimize: expected at least one plan"
    assert "furnace_mode" in optimized, "/api/optimize: missing furnace_mode"
    assert "furnace_mode_note" in optimized, "/api/optimize: missing furnace_mode_note"
    print(
        "PASS /api/optimize: "
        f"plans={len(optimized['plans'])}, "
        f"furnace_mode={optimized['furnace_mode']}"
    )


if __name__ == "__main__":
    main()
