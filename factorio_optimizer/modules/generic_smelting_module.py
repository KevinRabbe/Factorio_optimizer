from __future__ import annotations

from factorio_optimizer.core.objects import Position
from factorio_optimizer.data.machines import get_machine
from factorio_optimizer.data.recipes import get_recipe
from factorio_optimizer.modules.connections import ModuleConnection
from factorio_optimizer.modules.module_base import FactoryModule, Footprint, ModuleRate
from factorio_optimizer.segments.belt_segment import create_belt_segment
from factorio_optimizer.segments.furnace_segment import create_furnace_segment
from factorio_optimizer.segments.inserter_segment import create_inserter_transfer_segment
from factorio_optimizer.segments.interface_segment import create_interface_segment


def build_generic_smelting_module(
    recipe_name: str,
    module_id: str | None = None,
    origin: Position | None = None,
    machine_name: str = "stone_furnace",
) -> FactoryModule:
    origin = origin or Position(0, 0)
    recipe = get_recipe(recipe_name)
    machine = get_machine(machine_name)

    if recipe.category != "smelting":
        raise ValueError(f"Recipe {recipe.name} is not a smelting recipe.")
    if recipe.category not in machine.allowed_categories:
        raise ValueError(
            f"Machine {machine.name} cannot craft recipe {recipe.name} "
            f"with category {recipe.category}."
        )

    module_id = module_id or f"generic_{recipe_name}_smelting_module"
    output_item = _single_output_item(recipe.outputs)
    input_items = tuple(recipe.inputs.keys())
    input_item = _single_input_item(recipe.inputs)

    input_lane_y = origin.y + 2
    furnace_x = origin.x + 4
    furnace_y = origin.y + 1
    output_lane_y = origin.y + 2

    segments = [
        create_interface_segment(
            segment_id=f"{module_id}_{input_item}_input",
            item=input_item,
            kind="input",
            position=Position(origin.x, input_lane_y),
            direction="east",
        ),
        create_belt_segment(
            segment_id=f"{module_id}_{input_item}_input_belt",
            item=input_item,
            position=Position(origin.x + 1, input_lane_y),
            direction="east",
            length=2,
        ),
        create_inserter_transfer_segment(
            segment_id=f"{module_id}_{input_item}_input_inserter",
            item=input_item,
            position=Position(origin.x + 3, input_lane_y),
            direction="east",
            role="ingredient_transfer",
        ),
        create_furnace_segment(
            segment_id=f"{module_id}_{recipe_name}_maker",
            recipe=recipe_name,
            input_items=input_items,
            output_item=output_item,
            position=Position(furnace_x, furnace_y),
            machine_type=machine_name,
        ),
        create_inserter_transfer_segment(
            segment_id=f"{module_id}_{output_item}_output_inserter",
            item=output_item,
            position=Position(origin.x + 6, output_lane_y),
            direction="east",
            role="product_transfer",
        ),
        create_belt_segment(
            segment_id=f"{module_id}_{output_item}_output_belt",
            item=output_item,
            position=Position(origin.x + 7, output_lane_y),
            direction="east",
            length=1,
        ),
        create_interface_segment(
            segment_id=f"{module_id}_{output_item}_output",
            item=output_item,
            kind="output",
            position=Position(origin.x + 7, output_lane_y),
            direction="east",
        ),
    ]

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

    flow_links = [
        ModuleConnection(
            flow_id=f"{input_item}_to_{recipe_name}_furnace",
            item=input_item,
            source_port_id=f"{module_id}_{input_item}_input_input",
            target_port_id=f"{module_id}_{recipe_name}_maker_{input_item}_input",
            source_object_id=f"{module_id}_{input_item}_input_interface",
            target_object_id=f"{module_id}_{recipe_name}_maker_furnace",
            method="generic_smelting_module",
            path=[Position(x, input_lane_y) for x in range(origin.x, furnace_x + 1)],
        ),
        ModuleConnection(
            flow_id=f"{output_item}_to_output",
            item=output_item,
            source_port_id=f"{module_id}_{recipe_name}_maker_{output_item}_output",
            target_port_id=f"{module_id}_{output_item}_output_output",
            source_object_id=f"{module_id}_{recipe_name}_maker_furnace",
            target_object_id=f"{module_id}_{output_item}_output_interface",
            method="generic_smelting_module",
            path=[Position(x, output_lane_y) for x in range(origin.x + 6, origin.x + 8)],
        ),
    ]

    return FactoryModule(
        module_id=module_id,
        module_type="generic_smelting_module",
        position=origin,
        input_ports=input_ports,
        output_ports=output_ports,
        input_rates=input_rates,
        output_rates=output_rates,
        segments=segments,
        flow_links=flow_links,
        recipe_name=recipe_name,
        machine_name=machine_name,
        footprint=Footprint(width=8, height=5),
    )


def _single_input_item(inputs: dict[str, float]) -> str:
    if len(inputs) != 1:
        raise ValueError("Generic smelting module currently supports exactly one input item.")
    return next(iter(inputs.keys()))


def _single_output_item(outputs: dict[str, float]) -> str:
    if len(outputs) != 1:
        raise ValueError("Generic smelting module currently supports exactly one output item.")
    return next(iter(outputs.keys()))
