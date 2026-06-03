from __future__ import annotations

from factorio_optimizer.core.blueprint_plan import BlueprintPlan
from factorio_optimizer.core.flows import Flow
from factorio_optimizer.core.objects import Position
from factorio_optimizer.modules.module_base import FactoryModule


def expand_module_to_blueprint_plan(
    module: FactoryModule,
    plan_id: str | None = None,
    width: int = 9,
    height: int = 7,
) -> BlueprintPlan:
    objects = module.expand()
    flows = _infer_simple_flows(module)

    return BlueprintPlan(
        plan_id=plan_id or module.module_id,
        width=width,
        height=height,
        objects=objects,
        flows=flows,
    )


def _infer_simple_flows(module: FactoryModule) -> list[Flow]:
    # Temporary bridge for the existing iron gear validator.
    # Later this should be replaced by explicit module connection graphs.
    if module.module_type != "iron_gear_module":
        return []

    return [
        Flow(
            flow_id="iron_to_assembler",
            item="iron_plate",
            source_id=f"{module.module_id}_iron_input_interface",
            target_id=f"{module.module_id}_gear_maker_assembler",
            method="segment_chain",
            path=[Position(x, module.position.y + 3) for x in range(module.position.x + 0, module.position.x + 5)],
        ),
        Flow(
            flow_id="gear_to_output",
            item="iron_gear_wheel",
            source_id=f"{module.module_id}_gear_maker_assembler",
            target_id=f"{module.module_id}_gear_output_interface",
            method="segment_chain",
            path=[Position(x, module.position.y + 3) for x in range(module.position.x + 6, module.position.x + 9)],
        ),
    ]
