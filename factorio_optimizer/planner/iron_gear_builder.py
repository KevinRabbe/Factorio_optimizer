from __future__ import annotations

from factorio_optimizer.core.blueprint_plan import BlueprintPlan
from factorio_optimizer.core.flows import Flow
from factorio_optimizer.core.objects import FactoryObject, Position


def build_iron_gear_plan() -> BlueprintPlan:
    return build_iron_gear_plan_with_layout(
        plan_id="iron_gear_v0",
        assembler_x=4,
        assembler_y=2,
        input_y=3,
        output_y=3,
    )


def build_iron_gear_plan_with_layout(
    plan_id: str,
    assembler_x: int,
    assembler_y: int,
    input_y: int,
    output_y: int,
) -> BlueprintPlan:
    plan = BlueprintPlan(
        plan_id=plan_id,
        width=9,
        height=7,
    )

    assembler_center_y = assembler_y + 1
    assembler_left_x = assembler_x
    assembler_right_x = assembler_x + 2

    iron_input = FactoryObject(
        object_id="iron_input",
        object_type="input_interface",
        position=Position(0, input_y),
        direction="east",
        item="iron_plate",
        role="source",
    )

    gear_output = FactoryObject(
        object_id="gear_output",
        object_type="output_interface",
        position=Position(8, output_y),
        direction="east",
        item="iron_gear_wheel",
        role="sink",
    )

    gear_maker = FactoryObject(
        object_id="gear_maker",
        object_type="assembler",
        position=Position(assembler_x, assembler_y),
        direction="north",
        width=3,
        height=3,
        recipe="iron_gear_wheel",
        role="producer",
    )

    input_inserter = FactoryObject(
        object_id="input_inserter",
        object_type="inserter",
        position=Position(assembler_left_x - 1, assembler_center_y),
        direction="east",
        role="ingredient_transfer",
    )

    output_inserter = FactoryObject(
        object_id="output_inserter",
        object_type="inserter",
        position=Position(assembler_right_x + 1, assembler_center_y),
        direction="east",
        role="product_transfer",
    )

    input_belts = [
        FactoryObject(
            object_id=f"iron_belt_{x}",
            object_type="belt",
            position=Position(x, input_y),
            direction="east",
            item="iron_plate",
            role="input_transport",
        )
        for x in range(1, assembler_left_x - 1)
    ]

    output_belts = [
        FactoryObject(
            object_id=f"gear_belt_{x}",
            object_type="belt",
            position=Position(x, output_y),
            direction="east",
            item="iron_gear_wheel",
            role="output_transport",
        )
        for x in range(assembler_right_x + 2, 9)
    ]

    plan.objects.extend(
        [
            iron_input,
            *input_belts,
            input_inserter,
            gear_maker,
            output_inserter,
            *output_belts,
            gear_output,
        ]
    )

    plan.flows.extend(
        [
            Flow(
                flow_id="iron_to_assembler",
                item="iron_plate",
                source_id="iron_input",
                target_id="gear_maker",
                method="belt_plus_inserter",
                path=[Position(x, input_y) for x in range(0, assembler_left_x)],
            ),
            Flow(
                flow_id="gear_to_output",
                item="iron_gear_wheel",
                source_id="gear_maker",
                target_id="gear_output",
                method="inserter_plus_belt",
                path=[Position(x, output_y) for x in range(assembler_right_x, 9)],
            ),
        ]
    )

    return plan
