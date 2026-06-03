from __future__ import annotations

from dataclasses import dataclass
from math import ceil

from factorio_optimizer.data.items import is_raw_resource
from factorio_optimizer.data.machines import Machine, get_best_machine_for_category, get_machine
from factorio_optimizer.data.modules import ModuleConfig, compute_module_effects
from factorio_optimizer.data.recipes import RECIPES, has_recipe


# ── Data structures ──────────────────────────────────────────────────────────

@dataclass
class ChainNode:
    """One production step in the resolved factory chain."""
    item: str
    display_name: str
    icon: str
    machine_name: str
    machine_display_name: str
    recipe_name: str

    # Rate math
    target_per_second: float        # what the parent chain demands
    machine_count_exact: float      # exact machines needed (e.g. 2.4)
    machine_count_ceil: int         # ceil → actual machines placed (e.g. 3)
    uptime_pct: float               # exact / ceil (e.g. 0.80 = 80%)
    output_per_second: float        # capacity output (at ceil machines)
    capacity_per_second: float      # same as output_per_second

    # Energy
    base_power_kw: float            # machine base power × ceil
    effective_power_kw: float       # after module energy bonus

    # Module effects applied
    speed_bonus: float
    productivity_bonus: float
    energy_bonus: float

    # Flags
    is_raw: bool                    # True if this is a raw resource leaf
    is_blackbox: bool               # True if this is a modular saved layout
    blackbox_raw_inputs: dict[str, float] # Pre-calculated raw inputs for blackbox
    children: list[ChainNode]       # ingredient sub-chains


@dataclass
class ProductionChain:
    root: ChainNode
    target_item: str
    target_per_second: float
    target_per_minute: float
    total_machines: int
    total_energy_kw: float
    efficiency_kw_per_output: float  # kW per item/s


# ── Solver ───────────────────────────────────────────────────────────────────

# Default machine tiers for each recipe category
_CATEGORY_TO_MACHINE: dict[str, dict[str, str]] = {
    "smelting": {
        "early": "stone_furnace",
        "mid": "steel_furnace",
        "mid_electric": "electric_furnace",
        "end": "electric_furnace",
    },
    "crafting": {
        "early": "assembling_machine_1",
        "mid": "assembling_machine_2",
        "end": "assembling_machine_3",
    },
    "crafting-with-fluid": {
        "early": "assembling_machine_2",
        "mid": "assembling_machine_2",
        "end": "assembling_machine_3",
    },
    "chemistry": {
        "early": "chemical_plant",
        "mid": "chemical_plant",
        "end": "chemical_plant",
    },
    "oil_processing": {
        "early": "oil_refinery",
        "mid": "oil_refinery",
        "end": "oil_refinery",
    },
}


def _pick_machine(category: str, era: str, use_electric_furnace: bool = False) -> str:
    tier_map = _CATEGORY_TO_MACHINE.get(category, {})
    if category == "smelting" and use_electric_furnace and era in ("mid", "end"):
        return tier_map.get("mid_electric", "stone_furnace")
    return tier_map.get(era, tier_map.get("early", "assembling_machine_1"))


def _compute_single_machine_rate(
    recipe_name: str,
    machine: Machine,
    modules: list[ModuleConfig],
) -> tuple[float, float, float, float, float, float]:
    """
    Return (output_per_second_per_machine, speed_bonus, productivity_bonus,
            energy_bonus, effective_speed, effective_power_kw_per_machine).
    """
    from factorio_optimizer.data.recipes import get_recipe
    recipe = get_recipe(recipe_name)

    speed_b, prod_b, energy_b = compute_module_effects(modules, machine.machine_type)
    effective_speed = machine.crafting_speed * (1.0 + speed_b)
    effective_power = machine.power_kw * (1.0 + energy_b)

    # crafts per second
    crafts_per_second = effective_speed / recipe.crafting_time_seconds

    # output per second per machine (considering multi-output + productivity)
    output_item = list(recipe.outputs.keys())[0]  # primary output
    output_amount = recipe.outputs[output_item]
    output_per_second = crafts_per_second * output_amount * (1.0 + prod_b)

    return output_per_second, speed_b, prod_b, energy_b, effective_speed, effective_power


def solve_chain(
    item: str,
    target_per_second: float,
    era: str = "mid",
    modules: list[ModuleConfig] | None = None,
    use_electric_furnace: bool = False,
    saved_layouts: dict[str, dict] | None = None,
    _visited: set[str] | None = None,
) -> ChainNode:
    """
    Recursively solve the production chain for `item` at `target_per_second`.
    """
    from factorio_optimizer.data.items import get_item, ITEMS
    from factorio_optimizer.data.recipes import get_recipe

    if modules is None:
        modules = []
    if _visited is None:
        _visited = set()
    if saved_layouts is None:
        saved_layouts = {}

    item_meta = get_item(item)

    # ── Modular Blackbox leaf ────────────────────────────────────────────
    if item in saved_layouts and item not in _visited:
        layout = saved_layouts[item]
        output_per_second_each = layout.get("target_per_second", 1.0)
        base_power_each = layout.get("total_energy_kw", 0.0)
        
        machine_count_exact = target_per_second / output_per_second_each if output_per_second_each else 0.0
        machine_count_ceil = max(1, ceil(machine_count_exact))
        uptime_pct = machine_count_exact / machine_count_ceil if machine_count_ceil > 0 else 1.0
        
        # Scale the raw inputs from the saved layout
        raw_inputs_each = layout.get("raw_inputs", {})
        scaled_raw_inputs = {k: v * machine_count_exact for k, v in raw_inputs_each.items()}

        return ChainNode(
            item=item,
            display_name=item_meta.display_name,
            icon=item_meta.icon,
            machine_name="saved_layout",
            machine_display_name="Saved Blueprint",
            recipe_name=layout.get("name", "Saved Blueprint"),
            target_per_second=target_per_second,
            machine_count_exact=machine_count_exact,
            machine_count_ceil=machine_count_ceil,
            uptime_pct=uptime_pct,
            output_per_second=output_per_second_each * machine_count_ceil,
            capacity_per_second=output_per_second_each * machine_count_ceil,
            base_power_kw=base_power_each * machine_count_ceil,
            effective_power_kw=base_power_each * machine_count_ceil,
            speed_bonus=0.0,
            productivity_bonus=0.0,
            energy_bonus=0.0,
            is_raw=False,
            is_blackbox=True,
            blackbox_raw_inputs=scaled_raw_inputs,
            children=[],
        )

    # ── Raw resource leaf ────────────────────────────────────────────────
    if is_raw_resource(item) or not has_recipe(item) or item in _visited:
        return ChainNode(
            item=item,
            display_name=item_meta.display_name,
            icon=item_meta.icon,
            machine_name="",
            machine_display_name="",
            recipe_name="",
            target_per_second=target_per_second,
            machine_count_exact=0.0,
            machine_count_ceil=0,
            uptime_pct=1.0,
            output_per_second=target_per_second,
            capacity_per_second=target_per_second,
            base_power_kw=0.0,
            effective_power_kw=0.0,
            speed_bonus=0.0,
            productivity_bonus=0.0,
            energy_bonus=0.0,
            is_raw=True,
            is_blackbox=False,
            blackbox_raw_inputs={},
            children=[],
        )

    # ── Find recipe and machine ──────────────────────────────────────────
    _visited = _visited | {item}

    recipe = get_recipe(item)
    machine_name = _pick_machine(recipe.category, era, use_electric_furnace)
    try:
        machine = get_machine(machine_name)
    except ValueError:
        machine_name = "assembling_machine_1"
        machine = get_machine(machine_name)

    # Filter modules: only those allowed for this machine type
    applicable_modules = [
        cfg for cfg in modules
        if machine.machine_type in cfg.module.allowed_machine_types
        and cfg.count <= machine.module_slots
    ]
    # Clamp total module count to available slots
    total_slots_used = sum(cfg.count for cfg in applicable_modules)
    if total_slots_used > machine.module_slots:
        # Reduce last entry to fit
        clamped: list[ModuleConfig] = []
        slots_remaining = machine.module_slots
        for cfg in applicable_modules:
            use = min(cfg.count, slots_remaining)
            if use > 0:
                from factorio_optimizer.data.modules import ModuleConfig as MC
                clamped.append(MC(module=cfg.module, count=use))
            slots_remaining -= use
        applicable_modules = clamped

    (
        output_per_second_each,
        speed_b, prod_b, energy_b,
        _eff_speed, effective_power_each,
    ) = _compute_single_machine_rate(item, machine, applicable_modules)

    # Number of machines needed
    machine_count_exact = target_per_second / output_per_second_each
    machine_count_ceil = max(1, ceil(machine_count_exact))
    uptime_pct = machine_count_exact / machine_count_ceil

    capacity_per_second = output_per_second_each * machine_count_ceil
    base_power = machine.power_kw * machine_count_ceil
    effective_power = effective_power_each * machine_count_ceil

    # ── Resolve ingredient sub-chains ────────────────────────────────────
    # We need to produce `target_per_second` of `item`.
    # How many crafts/second does that require?
    output_amount = recipe.outputs[item]
    # With productivity, each craft yields output_amount × (1 + prod_b)
    crafts_per_second_needed = target_per_second / (output_amount * (1.0 + prod_b))

    children: list[ChainNode] = []
    for ingredient, amount_per_craft in recipe.inputs.items():
        ingredient_rate = amount_per_craft * crafts_per_second_needed
        child = solve_chain(
            item=ingredient,
            target_per_second=ingredient_rate,
            era=era,
            modules=modules,
            use_electric_furnace=use_electric_furnace,
            saved_layouts=saved_layouts,
            _visited=_visited,
        )
        children.append(child)

    return ChainNode(
        item=item,
        display_name=item_meta.display_name,
        icon=item_meta.icon,
        machine_name=machine_name,
        machine_display_name=machine.display_name,
        recipe_name=item,
        target_per_second=target_per_second,
        machine_count_exact=machine_count_exact,
        machine_count_ceil=machine_count_ceil,
        uptime_pct=uptime_pct,
        output_per_second=capacity_per_second,
        capacity_per_second=capacity_per_second,
        base_power_kw=base_power,
        effective_power_kw=effective_power,
        speed_bonus=speed_b,
        productivity_bonus=prod_b,
        energy_bonus=energy_b,
        is_raw=False,
        is_blackbox=False,
        blackbox_raw_inputs={},
        children=children,
    )


# ── Aggregation helpers ───────────────────────────────────────────────────────

def total_machines(node: ChainNode) -> int:
    if node.is_raw:
        return 0
    # For a blackbox, it's treated as 1 "blueprint" machine conceptually, 
    # but practically we might want to return 0 or the machine_count_ceil. 
    # Let's count it as `machine_count_ceil` modular setups.
    return node.machine_count_ceil + sum(total_machines(c) for c in node.children)


def total_energy_kw(node: ChainNode) -> float:
    if node.is_raw:
        return 0.0
    return node.effective_power_kw + sum(total_energy_kw(c) for c in node.children)


def collect_raw_inputs(node: ChainNode) -> dict[str, float]:
    """Collect all raw resource requirements (items/second) from the chain."""
    result: dict[str, float] = {}
    if node.is_raw:
        result[node.item] = result.get(node.item, 0.0) + node.target_per_second
    if node.is_blackbox:
        for k, v in node.blackbox_raw_inputs.items():
            result[k] = result.get(k, 0.0) + v
    for child in node.children:
        for k, v in collect_raw_inputs(child).items():
            result[k] = result.get(k, 0.0) + v
    return result


def build_production_chain(
    item: str,
    target_per_second: float,
    era: str = "mid",
    modules: list[ModuleConfig] | None = None,
    use_electric_furnace: bool = False,
    saved_layouts: dict[str, dict] | None = None,
) -> ProductionChain:
    root = solve_chain(
        item=item,
        target_per_second=target_per_second,
        era=era,
        modules=modules,
        use_electric_furnace=use_electric_furnace,
        saved_layouts=saved_layouts,
    )
    machines = total_machines(root)
    energy = total_energy_kw(root)
    eff = energy / target_per_second if target_per_second > 0 else 0.0

    return ProductionChain(
        root=root,
        target_item=item,
        target_per_second=target_per_second,
        target_per_minute=target_per_second * 60.0,
        total_machines=machines,
        total_energy_kw=energy,
        efficiency_kw_per_output=eff,
    )


def chain_node_to_dict(node: ChainNode) -> dict:
    """Serialize a ChainNode to a JSON-safe dict for the web API."""
    return {
        "item": node.item,
        "display_name": node.display_name,
        "icon": node.icon,
        "machine_name": node.machine_name,
        "machine_display_name": node.machine_display_name,
        "target_per_second": round(node.target_per_second, 4),
        "target_per_minute": round(node.target_per_second * 60, 2),
        "machine_count_exact": round(node.machine_count_exact, 3),
        "machine_count_ceil": node.machine_count_ceil,
        "uptime_pct": round(node.uptime_pct * 100, 1),
        "capacity_per_second": round(node.capacity_per_second, 4),
        "base_power_kw": round(node.base_power_kw, 2),
        "effective_power_kw": round(node.effective_power_kw, 2),
        "speed_bonus_pct": round(node.speed_bonus * 100, 1),
        "productivity_bonus_pct": round(node.productivity_bonus * 100, 1),
        "energy_bonus_pct": round(node.energy_bonus * 100, 1),
        "is_raw": node.is_raw,
        "is_blackbox": node.is_blackbox,
        "children": [chain_node_to_dict(c) for c in node.children],
    }
