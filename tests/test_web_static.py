from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_blueprint_report_ui_renders_lane_guides() -> None:
    app_js = (ROOT / "factorio_optimizer" / "web" / "static" / "app.js").read_text(encoding="utf-8")
    style_css = (ROOT / "factorio_optimizer" / "web" / "static" / "style.css").read_text(encoding="utf-8")

    assert "function renderLaneGuide" in app_js
    assert "function renderScaledPlanGuide" in app_js
    assert "function renderStarterMallGuide" in app_js
    assert "function renderScaledCandidateChips" in app_js
    assert "function renderBlueprintBuildSummary" in app_js
    assert "external_input_lanes" in app_js
    assert "output_lanes" in app_js
    assert "Repeatable Paste Plan" in app_js
    assert "Starter Mall Outputs" in app_js
    assert "Candidate Blocks" in app_js
    assert "blueprint-build-chip" in app_js
    assert ".lane-guide" in style_css
    assert ".lane-row" in style_css
    assert ".scaled-plan-guide" in style_css
    assert ".scaled-plan-row" in style_css
    assert ".blueprint-build-chip-active" in style_css
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
    assert "function runScaledGreenCircuitPlanner" in app_js
    assert "function runStarterMiningGenerator" in app_js
    assert "function runStarterMallGenerator" in app_js
    assert "function runStarterSmeltingGenerator" in app_js
    assert "function runStarterBrickGenerator" in app_js
    assert "function runStarterSteelGenerator" in app_js
    assert "/api/generate-scaled-early-science-plan" in app_js
    assert "/api/generate-scaled-green-circuit-plan" in app_js
    assert "/api/generate-mining-upgrade-block" in app_js
    assert "/api/generate-brick-smelting-block" in app_js
    assert "/api/generate-starter-steel-block" in app_js
    assert "/api/generate-starter-mall" in app_js
    assert "/api/generate-smelting-upgrade-block" in app_js
    assert "size_mode: 'half_yellow_15'" in app_js
    assert "size_mode: 'full_yellow_30'" in app_js
    assert "size_mode: 'full_belt_48'" in app_js
    assert "Starter Brick Line — 24 Furnaces" in app_js
    assert "Starter Steel Block — 12 Furnaces" in app_js
    assert "Starter Mall — Feed from Smelting" in app_js
    assert "Starter Base" in index_html
    assert "Generate Mining Chunk â€” Electric Drills" in index_html
    assert "Generate Starter Mall" in index_html
    assert "Generate Coal Smelting Block — 48 Furnaces" in index_html
    assert "Plan Scaled Red + Green" in index_html
    assert "Plan Scaled Green Circuits" in index_html
