from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


BottleneckLevel = Literal["critical", "warning"]


@dataclass(frozen=True)
class BottleneckDiagnostic:
    item: str
    display_name: str
    icon: str
    level: BottleneckLevel
    reason: str
    exact_machines: float
    built_machines: int
    uptime_pct: float
    rounding_waste_pct: float
    severity: float

    def to_dict(self) -> dict:
        return {
            "item": self.item,
            "display_name": self.display_name,
            "icon": self.icon,
            "level": self.level,
            "reason": self.reason,
            "exact_machines": round(self.exact_machines, 4),
            "built_machines": self.built_machines,
            "uptime_pct": round(self.uptime_pct, 2),
            "rounding_waste_pct": round(self.rounding_waste_pct, 2),
            "severity": round(self.severity, 4),
        }


def build_bottleneck_diagnostics(best_plan: dict, limit: int = 10) -> list[dict]:
    chain = best_plan.get("chain") if best_plan else None
    if not chain:
        return []

    diagnostics: list[BottleneckDiagnostic] = []
    _collect_chain_diagnostics(chain, diagnostics)
    diagnostics.sort(key=lambda item: item.severity, reverse=True)
    return [diagnostic.to_dict() for diagnostic in diagnostics[:limit]]


def build_bottleneck_summary(diagnostics: list[dict]) -> dict:
    critical_count = sum(1 for item in diagnostics if item.get("level") == "critical")
    warning_count = sum(1 for item in diagnostics if item.get("level") == "warning")
    status = "critical" if critical_count else "warning" if warning_count else "stable"

    return {
        "status": status,
        "critical_count": critical_count,
        "warning_count": warning_count,
        "total_count": len(diagnostics),
    }


def _collect_chain_diagnostics(node: dict, diagnostics: list[BottleneckDiagnostic]) -> None:
    if node.get("is_raw"):
        return

    uptime_pct = float(node.get("uptime_pct", 0.0) or 0.0)
    exact_machines = float(node.get("machine_count_exact", 0.0) or 0.0)
    built_machines = int(node.get("machine_count_ceil", 0) or 0)
    rounding_waste = _rounding_waste(exact_machines, built_machines)

    is_critical = 0.0 < uptime_pct < 70.0
    is_warning = 70.0 <= uptime_pct < 90.0
    is_wasteful_rounding = rounding_waste > 30.0

    if is_critical or is_warning or is_wasteful_rounding:
        level: BottleneckLevel = "critical" if is_critical else "warning"
        reason = _reason(is_critical, is_warning)
        severity = (100.0 - uptime_pct) + (rounding_waste * 0.5) + (100.0 if level == "critical" else 0.0)
        diagnostics.append(
            BottleneckDiagnostic(
                item=str(node.get("item", "")),
                display_name=str(node.get("display_name", node.get("item", "unknown"))),
                icon=str(node.get("icon", "⚙️")),
                level=level,
                reason=reason,
                exact_machines=exact_machines,
                built_machines=built_machines,
                uptime_pct=uptime_pct,
                rounding_waste_pct=rounding_waste,
                severity=severity,
            )
        )

    for child in node.get("children", []) or []:
        _collect_chain_diagnostics(child, diagnostics)


def _rounding_waste(exact_machines: float, built_machines: int) -> float:
    if built_machines <= 0:
        return 0.0
    return max(0.0, built_machines - exact_machines) / built_machines * 100.0


def _reason(is_critical: bool, is_warning: bool) -> str:
    if is_critical:
        return "critical low machine uptime"
    if is_warning:
        return "ratio inefficiency warning"
    return "rounding waste from ceil(machine count)"
