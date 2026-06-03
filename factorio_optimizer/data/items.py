from __future__ import annotations

from dataclasses import dataclass, field


# Raw resources that the solver treats as leaves (no recipe needed)
RAW_RESOURCES: frozenset[str] = frozenset({
    "iron_ore",
    "copper_ore",
    "coal",
    "stone",
    "wood",
    "water",
    "crude_oil",
    # Fluid products from oil processing treated as raw for chain purposes
    "petroleum_gas",
    "heavy_oil",
    "light_oil",
    "lubricant",
})


@dataclass(frozen=True)
class ItemMeta:
    name: str
    display_name: str
    era: str            # "early", "mid", "end", "raw"
    category: str       # "science", "intermediate", "military", "logistics", "raw"
    icon: str           # emoji icon for the web UI


# ── Item catalog ────────────────────────────────────────────────────────────
ITEMS: dict[str, ItemMeta] = {
    # Raw resources
    "iron_ore":       ItemMeta("iron_ore",       "Iron Ore",       "raw",   "raw",          "🪨"),
    "copper_ore":     ItemMeta("copper_ore",      "Copper Ore",     "raw",   "raw",          "🟠"),
    "coal":           ItemMeta("coal",            "Coal",           "raw",   "raw",          "⬛"),
    "stone":          ItemMeta("stone",           "Stone",          "raw",   "raw",          "🪨"),
    "wood":           ItemMeta("wood",            "Wood",           "raw",   "raw",          "🪵"),
    "water":          ItemMeta("water",           "Water",          "raw",   "raw",          "💧"),
    "crude_oil":      ItemMeta("crude_oil",       "Crude Oil",      "raw",   "raw",          "🛢️"),
    "petroleum_gas":  ItemMeta("petroleum_gas",   "Petroleum Gas",  "raw",   "raw",          "💨"),
    "heavy_oil":      ItemMeta("heavy_oil",       "Heavy Oil",      "raw",   "raw",          "🫙"),
    "light_oil":      ItemMeta("light_oil",       "Light Oil",      "raw",   "raw",          "💛"),
    "lubricant":      ItemMeta("lubricant",       "Lubricant",      "mid",   "intermediate", "🟡"),

    # ── Early game intermediates ─────────────────────────────────────────
    "iron_plate":     ItemMeta("iron_plate",      "Iron Plate",     "early", "intermediate", "🔩"),
    "copper_plate":   ItemMeta("copper_plate",    "Copper Plate",   "early", "intermediate", "🟤"),
    "stone_brick":    ItemMeta("stone_brick",     "Stone Brick",    "early", "intermediate", "🧱"),
    "iron_gear_wheel":ItemMeta("iron_gear_wheel", "Iron Gear Wheel","early", "intermediate", "⚙️"),
    "copper_cable":   ItemMeta("copper_cable",    "Copper Cable",   "early", "intermediate", "🔌"),
    "electronic_circuit": ItemMeta("electronic_circuit", "Electronic Circuit", "early", "intermediate", "🟢"),
    "iron_stick":     ItemMeta("iron_stick",      "Iron Stick",     "early", "intermediate", "📏"),
    "pipe":           ItemMeta("pipe",            "Pipe",           "early", "logistics",    "🔧"),

    # ── Early game logistics / equipment ─────────────────────────────────
    "transport_belt": ItemMeta("transport_belt",  "Transport Belt", "early", "logistics",    "🟡"),
    "underground_belt":ItemMeta("underground_belt","Underground Belt","early","logistics",   "🔽"),
    "splitter":       ItemMeta("splitter",        "Splitter",       "early", "logistics",    "↔️"),
    "inserter":       ItemMeta("inserter",        "Inserter",       "early", "logistics",    "🦾"),
    "fast_inserter":  ItemMeta("fast_inserter",   "Fast Inserter",  "mid",   "logistics",    "⚡"),
    "small_electric_pole": ItemMeta("small_electric_pole", "Small Electric Pole", "early", "logistics", "🔋"),
    "medium_electric_pole": ItemMeta("medium_electric_pole", "Medium Electric Pole", "mid", "logistics", "🔋"),
    "stone_wall":     ItemMeta("stone_wall",      "Stone Wall",     "early", "military",     "🏰"),

    # ── Early game machines ──────────────────────────────────────────────
    "assembling_machine_1": ItemMeta("assembling_machine_1", "Assembling Machine 1", "early", "intermediate", "🏭"),
    "electric_mining_drill": ItemMeta("electric_mining_drill", "Electric Mining Drill", "early", "intermediate", "⛏️"),
    "lab":            ItemMeta("lab",             "Lab",            "early", "intermediate", "🔬"),

    # ── Early game science ───────────────────────────────────────────────
    "automation_science_pack": ItemMeta(
        "automation_science_pack", "Automation Science Pack", "early", "science", "🔴"
    ),
    "logistic_science_pack": ItemMeta(
        "logistic_science_pack", "Logistic Science Pack", "early", "science", "🟢"
    ),

    # ── Mid game intermediates ───────────────────────────────────────────
    "steel_plate":    ItemMeta("steel_plate",     "Steel Plate",    "mid",   "intermediate", "🔘"),
    "advanced_circuit": ItemMeta("advanced_circuit", "Advanced Circuit", "mid", "intermediate", "🔴"),
    "engine_unit":    ItemMeta("engine_unit",     "Engine Unit",    "mid",   "intermediate", "⚙️"),
    "electric_engine_unit": ItemMeta("electric_engine_unit", "Electric Engine Unit", "mid", "intermediate", "🔌"),
    "flying_robot_frame": ItemMeta("flying_robot_frame", "Flying Robot Frame", "mid", "intermediate", "🤖"),
    "battery":        ItemMeta("battery",         "Battery",        "mid",   "intermediate", "🔋"),
    "plastic_bar":    ItemMeta("plastic_bar",     "Plastic Bar",    "mid",   "intermediate", "⬜"),
    "sulfur":         ItemMeta("sulfur",          "Sulfur",         "mid",   "intermediate", "🟡"),
    "sulfuric_acid":  ItemMeta("sulfuric_acid",   "Sulfuric Acid",  "mid",   "intermediate", "🧪"),
    "low_density_structure": ItemMeta("low_density_structure", "Low Density Structure", "end", "intermediate", "🧩"),
    "rail":           ItemMeta("rail",            "Rail",           "mid",   "logistics",    "🛤️"),

    # ── Mid game military ────────────────────────────────────────────────
    "firearm_magazine": ItemMeta("firearm_magazine", "Firearm Magazine", "early", "military", "🔫"),
    "piercing_rounds_magazine": ItemMeta("piercing_rounds_magazine", "Piercing Rounds", "mid", "military", "💥"),
    "grenade":        ItemMeta("grenade",         "Grenade",        "mid",   "military",     "💣"),

    # ── Mid game machines ────────────────────────────────────────────────
    "assembling_machine_2": ItemMeta("assembling_machine_2", "Assembling Machine 2", "mid", "intermediate", "🏭"),

    # ── Mid game science ─────────────────────────────────────────────────
    "military_science_pack": ItemMeta(
        "military_science_pack", "Military Science Pack", "mid", "science", "⚫"
    ),
    "chemical_science_pack": ItemMeta(
        "chemical_science_pack", "Chemical Science Pack", "mid", "science", "🔵"
    ),

    # ── End game science ─────────────────────────────────────────────────
    "production_science_pack": ItemMeta(
        "production_science_pack", "Production Science Pack", "end", "science", "🟣"
    ),
    "utility_science_pack": ItemMeta(
        "utility_science_pack", "Utility Science Pack", "end", "science", "🟡"
    ),
}


def get_item(item_name: str) -> ItemMeta:
    return ITEMS.get(item_name, ItemMeta(item_name, item_name.replace("_", " ").title(), "early", "intermediate", "📦"))


def is_raw_resource(item_name: str) -> bool:
    return item_name in RAW_RESOURCES


def get_items_by_era(era: str) -> list[ItemMeta]:
    return [item for item in ITEMS.values() if item.era == era]


def get_optimizable_items() -> dict[str, list[dict]]:
    """Return items grouped by era, filtered to those with recipes (not raw resources)."""
    result: dict[str, list[dict]] = {"early": [], "mid": [], "end": []}
    for item in ITEMS.values():
        if item.era in result:
            result[item.era].append({
                "name": item.name,
                "display_name": item.display_name,
                "category": item.category,
                "icon": item.icon,
            })
    return result
