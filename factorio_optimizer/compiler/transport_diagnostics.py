from __future__ import annotations

from dataclasses import dataclass
from math import ceil
from typing import Literal


TransportLevel = Literal["ok", "warning", "critical"]
TransportKind = Literal["belt_capacity", "inserter_capacity"]


BELT_CAPACITY_ITEMS_PER_SECOND = {
    "transport_belt": 15.0,
    "fast_transport_belt": 30.0,
    "express_transport_belt": 45.0,
}

INSERTER_CAPACITY_ITEMS_PER_SECOND = {
    "burner_inserter": 0.60,
    "inserter": 0.83,
    "fast_inserter": 2.31,
    "stack_inserter": 12.0,
}

ERA_BELT = {
    "early": "transport_belt",
    "mid": "transport_belt",
    "end": "express_transport_belt",
}

ERA_INSERTER = {
    "early": "inserter",
    "mid": "fast_inserter",
    "end": "stack_inserter",
}


@dataclass(frozen=True)
class TransportDiagnostic:
    item: str
    display_name: str
    icon: str
    kind: TransportKind
    level: TransportLevel
    required_per_second: float
    required_per_minute: float
    selected_entity: str
    selected_capacity_per_second: float
    required_entities: int
    utilization_pct: float
    recommendation: str

    def to_dict(self) -> dict:
        return {
            "item": self.item,
            "display_name": self.display_name,
            "icon": self.icon,
            "kind": self.kind,
            "level": self.level,
            "required_per_second": round(self.required_per_second, 6),
            "required_per_minute": round(self.required_per_minute, 4),
            "selected_entity": self.selected_entity,
            "selected_capacity_per_second": round(self.selected_capacity_per_second, 4),
            "required_entities": self.required_entities,
            "utilization_pct": round(self.utilization_pct, 2),
            "recommendation": self.recommendation,
        }


def build_transport_diagnostics(
    best_plan: dict,
    era: str,
    belt_name: str | None = None,
    inserter_name: str | None = None,
    limit: int = 12,
) -> list[dict]:
    chain = best_plan.get("chain") if best_plan else None
    if not chain:
        return []

    selected_belt = _resolve_belt_name(era, belt_name)
    selected_inserter = _resolve_inserter_name(era, inserter_name)
    belt_capacity = BELT_CAPACITY_ITEMS_PER_SECOND[selected_belt]
    inserter_capacity = INSERTER_CAPACITY_ITEMS_PER_SECOND[selected_inserter]

    diagnostics: list[TransportDiagnostic] = []
    _collect_transport_diagnostics(
        node=chain,
        diagnostics=diagnostics,
        belt_name=selected_belt,
        belt_capacity=belt_capacity,
        inserter_name=selected_inserter,
        inserter_capacity=inserter_capacity,
    )
    diagnostics.sort(key=lambda item: item.utilization_pct, reverse=True)
    return [diagnostic.to_dict() for diagnostic in diagnostics[:limit]]


def build_transport_summary(diagnostics: list[dict]) -> dict:
    critical_count = sum(1 for item in diagnostics if item.get("level") == "critical")
    warning_count = sum(1 for item in diagnostics if item.get("level") == "warning")
    status = "critical" if critical_count else "warning" if warning_count else "stable"
    return {
        "status": status,
        "critical_count": critical_count,
        "warning_count": warning_count,
        "total_count": len(diagnostics),
    }


def _resolve_belt_name(era: str, belt_name: str | None) -> str:
    if belt_name in BELT_CAPACITY_ITEMS_PER_SECOND:
        return belt_name
    return ERA_BELT.get(era, "transport_belt")


def _resolve_inserter_name(era: str, inserter_name: str | None) -> str:
    if inserter_name in INSERTER_CAPACITY_ITEMS_PER_SECOND:
        return inserter_name
    return ERA_INSERTER.get(era, "inserter")


def _collect_transport_diagnostics(
    node: dict,
    diagnostics: list[TransportDiagnostic],
    belt_name: str,
    belt_capacity: float,
    inserter_name: str,
    inserter_capacity: float,
) -> None:
    if node.get("is_raw"):
        return

    # Inputs into this node: each child must be transported into the recipe.
    for child in node.get("children", []) or []:
        required = float(child.get("target_per_second", 0.0) or 0.0)
        if required > 0:
            diagnostics.append(_make_belt_diagnostic(child, required, belt_name, belt_capacity))
            diagnostics.append(_make_inserter_diagnostic(child, required, inserter_name, inserter_capacity))
        _collect_transport_diagnostics(child, diagnostics, belt_name, belt_capacity, inserter_name, inserter_capacity)

    # Output from this node must also leave the producing machine.
    output_required = float(node.get("target_per_second", 0.0) or 0.0)
    if output_required > 0:
        diagnostics.append(_make_inserter_diagnostic(node, output_required, inserter_name, inserter_capacity))


def _make_belt_diagnostic(node: dict, required: float, belt_name: str, capacity: float) -> TransportDiagnostic:
    required_entities = max(1, ceil(required / capacity))
    utilization = required / capacity * 100.0
    level = _level_for_utilization(utilization)
    display = str(node.get("display_name", node.get("item", "item")))
    recommendation = _belt_recommendation(display, required, belt_name, capacity, required_entities, level)
    return TransportDiagnostic(
        item=str(node.get("item", "")),
        display_name=display,
        icon=str(node.get("icon", "📦")),
        kind="belt_capacity",
        level=level,
        required_per_second=required,
        required_per_minute=required * 60.0,
        selected_entity=belt_name,
        selected_capacity_per_second=capacity,
        required_entities=required_entities,
        utilization_pct=utilization,
        recommendation=recommendation,
    )


def _make_inserter_diagnostic(node: dict, required: float, inserter_name: str, capacity: float) -> TransportDiagnostic:
    required_entities = max(1, ceil(required / capacity))
    utilization = required / capacity * 100.0
    level = _level_for_utilization(utilization)
    display = str(node.get("display_name", node.get("item", "item")))
    recommendation = _inserter_recommendation(display, required, inserter_name, capacity, required_entities, level)
    return TransportDiagnostic(
        item=str(node.get("item", "")),
        display_name=display,
        icon=str(node.get("icon", "📦")),
        kind="inserter_capacity",
        level=level,
        required_per_second=required,
        required_per_minute=required * 60.0,
        selected_entity=inserter_name,
        selected_capacity_per_second=capacity,
        required_entities=required_entities,
        utilization_pct=utilization,
        recommendation=recommendation,
    )


def _level_for_utilization(utilization_pct: float) -> TransportLevel:
    if utilization_pct > 100.0:
        return "critical"
    if utilization_pct >= 80.0:
        return "warning"
    return "ok"


def _belt_recommendation(
    display_name: str,
    required: float,
    belt_name: str,
    capacity: float,
    required_entities: int,
    level: TransportLevel,
) -> str:
    if level == "critical":
        return (
            f"{display_name} needs {required:.2f}/s but one {belt_name} carries {capacity:.2f}/s. "
            f"Use at least {required_entities} belt lane(s), faster belts, or split the flow."
        )
    if level == "warning":
        return (
            f"{display_name} uses {required / capacity * 100.0:.1f}% of one {belt_name}. "
            "This is close to belt saturation; leave margin or split later."
        )
    return f"{display_name} fits on one {belt_name} with current target rate."


def _inserter_recommendation(
    display_name: str,
    required: float,
    inserter_name: str,
    capacity: float,
    required_entities: int,
    level: TransportLevel,
) -> str:
    if level == "critical":
        return (
            f"{display_name} needs {required:.2f}/s but one {inserter_name} moves about {capacity:.2f}/s. "
            f"Use at least {required_entities} inserter(s), faster inserters, or reduce per-inserter load."
        )
    if level == "warning":
        return (
            f"{display_name} uses {required / capacity * 100.0:.1f}% of one {inserter_name}. "
            "This is close to inserter saturation; upgrade or add a second inserter if unstable."
        )
    return f"{display_name} fits through one {inserter_name} at current target rate."
