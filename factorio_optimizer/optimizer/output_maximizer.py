from __future__ import annotations

from dataclasses import dataclass

from factorio_optimizer.layout.chain_layout_request import ChainLayoutRequest


@dataclass(frozen=True)
class MachineOutputGroup:
    item: str
    machine_name: str
    machine_count: int
    target_per_second: float
    capacity_per_second: float

    @property
    def utilization_pct(self) -> float:
        if self.capacity_per_second <= 0:
            return 0.0
        return min(100.0, (self.target_per_second / self.capacity_per_second) * 100.0)

    @property
    def spare_capacity_per_second(self) -> float:
        return max(0.0, self.capacity_per_second - self.target_per_second)


@dataclass(frozen=True)
class OutputMaximizerReport:
    target_item: str
    target_per_second: float
    groups: tuple[MachineOutputGroup, ...]

    @property
    def average_utilization_pct(self) -> float:
        if not self.groups:
            return 0.0
        return sum(group.utilization_pct for group in self.groups) / len(self.groups)

    @property
    def lowest_utilization_pct(self) -> float:
        if not self.groups:
            return 0.0
        return min(group.utilization_pct for group in self.groups)


def build_output_maximizer_report(request: ChainLayoutRequest) -> OutputMaximizerReport:
    groups = tuple(
        MachineOutputGroup(
            item=module.item,
            machine_name=module.machine_name,
            machine_count=module.machine_count,
            target_per_second=module.target_per_second,
            capacity_per_second=module.capacity_per_second,
        )
        for module in request.modules
    )
    return OutputMaximizerReport(
        target_item=request.target_item,
        target_per_second=request.target_per_second,
        groups=groups,
    )


def format_output_maximizer_report(report: OutputMaximizerReport) -> str:
    lines = [
        f"Output maximizer report for {report.target_item}: {report.target_per_second:.3f}/s",
        f"Average machine utilization: {report.average_utilization_pct:.1f}%",
        f"Lowest machine utilization: {report.lowest_utilization_pct:.1f}%",
        "Machine groups:",
    ]

    for group in report.groups:
        lines.append(
            f"- {group.item}: {group.machine_count}x {group.machine_name}, "
            f"target={group.target_per_second:.3f}/s, "
            f"capacity={group.capacity_per_second:.3f}/s, "
            f"utilization={group.utilization_pct:.1f}%, "
            f"spare={group.spare_capacity_per_second:.3f}/s"
        )

    if not report.groups:
        lines.append("- none")

    return "\n".join(lines)
