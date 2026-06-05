from __future__ import annotations

from factorio_optimizer.core.blueprint_plan import BlueprintPlan


def render_ascii(plan: BlueprintPlan) -> str:
    grid = [["." for _ in range(plan.width)] for _ in range(plan.height)]

    for obj in plan.objects:
        symbol = _symbol_for_object(obj.object_type, obj.role)

        for tile in obj.occupied_tiles():
            if 0 <= tile.x < plan.width and 0 <= tile.y < plan.height:
                grid[tile.y][tile.x] = symbol

    return "\n".join(" ".join(row) for row in grid)


def _symbol_for_object(object_type: str, role: str | None) -> str:
    if object_type == "input_interface":
        return "I"

    if object_type == "output_interface":
        return "O"

    if object_type == "assembler":
        return "A"

    if object_type == "furnace":
        return "F"

    if object_type == "inserter":
        if role == "ingredient_transfer":
            return "i"
        if role == "product_transfer":
            return "o"
        return "x"

    if object_type == "belt":
        return ">"

    if object_type == "splitter":
        return "S"

    if object_type == "electric_pole":
        return "P"

    if object_type == "pipe":
        return "|"

    if object_type == "chemical_plant":
        return "C"

    if object_type == "refinery":
        return "R"

    if object_type == "lab":
        return "L"

    return "?"
