from __future__ import annotations

from factorio_optimizer.core.objects import Position
from factorio_optimizer.data.machines import get_machine
from factorio_optimizer.data.recipes import get_recipe
from factorio_optimizer.modules.connections import ModuleConnection
from factorio_optimizer.modules.module_base import FactoryModule, Footprint, ModuleRate
from factorio_optimizer.segments.assembler_segment import create_assembler_segment
from factorio_optimizer.segments.belt_segment import create_belt_segment
from factorio_optimizer.segments.inserter_segment import create_inserter_transfer_segment
from factorio_optimizer.segments.interface_segment import create_interface_segment


def build_generic_assembler_module(
    recipe_name: str,
    module_id: str | None = None,
    origin: Position | None = None,
    machine_name: str = "assembling_machine_1",
) -> FactoryModule:
    origin = origin or Position(0, 0)
    recipe = get_recipe(recipe_name)
    machine = get_machine(machine_name)

    if recipe.category not in machine.allowed_categories:
        raise ValueError(
            f"Machine {machine.name} cannot craft recipe {recipe.name} "
            f"with category {recipe.category}."
        )

    module_id = module_id or f"generic_{recipe_name}_module"
    output_item = _single_output_item(recipe.outputs)
    input_items = tuple(recipe.inputs.keys())

    segments = []
    input_lane_y_by_item: dict[str, int] = {}
    assembler_y = origin.y + 1 + len(input_items)
    assembler_x = origin.x + 4

    for index, item in enumerate(input_items):
        lane_y = origin.y + index
        input_lane_y_by_item[item] = lane_y
        segments.extend(
            [
                create_interface_segment(
                    segment_id=f"{module_id}_{item}_input",
                    item=item,
                    kind="input",
                    position=Position(origin.x, lane_y),
                    direction="east",
                ),
                create_belt_segment(
                    segment_id=f"{module_id}_{item}_input_belt",
                    item=item,
                    position=Position(origin.x + 1, lane_y),
                    direction="east",
                    length=2,
                ),
                create_inserter_transfer_segment(
                    segment_id=f"{module_id}_{item}_input_inserter",
                    item=item,
                    position=Position(origin.x + 3, lane_y),
                    direction="east",
                    role="ingredient_transfer",
                ),
            ]
        )

    assembler = create_assembler_segment(
        segment_id=f"{module_id}_{recipe_name}_maker",
        recipe=recipe_name,
        input_items=input_items,
        output_item=output_item,
        position=Position(assembler_x, assembler_y),
        machine_type=machine_name,
    )
    segments.append(assembler)

    output_lane_y = assembler_y + 1
    segments.extend(
        [
            create_inserter_transfer_segment(
                segment_id=f"{module_id}_{output_item}_output_inserter",
                item=output_item,
                position=Position(assembler_x + 3, output_lane_y),
                direction="east",
                role="product_transfer",
            ),
            create_belt_segment(
                segment_id=f"{module_id}_{output_item}_output_belt",
                item=output_item,
                position=Position(assembler_x + 4, output_lane_y),
                direction="east",
                length=1,
            ),
            create_interface_segment(
                segment_id=f"{module_id}_{output_item}_output",
                item=output_item,
                kind="output",
                position=Position(assembler_x + 4, output_lane_y),
                direction="east",
            ),
        ]
    )

    input_ports = [port for segment in segments for port in segment.ports if port.kind == "input"]
    output_ports = [port for segment in segments for port in segment.ports if port.kind == "output"]

    crafts_per_second = machine.crafting_speed / recipe.crafting_time_seconds
    input_rates = [
        ModuleRate(item=item, amount_per_second=amount * crafts_per_second)
        for item, amount in recipe.inputs.items()
    ]
    output_rates = [
        ModuleRate(item=item, amount_per_second=amount * crafts_per_second)
        for item, amount in recipe.outputs.items()
    ]
    flow_links = _build_flow_links(
        module_id=module_id,
        recipe_name=recipe_name,
        input_items=input_items,
        output_item=output_item,
        origin=origin,
        assembler_x=assembler_x,
        assembler_y=assembler_y,
        output_lane_y=output_lane_y,
        input_lane_y_by_item=input_lane_y_by_item,
    )

    return FactoryModule(
        module_id=module_id,
        module_type="generic_assembler_module",
        position=origin,
        input_ports=input_ports,
        output_ports=output_ports,
        input_rates=input_rates,
        output_rates=output_rates,
        segments=segments,
        flow_links=flow_links,
        recipe_name=recipe_name,
        machine_name=machine_name,
        footprint=Footprint(width=9, height=output_lane_y - origin.y + 2),
    )


def _build_flow_links(
    module_id: str,
    recipe_name: str,
    input_items: tuple[str, ...],
    output_item: str,
    origin: Position,
    assembler_x: int,
    assembler_y: int,
    output_lane_y: int,
    input_lane_y_by_item: dict[str, int],
) -> list[ModuleConnection]:
    links: list[ModuleConnection] = []

    for item in input_items:
        lane_y = input_lane_y_by_item[item]
        links.append(
            ModuleConnection(
                flow_id=f"{item}_to_{recipe_name}_assembler",
                item=item,
                source_port_id=f"{module_id}_{item}_input_input",
                target_port_id=f"{module_id}_{recipe_name}_maker_{item}_input",
                source_object_id=f"{module_id}_{item}_input_interface",
                target_object_id=f"{module_id}_{recipe_name}_maker_assembler",
                method="generic_module",
                path=[Position(x, lane_y) for x in range(origin.x, assembler_x + 1)],
            )
        )

    links.append(
        ModuleConnection(
            flow_id=f"{output_item}_to_output",
            item=output_item,
            source_port_id=f"{module_id}_{recipe_name}_maker_{output_item}_output",
            target_port_id=f"{module_id}_{output_item}_output_output",
            source_object_id=f"{module_id}_{recipe_name}_maker_assembler",
            target_object_id=f"{module_id}_{output_item}_output_interface",
            method="generic_module",
            path=[Position(x, output_lane_y) for x in range(assembler_x + 3, assembler_x + 5)],
        )
    )

    return links


def _single_output_item(outputs: dict[str, float]) -> str:
    if len(outputs) != 1:
        raise ValueError("Generic assembler module currently supports exactly one output item.")
    return next(iter(outputs.keys()))
