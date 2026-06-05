from __future__ import annotations

import pytest

from factorio_optimizer.core.errors import DomainError
from factorio_optimizer.data.items import ItemMeta, ITEMS
from factorio_optimizer.data.recipes import RECIPES, Recipe
from factorio_optimizer.layout.chain_to_layout import chain_to_layout_request
from factorio_optimizer.milestones.red_science import build_red_science_milestone
from factorio_optimizer.optimizer.factory_optimizer import compare_plans
from factorio_optimizer.optimizer.output_maximizer import build_output_maximizer_report
from factorio_optimizer.rates.chain_solver import build_production_chain, collect_raw_inputs


def test_chain_solver_core_items() -> None:
    gear_chain = build_production_chain("iron_gear_wheel", 1.0, era="early")
    assert gear_chain.total_machines == 8
    assert collect_raw_inputs(gear_chain.root) == {"iron_ore": 2.0}

    circuit_chain = build_production_chain("electronic_circuit", 1.0, era="mid")
    assert circuit_chain.total_machines == 7
    assert collect_raw_inputs(circuit_chain.root) == {
        "iron_ore": 1.0,
        "copper_ore": 1.5,
    }

    engine_chain = build_production_chain("electric_engine_unit", 0.1, era="mid")
    raw_inputs = collect_raw_inputs(engine_chain.root)
    assert engine_chain.total_machines > 0
    assert raw_inputs["lubricant"] == 1.5


def test_compare_plans_for_chemical_science() -> None:
    plans = compare_plans("chemical_science_pack", 0.25, era="mid")
    assert plans
    assert plans[0].score > 0
    assert plans[0].total_machines_count > 0


def test_layout_request_and_output_maximizer() -> None:
    chain = build_production_chain("electronic_circuit", 1.0, era="mid")
    request = chain_to_layout_request(chain)
    report = build_output_maximizer_report(request)

    assert request.target_item == "electronic_circuit"
    assert len(request.modules) == 4
    assert report.average_utilization_pct > 0
    assert report.lowest_utilization_pct > 0


def test_red_science_milestone_layout() -> None:
    report = build_red_science_milestone(30.0, 30.0)
    assert report.target_per_second == 1.0
    assert report.total_machines == 22
    assert report.raw_inputs_per_second == {
        "copper_ore": 1.0,
        "iron_ore": 2.0,
    }
    assert "Layout request for automation_science_pack" in report.layout_request_text
    assert "Output maximizer report for automation_science_pack" in report.output_maximizer_text


def test_unknown_solver_item_fails_loudly() -> None:
    with pytest.raises(DomainError, match="Unknown item"):
        build_production_chain("does_not_exist", 1.0)


def test_recipe_cycle_fails_loudly(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(ITEMS, "cycle_a", ItemMeta("cycle_a", "Cycle A", "early", "intermediate", "A"))
    monkeypatch.setitem(ITEMS, "cycle_b", ItemMeta("cycle_b", "Cycle B", "early", "intermediate", "B"))
    monkeypatch.setitem(
        RECIPES,
        "cycle_a",
        Recipe("cycle_a", inputs={"cycle_b": 1}, outputs={"cycle_a": 1}, crafting_time_seconds=1.0),
    )
    monkeypatch.setitem(
        RECIPES,
        "cycle_b",
        Recipe("cycle_b", inputs={"cycle_a": 1}, outputs={"cycle_b": 1}, crafting_time_seconds=1.0),
    )

    with pytest.raises(DomainError, match="Recipe dependency cycle"):
        build_production_chain("cycle_a", 1.0)
