from __future__ import annotations

from factorio_optimizer.core.objects import Position
from factorio_optimizer.modules.connections import ModuleConnection
from factorio_optimizer.modules.iron_gear_module import build_iron_gear_module
from factorio_optimizer.modules.module_base import FactoryModule


def build_iron_gear_graph_module(
    module_id: str = "iron_gear_graph_module",
    origin: Position | None = None,
) -> FactoryModule:
    module = build_iron_gear_module(module_id=module_id, origin=origin)
    origin = origin or Position(0, 0)

    module.flow_links = [
        ModuleConnection(
            flow_id="iron_to_assembler",
            item="iron_plate",
            source_port_id=f"{module_id}_iron_input_input",
            target_port_id=f"{module_id}_gear_maker_iron_plate_input",
            source_object_id=f"{module_id}_iron_input_interface",
            target_object_id=f"{module_id}_gear_maker_assembler",
            method="segment_graph",
            path=[Position(x, origin.y + 3) for x in range(origin.x + 0, origin.x + 5)],
        ),
        ModuleConnection(
            flow_id="gear_to_output",
            item="iron_gear_wheel",
            source_port_id=f"{module_id}_gear_maker_iron_gear_wheel_output",
            target_port_id=f"{module_id}_gear_output_output",
            source_object_id=f"{module_id}_gear_maker_assembler",
            target_object_id=f"{module_id}_gear_output_interface",
            method="segment_graph",
            path=[Position(x, origin.y + 3) for x in range(origin.x + 6, origin.x + 9)],
        ),
    ]

    return module
