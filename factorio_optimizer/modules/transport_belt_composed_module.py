from __future__ import annotations

from factorio_optimizer.core.objects import Position
from factorio_optimizer.modules.connections import ModuleConnection
from factorio_optimizer.modules.iron_gear_module import build_iron_gear_module
from factorio_optimizer.modules.module_base import FactoryModule, Footprint, ModuleRate
from factorio_optimizer.segments.assembler_segment import create_assembler_segment
from factorio_optimizer.segments.belt_segment import create_belt_segment
from factorio_optimizer.segments.inserter_segment import create_inserter_transfer_segment
from factorio_optimizer.segments.interface_segment import create_interface_segment
from factorio_optimizer.segments.segment_base import ExpandableSegment


def build_transport_belt_module_v1(
    module_id: str = "transport_belt_module_v1",
    origin: Position | None = None,
) -> FactoryModule:
    origin = origin or Position(0, 0)

    gear_module = build_iron_gear_module(
        module_id=f"{module_id}_gear_module",
        origin=Position(origin.x, origin.y),
    )

    plate_input = create_interface_segment(
        segment_id=f"{module_id}_plate_input",
        item="iron_plate",
        kind="input",
        position=Position(origin.x + 0, origin.y + 8),
        direction="east",
    )

    plate_belt = create_belt_segment(
        segment_id=f"{module_id}_plate_belt",
        item="iron_plate",
        position=Position(origin.x + 1, origin.y + 8),
        direction="east",
        length=2,
    )

    plate_inserter = create_inserter_transfer_segment(
        segment_id=f"{module_id}_plate_inserter",
        item="iron_plate",
        position=Position(origin.x + 3, origin.y + 8),
        direction="east",
        role="ingredient_transfer",
    )

    belt_assembler = create_assembler_segment(
        segment_id=f"{module_id}_belt_maker",
        recipe="transport_belt",
        input_items=("iron_plate", "iron_gear_wheel"),
        output_item="transport_belt",
        position=Position(origin.x + 4, origin.y + 7),
    )

    gear_transfer_belt = create_belt_segment(
        segment_id=f"{module_id}_gear_transfer_belt",
        item="iron_gear_wheel",
        position=Position(origin.x + 8, origin.y + 3),
        direction="east",
        length=2,
    )

    gear_input_inserter = create_inserter_transfer_segment(
        segment_id=f"{module_id}_gear_input_inserter",
        item="iron_gear_wheel",
        position=Position(origin.x + 10, origin.y + 8),
        direction="west",
        role="ingredient_transfer",
    )

    output_inserter = create_inserter_transfer_segment(
        segment_id=f"{module_id}_output_inserter",
        item="transport_belt",
        position=Position(origin.x + 7, origin.y + 8),
        direction="east",
        role="product_transfer",
    )

    output_belt = create_belt_segment(
        segment_id=f"{module_id}_output_belt",
        item="transport_belt",
        position=Position(origin.x + 8, origin.y + 8),
        direction="east",
        length=1,
    )

    output = create_interface_segment(
        segment_id=f"{module_id}_output",
        item="transport_belt",
        kind="output",
        position=Position(origin.x + 8, origin.y + 8),
        direction="east",
    )

    local_segments: list[ExpandableSegment] = [
        plate_input,
        plate_belt,
        plate_inserter,
        belt_assembler,
        gear_transfer_belt,
        gear_input_inserter,
        output_inserter,
        output_belt,
        output,
    ]

    all_segments = [*gear_module.segments, *local_segments]
    input_ports = [port for segment in all_segments for port in segment.ports if port.kind == "input"]
    output_ports = [port for segment in all_segments for port in segment.ports if port.kind == "output"]

    flow_links = [
        ModuleConnection(
            flow_id="iron_plate_to_internal_gear_module",
            item="iron_plate",
            source_port_id=f"{module_id}_gear_module_iron_input_input",
            target_port_id=f"{module_id}_gear_module_gear_maker_iron_plate_input",
            source_object_id=f"{module_id}_gear_module_iron_input_interface",
            target_object_id=f"{module_id}_gear_module_gear_maker_assembler",
            method="internal_module",
            path=[Position(x, origin.y + 3) for x in range(origin.x + 0, origin.x + 5)],
        ),
        ModuleConnection(
            flow_id="iron_plate_to_transport_belt_assembler",
            item="iron_plate",
            source_port_id=f"{module_id}_plate_input_input",
            target_port_id=f"{module_id}_belt_maker_iron_plate_input",
            source_object_id=f"{module_id}_plate_input_interface",
            target_object_id=f"{module_id}_belt_maker_assembler",
            method="segment_graph",
            path=[Position(x, origin.y + 8) for x in range(origin.x + 0, origin.x + 5)],
        ),
        ModuleConnection(
            flow_id="internal_gear_to_transport_belt_assembler",
            item="iron_gear_wheel",
            source_port_id=f"{module_id}_gear_module_gear_maker_iron_gear_wheel_output",
            target_port_id=f"{module_id}_belt_maker_iron_gear_wheel_input",
            source_object_id=f"{module_id}_gear_module_gear_maker_assembler",
            target_object_id=f"{module_id}_belt_maker_assembler",
            method="module_composition",
            path=[
                Position(origin.x + 6, origin.y + 3),
                Position(origin.x + 7, origin.y + 3),
                Position(origin.x + 8, origin.y + 3),
                Position(origin.x + 9, origin.y + 3),
                Position(origin.x + 10, origin.y + 4),
                Position(origin.x + 10, origin.y + 5),
                Position(origin.x + 10, origin.y + 6),
                Position(origin.x + 10, origin.y + 7),
                Position(origin.x + 10, origin.y + 8),
            ],
        ),
        ModuleConnection(
            flow_id="transport_belt_to_output",
            item="transport_belt",
            source_port_id=f"{module_id}_belt_maker_transport_belt_output",
            target_port_id=f"{module_id}_output_output",
            source_object_id=f"{module_id}_belt_maker_assembler",
            target_object_id=f"{module_id}_output_interface",
            method="segment_graph",
            path=[Position(x, origin.y + 8) for x in range(origin.x + 6, origin.x + 9)],
        ),
    ]

    return FactoryModule(
        module_id=module_id,
        module_type="transport_belt_module_v1",
        position=origin,
        input_ports=input_ports,
        output_ports=output_ports,
        input_rates=[ModuleRate(item="iron_plate", amount_per_second=3.0)],
        output_rates=[ModuleRate(item="transport_belt", amount_per_second=2.0)],
        segments=all_segments,
        flow_links=flow_links,
        recipe_name="transport_belt",
        machine_name="assembling_machine_1",
        footprint=Footprint(width=12, height=11),
    )
