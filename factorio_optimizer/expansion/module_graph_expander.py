from __future__ import annotations

from factorio_optimizer.core.blueprint_plan import BlueprintPlan
from factorio_optimizer.core.flows import Flow
from factorio_optimizer.modules.module_base import FactoryModule


def expand_module_graph_to_blueprint_plan(
    module: FactoryModule,
    plan_id: str | None = None,
    width: int = 9,
    height: int = 7,
) -> BlueprintPlan:
    objects = module.expand()
    flows = _flows_from_module_links(module)

    return BlueprintPlan(
        plan_id=plan_id or module.module_id,
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
