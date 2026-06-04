from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class OptimizationReport:
    target_item: str
    target_rate_per_second: float
    target_rate_per_minute: float
    target_rate_per_hour: float
    era: str
    power_mode: str
    best_plan: dict[str, Any]
    plans: list[dict[str, Any]]
    summary: dict[str, Any] = field(default_factory=dict)
    diagnostics: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "target_item": self.target_item,
            "target_rate_per_second": round(self.target_rate_per_second, 6),
            "target_rate_per_minute": round(self.target_rate_per_minute, 4),
            "target_rate_per_hour": round(self.target_rate_per_hour, 4),
            "era": self.era,
            "power_mode": self.power_mode,
            "best_plan": self.best_plan,
            "plans": self.plans,
            "summary": self.summary,
            "diagnostics": self.diagnostics,
        }
