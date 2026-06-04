from __future__ import annotations

from factorio_optimizer.layout.chain_to_layout import chain_to_layout_request
from factorio_optimizer.optimizer.output_maximizer import (
    build_output_maximizer_report,
    format_output_maximizer_report,
)
from factorio_optimizer.rates.chain_solver import build_production_chain


def main() -> None:
    print("# Output maximizer smoke test")

    chain = build_production_chain("electronic_circuit", 1.0, era="mid")
    request = chain_to_layout_request(chain)
    report = build_output_maximizer_report(request)

    assert report.groups, "expected machine groups"
    assert report.average_utilization_pct > 0.0, "expected utilization above zero"
    assert report.lowest_utilization_pct > 0.0, "expected lowest utilization above zero"

    print(format_output_maximizer_report(report))
    print("PASS output maximizer")


if __name__ == "__main__":
    main()
