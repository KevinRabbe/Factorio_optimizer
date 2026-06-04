from __future__ import annotations

from dataclasses import dataclass

from factorio_optimizer.layout.chain_layout_request import format_chain_layout_request
from factorio_optimizer.layout.chain_to_layout import chain_to_layout_request
from factorio_optimizer.optimizer.output_maximizer import (
    build_output_maximizer_report,
    format_output_maximizer_report,
)
from factorio_optimizer.rates.chain_solver import build_production_chain, collect_raw_inputs


RED_SCIENCE_ITEM = "automation_science_pack"


@dataclass(frozen=True)
class RedScienceMilestoneReport:
    target_per_second: float
    target_per_minute: float
    target_per_30_seconds: float
    total_machines: int
    total_energy_kw: float
    raw_inputs_per_second: dict[str, float]
    layout_request_text: str
    output_maximizer_text: str


def build_red_science_milestone(target_count: float, seconds: float, era: str = "early") -> RedScienceMilestoneReport:
    if target_count <= 0:
        raise ValueError("target_count must be positive.")
    if seconds <= 0:
        raise ValueError("seconds must be positive.")

    target_per_second = target_count / seconds
    chain = build_production_chain(RED_SCIENCE_ITEM, target_per_second, era=era)
    layout_request = chain_to_layout_request(chain)
    maximizer_report = build_output_maximizer_report(layout_request)

    return RedScienceMilestoneReport(
        target_per_second=target_per_second,
        target_per_minute=target_per_second * 60.0,
        target_per_30_seconds=target_per_second * 30.0,
        total_machines=chain.total_machines,
        total_energy_kw=chain.total_energy_kw,
        raw_inputs_per_second=collect_raw_inputs(chain.root),
        layout_request_text=format_chain_layout_request(layout_request),
        output_maximizer_text=format_output_maximizer_report(maximizer_report),
    )


def format_red_science_milestone(report: RedScienceMilestoneReport) -> str:
    raw_lines = [
        f"- {item}: {rate:.3f}/s, {rate * 60.0:.1f}/min"
        for item, rate in sorted(report.raw_inputs_per_second.items())
    ]
    if not raw_lines:
        raw_lines = ["- none"]

    return "\n".join(
        [
            "# Red Science Milestone",
            f"Target: {report.target_per_second:.3f}/s",
            f"Target per minute: {report.target_per_minute:.1f}/min",
            f"Target per 30 seconds: {report.target_per_30_seconds:.1f}/30s",
            f"Total machines: {report.total_machines}",
            f"Total energy: {report.total_energy_kw:.1f} kW",
            "Raw inputs:",
            *raw_lines,
            "",
            report.layout_request_text,
            "",
            report.output_maximizer_text,
        ]
    )
