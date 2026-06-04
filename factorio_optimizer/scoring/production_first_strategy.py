from __future__ import annotations

from dataclasses import dataclass

from factorio_optimizer.core.blueprint_plan import BlueprintPlan
from factorio_optimizer.rates.bottleneck_report import BottleneckReport
from factorio_optimizer.rates.efficiency_report import EfficiencyReport
from factorio_optimizer.scoring.basic_layout_strategy import BasicLayoutScoring
from factorio_optimizer.scoring.strategy import ScoreResult
from factorio_optimizer.validation.structure_validator import validate_plan_structure


@dataclass(frozen=True)
class ProductionContext:
    efficiency_report: EfficiencyReport | None = None
    bottleneck_report: BottleneckReport | None = None


class ProductionFirstScoring:
    name = "production_first"

    def __init__(self, context: ProductionContext | None = None) -> None:
        self.context = context or ProductionContext()
        self.layout_scoring = BasicLayoutScoring()

    def score(self, plan: BlueprintPlan) -> ScoreResult:
        structure_validation = validate_plan_structure(plan)
        structure_bonus = 100_000.0 if structure_validation.passed else 0.0

        efficiency_bonus = 0.0
        if self.context.efficiency_report is not None:
            efficiency_bonus = min(self.context.efficiency_report.efficiency_percent, 100.0) * 10_000.0

        bottleneck_bonus = 0.0
        if self.context.bottleneck_report is not None and not self.context.bottleneck_report.has_bottleneck:
            bottleneck_bonus = 50_000.0

        layout_score = self.layout_scoring.score(plan)
        layout_tiebreaker = layout_score.total * 0.01

        total = structure_bonus + efficiency_bonus + bottleneck_bonus + layout_tiebreaker
        return ScoreResult(
            total=total,
            label=self.name,
            details={
                "structure_bonus": structure_bonus,
                "efficiency_bonus": efficiency_bonus,
                "bottleneck_bonus": bottleneck_bonus,
                "layout_tiebreaker": layout_tiebreaker,
            },
        )
