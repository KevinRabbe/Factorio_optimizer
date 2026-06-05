from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_blueprint_report_ui_renders_lane_guides() -> None:
    app_js = (ROOT / "factorio_optimizer" / "web" / "static" / "app.js").read_text(encoding="utf-8")
    style_css = (ROOT / "factorio_optimizer" / "web" / "static" / "style.css").read_text(encoding="utf-8")

    assert "function renderLaneGuide" in app_js
    assert "function renderScaledPlanGuide" in app_js
    assert "function renderBlueprintBuildSummary" in app_js
    assert "external_input_lanes" in app_js
    assert "output_lanes" in app_js
    assert "Repeatable Paste Plan" in app_js
    assert "blueprint-build-chip" in app_js
    assert ".lane-guide" in style_css
    assert ".lane-row" in style_css
    assert ".scaled-plan-guide" in style_css
    assert ".scaled-plan-row" in style_css
    assert ".blueprint-build-summary" in style_css
    assert ".blueprint-build-chip" in style_css
    assert "id=\"blueprint-string-output\"" in app_js
    assert "Clipboard blocked. Press Ctrl+C now." in app_js
    assert ".blueprint-string-output" in style_css
    assert ".blueprint-copy-status" in style_css


def test_build_list_ui_renders_collapsible_totals() -> None:
    build_js = (ROOT / "factorio_optimizer" / "web" / "static" / "ui_build_list_adapter.js").read_text(encoding="utf-8")
    style_css = (ROOT / "factorio_optimizer" / "web" / "static" / "style.css").read_text(encoding="utf-8")

    assert "summarizeBuildListItems" in build_js
    assert "build-total-chip" in build_js
    assert "<details class=\"build-block\"" in build_js
    assert "<details class=\"build-category\"" in build_js
    assert ".build-total-row" in style_css
    assert ".build-line-item" in style_css


def test_blueprint_button_routes_to_practical_generators() -> None:
    response_js = (ROOT / "factorio_optimizer" / "web" / "static" / "ui_response_adapter.js").read_text(encoding="utf-8")
    app_js = (ROOT / "factorio_optimizer" / "web" / "static" / "app.js").read_text(encoding="utf-8")
    index_html = (ROOT / "factorio_optimizer" / "web" / "static" / "index.html").read_text(encoding="utf-8")

    assert "function selectedBlueprintRequest" in response_js
    assert "renderBlueprintReport(request.label, data)" in response_js
    assert "'/api/generate-green-circuit-block'" in response_js
    assert "'/api/generate-red-science-block'" in response_js
    assert "'/api/generate-early-science-slice'" in response_js
    assert "'/api/generate-mid-tier-slice'" in response_js
    assert "'/api/generate-module-blueprint'" in response_js
    assert "'chemical_science_pack'" in response_js
    assert "'military_science_pack'" in response_js
    assert "function runScaledEarlySciencePlanner" in app_js
    assert "/api/generate-scaled-early-science-plan" in app_js
    assert "Plan Scaled Red + Green" in index_html
