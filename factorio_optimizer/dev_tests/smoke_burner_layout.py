from __future__ import annotations

from factorio_optimizer.layout.chain_layout_request import format_chain_layout_request
from factorio_optimizer.layout.chain_to_layout import chain_to_layout_request
from factorio_optimizer.rates.chain_solver import build_production_chain


def main() -> None:
    print("# Burner layout input smoke test")

    chain = build_production_chain("iron_plate", 1.0, era="early")
    request = chain_to_layout_request(chain)

    external_items = {item.item for item in request.external_inputs}
    burner_items = {item.item for item in request.burner_inputs}
    burner_consumers = {item.consumer_machine_name for item in request.burner_inputs}

    assert "iron_ore" in external_items, "expected iron ore as recipe input"
    assert "coal" in external_items, "expected coal as external support input"
    assert "coal" in burner_items, "expected coal as burner input"
    assert "stone_furnace" in burner_consumers, "expected stone furnace burner consumer"

    print(format_chain_layout_request(request))
    print("PASS burner layout input")


if __name__ == "__main__":
    main()
