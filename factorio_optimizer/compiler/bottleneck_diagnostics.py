from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


DiagnosticKind = Literal[
    "final_production_requirement",
    "intermediate_scaling_requirement",
    "ratio_inefficiency",
]
DiagnosticLevel = Literal["info", "warning", "critical"]


@dataclass(frozen=True)
class ProductionDiagnostic:
    item: str
    display_name: str
    icon: str
    kind: DiagnosticKind
    level: DiagnosticLevel
    reason: str
    recommendation: str
    exact_machines: float
    built_machines: int
    uptime_pct: float
    rounding_waste_pct: float
    target_per_second: float
    target_per_minute: float
    depth: int
    severity: float

    def to_dict(self) -> dict:
        return {
            "item": self.item,
            "display_name": self.display_name,
            "icon": self.icon,
            "kind": self.kind,
            "level": self.level,
            "reason": self.reason,
            "recommendation": self.recommendation,
            "exact_machines": round(self.exact_machines, 4),
            "built_machines": self.built_machines,
            "uptime_pct": round(self.uptime_pct, 2),
            "rounding_waste_pct": round(self.rounding_waste_pct, 2),
            "target_per_second": round(self.target_per_second, 6),
            "target_per_minute": round(self.target_per_minute, 4),
            "depth": self.depth,
            "severity": round(self.severity, 4),
        }


def build_bottleneck_diagnostics(best_plan: dict, limit: int = 10) -> list[dict]:
    chain = best_plan.get("chain") if best_plan else None
    if not chain:
        return []

    diagnostics: list[ProductionDiagnostic] = []
    _collect_chain_diagnostics(chain, diagnostics, depth=0)
    diagnostics.sort(key=lambda item: item.severity, reverse=True)
    return [diagnostic.to_dict() for diagnostic in diagnostics[:limit]]


def build_bottleneck_summary(diagnostics: list[dict]) -> dict:
    critical_count = sum(1 for item in diagnostics if item.get("level") == "critical")
    warning_count = sum(1 for item in diagnostics if item.get("level") == "warning")
    info_count = sum(1 for item in diagnostics if item.get("level") == "info")
    true_bottleneck_count = sum(
        1 for item in diagnostics
        if item.get("kind") == "final_production_requirement" and item.get("level") in {"critical", "warning"}
    )
    scaling_count = sum(
        1 for item in diagnostics
        if item.get("kind") == "intermediate_scaling_requirement"
    )
    status = "critical" if critical_count else "warning" if warning_count else "stable"

    return {
        "status": status,
        "critical_count": critical_count,
        "warning_count": warning_count,
        "info_count": info_count,
        "true_bottleneck_count": true_bottleneck_count,
        "scaling_count": scaling_count,
        "total_count": len(diagnostics),
    }


def _collect_chain_diagnostics(node: dict, diagnostics: list[ProductionDiagnostic], depth: int) -> None:
    if node.get("is_raw"):
        return

    uptime_pct = float(node.get("uptime_pct", 0.0) or 0.0)
    exact_machines = float(node.get("machine_count_exact", 0.0) or 0.0)
    built_machines = int(node.get("machine_count_ceil", 0) or 0)
    target_per_second = float(node.get("target_per_second", 0.0) or 0.0)
    target_per_minute = float(node.get("target_per_minute", target_per_second * 60.0) or 0.0)
    rounding_waste = _rounding_waste(exact_machines, built_machines)
    is_final_target = depth == 0

    diagnostic = _build_node_diagnostic(
        node=node,
        is_final_target=is_final_target,
        uptime_pct=uptime_pct,
        exact_machines=exact_machines,
        built_machines=built_machines,
        rounding_waste=rounding_waste,
        target_per_second=target_per_second,
        target_per_minute=target_per_minute,
        depth=depth,
    )
    if diagnostic is not None:
        diagnostics.append(diagnostic)

    for child in node.get("children", []) or []:
        _collect_chain_diagnostics(child, diagnostics, depth + 1)


def _build_node_diagnostic(
    node: dict,
    is_final_target: bool,
    uptime_pct: float,
    exact_machines: float,
    built_machines: int,
    rounding_waste: float,
    target_per_second: float,
    target_per_minute: float,
    depth: int,
) -> ProductionDiagnostic | None:
    is_critical_uptime = 0.0 < uptime_pct < 70.0
    is_warning_uptime = 70.0 <= uptime_pct < 90.0
    is_wasteful_rounding = rounding_waste > 30.0

    if is_final_target:
        if not (is_critical_uptime or is_warning_uptime or is_wasteful_rounding):
            return None
        level: DiagnosticLevel = "critical" if is_critical_uptime else "warning"
        reason = _final_reason(is_critical_uptime, is_warning_uptime)
        kind: DiagnosticKind = "final_production_requirement"
        recommendation = _final_recommendation(built_machines, uptime_pct, rounding_waste)
        severity = (100.0 - uptime_pct) + (rounding_waste * 0.5) + (100.0 if level == "critical" else 25.0)
    else:
        if not (is_critical_uptime or is_warning_uptime or is_wasteful_rounding):
            return None
        level = "info"
        kind = "intermediate_scaling_requirement"
        reason = "upstream production scaling requirement"
        recommendation = _upstream_recommendation(
            display_name=str(node.get("display_name", node.get("item", "this item"))),
            built_machines=built_machines,
            target_per_minute=target_per_minute,
        )
        severity = max(0.0, target_per_minute) + rounding_waste * 0.1

    return ProductionDiagnostic(
        item=str(node.get("item", "")),
        display_name=str(node.get("display_name", node.get("item", "unknown"))),
        icon=str(node.get("icon", "⚙️")),
        kind=kind,
        level=level,
        reason=reason,
        recommendation=recommendation,
        exact_machines=exact_machines,
        built_machines=built_machines,
        uptime_pct=uptime_pct,
        rounding_waste_pct=rounding_waste,
        target_per_second=target_per_second,
        target_per_minute=target_per_minute,
        depth=depth,
        severity=severity,
    )


def _rounding_waste(exact_machines: float, built_machines: int) -> float:
    if built_machines <= 0:
        return 0.0
    return max(0.0, built_machines - exact_machines) / built_machines * 100.0


def _final_reason(is_critical: bool, is_warning: bool) -> str:
    if is_critical:
        return "final crafting process has critical low uptime"
    if is_warning:
        return "final crafting process has ratio inefficiency"
    return "final crafting process has rounding waste from ceil(machine count)"


def _final_recommendation(built_machines: int, uptime_pct: float, rounding_waste: float) -> str:
    if uptime_pct < 70.0:
        return f"Build at least {built_machines} final machines, then check belts/inserters feeding the final recipe."
    if rounding_waste > 30.0:
        return "This is mostly rounding waste. Increase target rate or accept idle time for a cleaner small factory."
    return f"Build {built_machines} final machines. This is a ratio warning, not necessarily a broken factory."


def _upstream_recommendation(display_name: str, built_machines: int, target_per_minute: float) -> str:
    return (
        f"Scale {display_name} production to {target_per_minute:.2f}/min "
        f"by building {built_machines} upstream machine(s) or module copy/copies."
    )
