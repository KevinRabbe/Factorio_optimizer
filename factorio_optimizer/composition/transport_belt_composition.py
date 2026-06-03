from __future__ import annotations

from factorio_optimizer.composition.module_composer import CompositionPlan
from factorio_optimizer.core.objects import Position
from factorio_optimizer.modules.transport_belt_composed_module import build_transport_belt_module_v1


def build_transport_belt_composition_v1(origin: Position | None = None) -> CompositionPlan:
    composition = CompositionPlan(
        plan_id="transport_belt_composition_v1",
        requested_output="transport_belt",
    )
    composition.add_module(
        build_transport_belt_module_v1(
            module_id="transport_belt_composed_v1",
            origin=origin or Position(0, 0),
        )
    )
    return composition
