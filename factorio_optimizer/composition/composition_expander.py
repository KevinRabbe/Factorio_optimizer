from __future__ import annotations

from factorio_optimizer.composition.module_composer import CompositionPlan
from factorio_optimizer.core.blueprint_plan import BlueprintPlan
from factorio_optimizer.core.flows import Flow
from factorio_optimizer.modules.module_base import FactoryModule


def expand_composition_to_blueprint_plan(
    composition: CompositionPlan,
    width: int,
    height: int,
    plan_id: str | None = None,
) -> BlueprintPlan:
    objects = []
    flows: list[Flow] = []

    for module in composition.modules:
        objects.extend(module.expand())
        flows.extend(_flows_from_module_links(module))

    return BlueprintPlan(
        plan_id=plan_id or composition.plan_id,
        width=width,
        height=height,
        objects=objects,
        flows=flows,
    )


def _flows_from_module_links(module: FactoryModule) -> list[Flow]:
    return [
        Flow(
            flow_id=link.flow_id,
            item=link.item,
            source_id=link.source_object_id,
            target_id=link.target_object_id,
            method=link.method,
            path=link.path,
        )
        for link in module.flow_links
    ]
