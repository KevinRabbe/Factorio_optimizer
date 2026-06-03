from __future__ import annotations

from factorio_optimizer.layout.chain_layout_request import format_chain_layout_request
from factorio_optimizer.layout.chain_to_layout import chain_to_layout_request
from factorio_optimizer.rates.chain_solver import build_production_chain


def main() -> None:
    print("# Chain layout request smoke test")

    chain = build_production_chain("electronic_circuit", 1.0, era="mid")
    request = chain_to_layout_request(chain)

    assert request.target_item == "electronic_circuit"
    assert request.target_per_second == 1.0
    assert request.modules, "expected module requests"
    assert request.external_inputs, "expected external inputs"
    assert request.external_outputs, "expected external outputs"

    module_items = {module.item for module in request.modules}
    external_input_items = {input_item.item for input_item in request.external_inputs}

    assert "electronic_circuit" in module_items, "expected electronic circuit module request"
    assert "copper_cable" in module_items, "expected copper cable module request"
    assert "iron_plate" in module_items, "expected iron plate module request"
    assert "copper_plate" in module_items, "expected copper plate module request"
    assert "iron_ore" in external_input_items, "expected iron ore external input"
    assert "copper_ore" in external_input_items, "expected copper ore external input"

    print(format_chain_layout_request(request))
    print("PASS chain layout request")


if __name__ == "__main__":
    main()
