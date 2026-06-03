from __future__ import annotations

from factorio_optimizer.composition.composition_expander import expand_composition_to_blueprint_plan
from factorio_optimizer.composition.transport_belt_composition import build_transport_belt_composition_v1
from factorio_optimizer.data.machines import get_machine
from factorio_optimizer.data.resources import get_resource
from factorio_optimizer.expansion.module_expander import expand_module_to_blueprint_plan
from factorio_optimizer.expansion.module_graph_expander import expand_module_graph_to_blueprint_plan
from factorio_optimizer.export.blueprint_json_exporter import export_plan_to_blueprint_json
from factorio_optimizer.export.blueprint_string_encoder import encode_blueprint_string
from factorio_optimizer.modules.iron_gear_module import build_iron_gear_module
from factorio_optimizer.modules.transport_belt_module import build_transport_belt_module_v0
from factorio_optimizer.mutation.iron_gear_mutations import generate_iron_gear_variants
from factorio_optimizer.planner.iron_gear_builder import build_iron_gear_plan
from factorio_optimizer.rates.bottleneck_report import format_bottleneck_report
from factorio_optimizer.rates.efficiency_report import build_efficiency_report, format_efficiency_report
from factorio_optimizer.rates.fuel_rate import calculate_burner_coal_miner_net_output
from factorio_optimizer.rates.mining_rate import calculate_mining_rate, calculate_required_miners
from factorio_optimizer.rates.module_rate import build_module_rate_report
from factorio_optimizer.rates.rate_report import build_machine_rate_report
from factorio_optimizer.rates.repair_recommendations import format_repair_recommendations, recommend_repairs
from factorio_optimizer.rates.starter_power import estimate_starter_steam_power, format_starter_power_estimate
from factorio_optimizer.rates.throughput_checks import build_transport_belt_v0_throughput_report
from factorio_optimizer.render.ascii_renderer import render_ascii
from factorio_optimizer.scoring.basic_fitness import score_plan
from factorio_optimizer.validation.connection_validator import validate_modules_connections
from factorio_optimizer.validation.recipe_validator import RecipeValidationSpec, validate_recipe_plan
from factorio_optimizer.validation.static_validator import validate_plan


def print_plan(plan) -> None:
    validation = validate_plan(plan)
    fitness = score_plan(plan)

    print("=" * 40)
    print(f"Generated plan: {plan.plan_id}")
    print(f"Grid: {plan.width}x{plan.height}")
    print(f"Fitness: {fitness.total}")
    print(
        "Breakdown: "
        f"valid={fitness.valid_bonus}, "
        f"entities=-{fitness.entity_penalty}, "
        f"belts=-{fitness.belt_penalty}, "
        f"area=-{fitness.area_penalty}, "
        f"flow=-{fitness.flow_penalty}"
    )
    print()

    print("ASCII:")
    print(render_ascii(plan))

    print()
    print("Validation:")
    if validation.passed:
        print("PASS")
    else:
        print("FAIL")
        for error in validation.errors:
            print(f"- {error}")


def print_recipe_plan(plan, spec: RecipeValidationSpec) -> None:
    validation = validate_recipe_plan(plan, spec)
    fitness = score_plan(plan)

    print("=" * 40)
    print(f"Generated plan: {plan.plan_id}")
    print(f"Grid: {plan.width}x{plan.height}")
    print(f"Recipe: {spec.recipe}")
    print(f"Fitness: {fitness.total}")
    print()

    print("ASCII:")
    print(render_ascii(plan))

    print()
    print("Recipe validation:")
    if validation.passed:
        print("PASS")
    else:
        print("FAIL")
        for error in validation.errors:
            print(f"- {error}")


def print_connection_validation(composition) -> None:
    result = validate_modules_connections(composition.modules)
    print()
    print("Connection validation:")
    if result.passed:
        print("PASS")
    else:
        print("FAIL")
        for error in result.errors:
            print(f"- {error}")


def print_best_blueprint(plan) -> None:
    blueprint_json = export_plan_to_blueprint_json(plan)
    blueprint_string = encode_blueprint_string(blueprint_json)

    print("=" * 40)
    print(f"Best plan: {plan.plan_id}")
    print("Blueprint string:")
    print(blueprint_string)


def run_legacy_object_flow_pipeline() -> None:
    base_plan = build_iron_gear_plan()
    variants = generate_iron_gear_variants(base_plan)

    scored_variants = sorted(
        variants,
        key=lambda plan: score_plan(plan).total,
        reverse=True,
    )

    print("# Legacy object-flow pipeline")
    print(f"Generated {len(scored_variants)} valid variants.")
    print()

    for variant in scored_variants:
        print_plan(variant)

    if scored_variants:
        print_best_blueprint(scored_variants[0])
    else:
        print("No valid legacy variants to export.")


def run_module_pipeline() -> None:
    print()
    print("# Segment/module pipeline")

    module = build_iron_gear_module()
    plan = expand_module_to_blueprint_plan(
        module=module,
        plan_id="iron_gear_module_expanded",
        width=9,
        height=7,
    )

    print_plan(plan)

    if validate_plan(plan).passed:
        print_best_blueprint(plan)
    else:
        print("Module-expanded plan is not valid yet.")


def run_transport_belt_module_pipeline() -> None:
    print()
    print("# Transport belt module pipeline")

    module = build_transport_belt_module_v0()
    plan = expand_module_graph_to_blueprint_plan(
        module=module,
        plan_id="transport_belt_module_v0_expanded",
        width=9,
        height=6,
    )
    spec = RecipeValidationSpec(
        recipe="transport_belt",
        input_items=("iron_plate", "iron_gear_wheel"),
        output_item="transport_belt",
    )

    print_recipe_plan(plan, spec)

    if validate_recipe_plan(plan, spec).passed:
        print_best_blueprint(plan)
    else:
        print("Transport belt module plan is not valid yet.")


def run_transport_belt_composition_pipeline() -> None:
    print()
    print("# Transport belt composed module pipeline")

    composition = build_transport_belt_composition_v1()
    plan = expand_composition_to_blueprint_plan(
        composition=composition,
        plan_id="transport_belt_composition_v1_expanded",
        width=12,
        height=11,
    )
    spec = RecipeValidationSpec(
        recipe="transport_belt",
        input_items=("iron_plate",),
        output_item="transport_belt",
    )

    print_recipe_plan(plan, spec)
    print_connection_validation(composition)

    if validate_recipe_plan(plan, spec).passed:
        print_best_blueprint(plan)
    else:
        print("Transport belt composition plan is not valid yet.")


def run_rate_reports() -> None:
    print()
    print("# Theoretical machine rate reports")
    print("=" * 40)
    print(build_machine_rate_report("iron_gear_wheel", "assembling_machine_1"))
    print()
    print("=" * 40)
    print(build_machine_rate_report("transport_belt", "assembling_machine_1"))
    print()
    print("=" * 40)
    print(build_machine_rate_report("iron_plate", "stone_furnace"))


def run_module_rate_reports() -> None:
    print()
    print("# Theoretical module rate reports")
    print("=" * 40)
    print(build_module_rate_report(build_iron_gear_module()))
    print()
    print("=" * 40)
    print(build_module_rate_report(build_transport_belt_module_v0()))


def run_efficiency_reports() -> None:
    print()
    print("# Mock efficiency reports")
    print("=" * 40)
    print(
        format_efficiency_report(
            build_efficiency_report(
                item="transport_belt",
                theoretical_per_hour=7200.0,
                actual_per_hour=7200.0,
            )
        )
    )
    print()
    print("=" * 40)
    print(
        format_efficiency_report(
            build_efficiency_report(
                item="transport_belt",
                theoretical_per_hour=7200.0,
                actual_per_hour=5400.0,
            )
        )
    )


def run_bottleneck_reports() -> None:
    print()
    print("# Throughput bottleneck reports")
    print("=" * 40)
    report = build_transport_belt_v0_throughput_report()
    print(format_bottleneck_report(report))
    print()
    print(format_repair_recommendations(recommend_repairs(report)))


def run_raw_resource_reports() -> None:
    print()
    print("# Raw resource and starter power reports")

    electric_iron = calculate_mining_rate(
        resource=get_resource("iron_ore"),
        miner=get_machine("electric_mining_drill"),
    )
    burner_coal = calculate_mining_rate(
        resource=get_resource("coal"),
        miner=get_machine("burner_mining_drill"),
    )
    gross, fuel_use, net = calculate_burner_coal_miner_net_output()

    print("=" * 40)
    print(
        f"Electric miner iron ore: {electric_iron.output_per_second:.3f}/s, "
        f"{electric_iron.output_per_minute:.1f}/min, "
        f"{electric_iron.output_per_hour:.1f}/hour"
    )
    print(
        f"Burner miner coal gross: {burner_coal.output_per_second:.3f}/s, "
        f"{burner_coal.output_per_minute:.1f}/min, "
        f"{burner_coal.output_per_hour:.1f}/hour"
    )
    print(
        f"Burner coal miner fuel use: {fuel_use:.3f}/s, "
        f"net coal: {net:.3f}/s"
    )
    print(
        "Electric iron miners needed for 2 iron_ore/s: "
        f"{calculate_required_miners('iron_ore', 'electric_mining_drill', 2.0)}"
    )

    print()
    print("=" * 40)
    print(format_starter_power_estimate(estimate_starter_steam_power(150.0)))


def main() -> None:
    run_legacy_object_flow_pipeline()
    run_module_pipeline()
    run_transport_belt_module_pipeline()
    run_transport_belt_composition_pipeline()
    run_rate_reports()
    run_module_rate_reports()
    run_efficiency_reports()
    run_bottleneck_reports()
    run_raw_resource_reports()


if __name__ == "__main__":
    main()
