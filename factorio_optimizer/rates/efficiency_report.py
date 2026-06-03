from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


EfficiencyStatus = Literal[
    "perfect",
    "near_perfect",
    "below_target",
    "no_output",
]


@dataclass(frozen=True)
class EfficiencyReport:
    item: str
    theoretical_per_hour: float
    actual_per_hour: float

    @property
    def efficiency_ratio(self) -> float:
        if self.theoretical_per_hour <= 0:
            return 0.0
        return self.actual_per_hour / self.theoretical_per_hour

    @property
    def efficiency_percent(self) -> float:
        return self.efficiency_ratio * 100.0

    @property
    def missing_per_hour(self) -> float:
        return max(0.0, self.theoretical_per_hour - self.actual_per_hour)

    @property
    def status(self) -> EfficiencyStatus:
        if self.efficiency_percent >= 99.9:
            return "perfect"
        if self.efficiency_percent >= 95.0:
            return "near_perfect"
        if self.efficiency_percent > 0.0:
            return "below_target"
        return "no_output"


def build_efficiency_report(
    item: str,
    theoretical_per_hour: float,
    actual_per_hour: float,
) -> EfficiencyReport:
    if theoretical_per_hour < 0:
        raise ValueError("theoretical_per_hour cannot be negative.")
    if actual_per_hour < 0:
        raise ValueError("actual_per_hour cannot be negative.")

    return EfficiencyReport(
        item=item,
        theoretical_per_hour=theoretical_per_hour,
        actual_per_hour=actual_per_hour,
    )


def format_efficiency_report(report: EfficiencyReport) -> str:
    return "\n".join(
        [
            f"Item: {report.item}",
            f"Theoretical output: {report.theoretical_per_hour:.1f}/hour",
            f"Actual output: {report.actual_per_hour:.1f}/hour",
            f"Efficiency: {report.efficiency_percent:.2f}%",
            f"Missing output: {report.missing_per_hour:.1f}/hour",
            f"Status: {report.status}",
        ]
    )
