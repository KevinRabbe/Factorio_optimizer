from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from factorio_optimizer.core.blueprint_plan import BlueprintPlan


@dataclass(frozen=True)
class ScoreResult:
    total: float
    label: str
    details: dict[str, float]


class ScoringStrategy(Protocol):
    name: str

    def score(self, plan: BlueprintPlan) -> ScoreResult:
        ...
