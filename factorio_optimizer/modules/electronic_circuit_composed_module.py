from __future__ import annotations

from factorio_optimizer.core.objects import Position
from factorio_optimizer.modules.connections import ModuleConnection
from factorio_optimizer.modules.generic_assembler_module import build_generic_assembler_module
from factorio_optimizer.modules.module_base import FactoryModule, ModuleRate


def build_electronic_circuit_composed_module(
    module_id: str = "electronic_circuit_composed_module",
    origin: Position | None = None,
) -> FactoryModule:
    origin = origin or Position(0, 0)

    cable_module = build_generic_assembler_module(
        recipe_name="copper_cable",
        module_id=f"{module_id}_copper_cable",
        origin=Position(origin.x, origin.y),
    )
    circuit_module = build_generic_assembler_module(
        recipe_name="electronic_circuit",
        module_id=f"{module_id}_electronic_circuit",
        origin=Position(origin.x, origin.y + 8),
    )

    segments = [*cable_module.segments, *circuit_module.segments]
    input_ports = [
        port
        for port in [*cable_module.input_ports, *circuit_module.input_ports]
        if port.item != "copper_cable"
    ]
    output_ports = [*circuit_module.output_ports]

    module = FactoryModule(
        module_id=module_id,
        module_type="electronic_circuit_composed_module",
        position=origin,
        input_ports=input_ports,
        output_ports=output_ports,
        input_rates=[
            ModuleRate(item="copper_plate", amount_per_second=1.5),
            ModuleRate(item="iron_plate", amount_per_second=1.0),
        ],
        output_rates=[ModuleRate(item="electronic_circuit", amount_per_second=1.0)],
        segments=segments,
    )

    module.flow_links = [
        *getattr(cable_module, "flow_links", []),
        *getattr(circuit_module, "flow_links", []),
        ModuleConnection(
            flow_id="copper_cable_internal_to_electronic_circuit",
            item="copper_cable",
            source_port_id=f"{module_id}_copper_cable_copper_cable_maker_copper_cable_output",
            target_port_id=f"{module_id}_electronic_circuit_electronic_circuit_maker_copper_cable_input",
            source_object_id=f"{module_id}_copper_cable_copper_cable_maker_assembler",
            target_object_id=f"{module_id}_electronic_circuit_electronic_circuit_maker_assembler",
            method="composed_module",
            path=[
                Position(origin.x + 7, origin.y + 3),
                Position(origin.x + 8, origin.y + 3),
                Position(origin.x + 8, origin.y + 8),
                Position(origin.x + 4, origin.y + 8),
            ],
        ),
    ]

    return module
