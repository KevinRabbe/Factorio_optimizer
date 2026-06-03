from __future__ import annotations

from typing import Any

from factorio_optimizer.core.blueprint_plan import BlueprintPlan


FACTORIO_DIRECTIONS = {
    "north": 0,
    "east": 2,
    "south": 4,
    "west": 6,
}

ENTITY_NAMES = {
    "belt": "transport-belt",
    "inserter": "inserter",
    "assembler": "assembling-machine-1",
    "splitter": "splitter",
}

# Factorio 2.0+ blueprint version used as a placeholder for now.
# We can later make this configurable per target Factorio version.
DEFAULT_BLUEPRINT_VERSION = 562949954142208


def export_plan_to_blueprint_json(plan: BlueprintPlan) -> dict[str, Any]:
    entities: list[dict[str, Any]] = []
    entity_number = 1

    for obj in plan.objects:
        if obj.object_type in {"input_interface", "output_interface"}:
            continue

        entity_name = ENTITY_NAMES.get(obj.object_type)
        if entity_name is None:
            continue

        entity: dict[str, Any] = {
            "entity_number": entity_number,
            "name": entity_name,
            "position": {
                "x": obj.position.x,
                "y": obj.position.y,
            },
            "direction": FACTORIO_DIRECTIONS[obj.direction],
        }

        if obj.object_type == "assembler" and obj.recipe is not None:
            entity["recipe"] = obj.recipe

        entities.append(entity)
        entity_number += 1

    return {
        "blueprint": {
            "item": "blueprint",
            "label": plan.plan_id,
            "version": DEFAULT_BLUEPRINT_VERSION,
            "entities": entities,
        }
    }
