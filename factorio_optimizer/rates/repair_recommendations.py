from __future__ import annotations

from dataclasses import dataclass
from math import ceil

from factorio_optimizer.data.belts import BELTS
from factorio_optimizer.data.inserters import INSERTERS
from factorio_optimizer.rates.bottleneck_report import BottleneckCheck, BottleneckReport


@dataclass(frozen=True)
class RepairRecommendation:
    bottleneck_name: str
    item: str
    current_capacity_per_second: float
    required_per_second: float
    recommendation: str


def recommend_repairs(report: BottleneckReport) -> list[RepairRecommendation]:
    recommendations: list[RepairRecommendation] = []

    for check in report.checks:
        if check.status != "limited":
            continue

        if check.kind == "inserter":
            recommendations.append(_recommend_inserter_repair(check))
        elif check.kind == "belt":
            recommendations.append(_recommend_belt_repair(check))
        else:
            recommendations.append(_recommend_generic_repair(check))

    return recommendations


def _recommend_inserter_repair(check: BottleneckCheck) -> RepairRecommendation:
    better_single = [
        inserter
        for inserter in INSERTERS.values()
        if inserter.estimated_items_per_second >= check.required_per_second
    ]

    if better_single:
        best = min(better_single, key=lambda inserter: inserter.estimated_items_per_second)
        recommendation = (
            f"Replace with {best.name} "
            f"({best.estimated_items_per_second:.3f}/s capacity)."
        )
    else:
        fastest = max(INSERTERS.values(), key=lambda inserter: inserter.estimated_items_per_second)
        needed = ceil(check.required_per_second / fastest.estimated_items_per_second)
        recommendation = (
            f"Use {needed}x {fastest.name} in parallel "
            f"({fastest.estimated_items_per_second:.3f}/s each)."
        )

    return RepairRecommendation(
        bottleneck_name=check.name,
        item=check.item,
        current_capacity_per_second=check.capacity_per_second,
        required_per_second=check.required_per_second,
        recommendation=recommendation,
    )


def _recommend_belt_repair(check: BottleneckCheck) -> RepairRecommendation:
    better_single = [
        belt
        for belt in BELTS.values()
        if belt.items_per_second >= check.required_per_second
    ]

    if better_single:
        best = min(better_single, key=lambda belt: belt.items_per_second)
        recommendation = f"Replace with {best.name} ({best.items_per_second:.3f}/s capacity)."
    else:
        fastest = max(BELTS.values(), key=lambda belt: belt.items_per_second)
        needed = ceil(check.required_per_second / fastest.items_per_second)
        recommendation = f"Use {needed}x {fastest.name} lanes in parallel."

    return RepairRecommendation(
        bottleneck_name=check.name,
        item=check.item,
        current_capacity_per_second=check.capacity_per_second,
        required_per_second=check.required_per_second,
        recommendation=recommendation,
    )


def _recommend_generic_repair(check: BottleneckCheck) -> RepairRecommendation:
    return RepairRecommendation(
        bottleneck_name=check.name,
        item=check.item,
        current_capacity_per_second=check.capacity_per_second,
        required_per_second=check.required_per_second,
        recommendation="Increase capacity or reduce target throughput.",
    )


def format_repair_recommendations(recommendations: list[RepairRecommendation]) -> str:
    if not recommendations:
        return "Repair recommendations: none needed"

    lines = ["Repair recommendations:"]
    for recommendation in recommendations:
        lines.append(
            f"- {recommendation.bottleneck_name} [{recommendation.item}]: "
            f"required={recommendation.required_per_second:.3f}/s, "
            f"current={recommendation.current_capacity_per_second:.3f}/s -> "
            f"{recommendation.recommendation}"
        )

    return "\n".join(lines)
