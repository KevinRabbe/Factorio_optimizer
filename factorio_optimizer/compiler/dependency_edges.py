from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DependencyEdge:
    source_item: str
    source_display_name: str
    source_icon: str
    source_machine: str
    target_item: str
    target_display_name: str
    target_icon: str
    target_machine: str
    required_per_second: float
    required_per_minute: float
    depth: int

    def to_dict(self) -> dict:
        return {
            "source_item": self.source_item,
            "source_display_name": self.source_display_name,
            "source_icon": self.source_icon,
            "source_machine": self.source_machine,
            "target_item": self.target_item,
            "target_display_name": self.target_display_name,
            "target_icon": self.target_icon,
            "target_machine": self.target_machine,
            "required_per_second": round(self.required_per_second, 6),
            "required_per_minute": round(self.required_per_minute, 4),
            "depth": self.depth,
        }


def build_dependency_edges(best_plan: dict, limit: int = 80) -> list[dict]:
    chain = best_plan.get("chain") if best_plan else None
    if not chain:
        return []

    edges: list[DependencyEdge] = []
    _collect_edges(chain, edges, depth=0)
    return [edge.to_dict() for edge in edges[:limit]]


def _collect_edges(node: dict, edges: list[DependencyEdge], depth: int) -> None:
    if node.get("is_raw"):
        return

    target_item = str(node.get("item", ""))
    target_display = str(node.get("display_name", target_item))
    target_icon = str(node.get("icon", "⚙️"))
    target_machine = str(node.get("machine_display_name", node.get("machine_name", "machine")))

    for child in node.get("children", []) or []:
        source_item = str(child.get("item", ""))
        required_per_second = float(child.get("target_per_second", 0.0) or 0.0)
        edges.append(
            DependencyEdge(
                source_item=source_item,
                source_display_name=str(child.get("display_name", source_item)),
                source_icon=str(child.get("icon", "📦")),
                source_machine=str(child.get("machine_display_name", child.get("machine_name", "source"))),
                target_item=target_item,
                target_display_name=target_display,
                target_icon=target_icon,
                target_machine=target_machine,
                required_per_second=required_per_second,
                required_per_minute=required_per_second * 60.0,
                depth=depth,
            )
        )
        _collect_edges(child, edges, depth + 1)
