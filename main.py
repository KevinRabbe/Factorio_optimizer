from __future__ import annotations

from factorio_optimizer.export.blueprint_json_exporter import export_plan_to_blueprint_json
from factorio_optimizer.export.blueprint_string_encoder import encode_blueprint_string
from factorio_optimizer.mutation.iron_gear_mutations import generate_iron_gear_variants
from factorio_optimizer.planner.iron_gear_builder import build_iron_gear_plan
from factorio_optimizer.render.ascii_renderer import render_ascii
from factorio_optimizer.scoring.basic_fitness import score_plan
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


def main() -> None:
    base_plan = build_iron_gear_plan()
    variants = generate_iron_gear_variants(base_plan)

    scored_variants = sorted(
        variants,
        key=lambda plan: score_plan(plan).total,
        reverse=True,
    )

    print(f"Generated {len(scored_variants)} valid variants.")
    print()

    for variant in scored_variants:
        print_plan(variant)

    if not scored_variants:
        print("No valid variants to export.")
        return

    best_plan = scored_variants[0]
    blueprint_json = export_plan_to_blueprint_json(best_plan)
    blueprint_string = encode_blueprint_string(blueprint_json)

    print("=" * 40)
    print(f"Best plan: {best_plan.plan_id}")
    print("Blueprint string:")
    print(blueprint_string)


if __name__ == "__main__":
    main()
