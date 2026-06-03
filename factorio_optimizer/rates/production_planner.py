from __future__ import annotations

from dataclasses import dataclass
from math import ceil

from factorio_optimizer.data.machines import get_machine
from factorio_optimizer.data.recipes import get_recipe
from factorio_optimizer.rates.machine_rate import calculate_machine_recipe_rate
from factorio_optimizer.rates.mining_rate import calculate_required_miners


@dataclass(frozen=True)
class RecipeMachinePlan:
    recipe_name: str
    machine_name: str
    machine_count: int
    target_output_item: str
    target_output_per_second: float
    capacity_output_per_second: float
    required_inputs_per_second: dict[str, float]

    @property
    def target_output_per_hour(self) -> float:
        return self.target_output_per_second * 3600.0

    @property
    def capacity_output_per_hour(self) -> float:
        return self.capacity_output_per_second * 3600.0


@dataclass(frozen=True)
class TransportBeltRawIronPlan:
    target_transport_belt_per_hour: float
    belt_plan: RecipeMachinePlan
    gear_plan: RecipeMachinePlan
    iron_plate_furnaces: int
    iron_plate_required_per_second: float
    iron_plate_capacity_per_second: float
    iron_ore_miners: int

    @property
    def iron_plate_required_per_hour(self) -> float:
        return self.iron_plate_required_per_second * 3600.0

    @property
    def iron_plate_capacity_per_hour(self) -> float:
        return self.iron_plate_capacity_per_second * 3600.0


def plan_recipe_machine_for_target_output(
    recipe_name: str,
    machine_name: str,
    output_item: str,
    target_output_per_second: float,
) -> RecipeMachinePlan:
    if target_output_per_second <= 0:
        raise ValueError("target_output_per_second must be positive.")

    recipe = get_recipe(recipe_name)
    machine = get_machine(machine_name)
    single_rate = calculate_machine_recipe_rate(recipe, machine, machine_count=1)

    output_rate = single_rate.outputs.get(output_item)
    if output_rate is None:
        raise ValueError(f"Recipe {recipe_name} does not output {output_item}.")

    machine_count = ceil(target_output_per_second / output_rate.per_second)
    capacity_rate = calculate_machine_recipe_rate(recipe, machine, machine_count=machine_count)

    output_capacity = capacity_rate.outputs[output_item].per_second

    output_amount_per_craft = recipe.outputs[output_item]
    required_crafts_per_second = target_output_per_second / output_amount_per_craft
    required_inputs = {
        item: amount * required_crafts_per_second
        for item, amount in recipe.inputs.items()
    }

    return RecipeMachinePlan(
        recipe_name=recipe_name,
        machine_name=machine_name,
        machine_count=machine_count,
        target_output_item=output_item,
        target_output_per_second=target_output_per_second,
        capacity_output_per_second=output_capacity,
        required_inputs_per_second=required_inputs,
    )


def plan_transport_belt_from_raw_iron(target_transport_belt_per_hour: float) -> TransportBeltRawIronPlan:
    if target_transport_belt_per_hour <= 0:
        raise ValueError("target_transport_belt_per_hour must be positive.")

    target_belt_per_second = target_transport_belt_per_hour / 3600.0

    belt_plan = plan_recipe_machine_for_target_output(
        recipe_name="transport_belt",
        machine_name="assembling_machine_1",
        output_item="transport_belt",
        target_output_per_second=target_belt_per_second,
    )

    gear_required_per_second = belt_plan.required_inputs_per_second["iron_gear_wheel"]
    gear_plan = plan_recipe_machine_for_target_output(
        recipe_name="iron_gear_wheel",
        machine_name="assembling_machine_1",
        output_item="iron_gear_wheel",
        target_output_per_second=gear_required_per_second,
    )

    direct_iron_plate_per_second = belt_plan.required_inputs_per_second["iron_plate"]
    gear_iron_plate_per_second = gear_plan.required_inputs_per_second["iron_plate"]
    total_iron_plate_per_second = direct_iron_plate_per_second + gear_iron_plate_per_second

    furnace_plan = plan_recipe_machine_for_target_output(
        recipe_name="iron_plate",
        machine_name="stone_furnace",
        output_item="iron_plate",
        target_output_per_second=total_iron_plate_per_second,
    )

    iron_ore_miners = calculate_required_miners(
        resource_name="iron_ore",
        miner_name="electric_mining_drill",
        required_output_per_second=total_iron_plate_per_second,
    )

    return TransportBeltRawIronPlan(
        target_transport_belt_per_hour=target_transport_belt_per_hour,
        belt_plan=belt_plan,
        gear_plan=gear_plan,
        iron_plate_furnaces=furnace_plan.machine_count,
        iron_plate_required_per_second=total_iron_plate_per_second,
        iron_plate_capacity_per_second=furnace_plan.capacity_output_per_second,
        iron_ore_miners=iron_ore_miners,
    )


def format_transport_belt_raw_iron_plan(plan: TransportBeltRawIronPlan) -> str:
    lines = [
        f"Target: {plan.target_transport_belt_per_hour:.1f} transport_belt/hour",
        "Machines:",
        f"- transport belt assemblers: {plan.belt_plan.machine_count} "
        f"capacity={plan.belt_plan.capacity_output_per_hour:.1f}/hour",
        f"- iron gear assemblers: {plan.gear_plan.machine_count} "
        f"capacity={plan.gear_plan.capacity_output_per_hour:.1f}/hour",
        f"- stone furnaces for iron plate: {plan.iron_plate_furnaces} "
        f"capacity={plan.iron_plate_capacity_per_hour:.1f} iron_plate/hour",
        f"- electric iron ore miners: {plan.iron_ore_miners}",
        "Required flow:",
        f"- iron_plate total: {plan.iron_plate_required_per_second:.3f}/s, "
        f"{plan.iron_plate_required_per_hour:.1f}/hour",
        f"- direct iron_plate to belts: "
        f"{plan.belt_plan.required_inputs_per_second['iron_plate']:.3f}/s",
        f"- iron_gear_wheel to belts: "
        f"{plan.belt_plan.required_inputs_per_second['iron_gear_wheel']:.3f}/s",
        f"- iron_plate to gears: "
        f"{plan.gear_plan.required_inputs_per_second['iron_plate']:.3f}/s",
    ]
    return "\n".join(lines)
