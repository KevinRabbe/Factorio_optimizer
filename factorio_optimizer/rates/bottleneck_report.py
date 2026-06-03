from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


BottleneckKind = Literal["belt", "inserter", "machine", "input", "output"]
BottleneckStatus = Literal["ok", "limited"]


@dataclass(frozen=True)
class BottleneckCheck:
    name: str
    item: str
    kind: BottleneckKind
    required_per_second: float
    capacity_per_second: float

    @property
    def status(self) -> BottleneckStatus:
        return "ok" if self.capacity_per_second >= self.required_per_second else "limited"

    @property
    def capacity_percent(self) -> float:
        if self.required_per_second <= 0:
            return 100.0
        return (self.capacity_per_second / self.required_per_second) * 100.0

    @property
    def missing_per_second(self) -> float:
        return max(0.0, self.required_per_second - self.capacity_per_second)


@dataclass(frozen=True)
class BottleneckReport:
    checks: tuple[BottleneckCheck, ...]

    @property
    def has_bottleneck(self) -> bool:
        return any(check.status == "limited" for check in self.checks)


def build_bottleneck_report(checks: list[BottleneckCheck]) -> BottleneckReport:
    return BottleneckReport(checks=tuple(checks))


def format_bottleneck_report(report: BottleneckReport) -> str:
    lines = ["Bottlenecks: YES" if report.has_bottleneck else "Bottlenecks: NO"]

    for check in report.checks:
        lines.append(
            f"- {check.name} [{check.kind}] {check.item}: "
            f"required={check.required_per_second:.3f}/s, "
            f"capacity={check.capacity_per_second:.3f}/s, "
            f"capacity={check.capacity_percent:.1f}%, "
            f"missing={check.missing_per_second:.3f}/s, "
            f"status={check.status}"
        )

    return "\n".join(lines)
