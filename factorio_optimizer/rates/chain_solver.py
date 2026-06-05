from __future__ import annotations

from dataclasses import dataclass
from math import ceil

from factorio_optimizer.core.errors import DomainError
from factorio_optimizer.data.items import is_raw_resource
from factorio_optimizer.data.machines import Machine, get_machine
from factorio_optimizer.data.modules import ModuleConfig, compute_module_effects
from factorio_optimizer.data.recipes import has_recipe


@dataclass
class ChainNode:
    item: str
    display_name: str
    icon: str
    machine_name: str
    machine_display_name: str
    recipe_name: str
    target_per_second: float
    machine_count_exact: float
    machine_count_ceil: int
    uptime_pct: float
    output_per_second: float
    capacity_per_second: float
    base_power_kw: float
    effective_power_kw: float
    speed_bonus: float
    productivity_bonus: float
    energy_bonus: float
    is_raw: bool
    is_blackbox: bool
    blackbox_raw_inputs: dict[str, float]
    children: list["ChainNode"]


@dataclass
class ProductionChain:
    root: ChainNode
    target_item: str
    target_per_second: float
    target_per_minute: float
    total_machines: int
    total_energy_kw: float
    efficiency_kw_per_output: float


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


_RECIPE_CATEGORY_OVERRIDES: dict[str, str] = {
    # Crafted in assemblers. The ingredient sulfuric_acid is a fluid, but the recipe category is not chemistry.
    "chemical_science_pack": "crafting-with-fluid",
}


def _recipe_category(recipe_name: str, recipe_category: str) -> str:
    return _RECIPE_CATEGORY_OVERRIDES.get(recipe_name, recipe_category)


def _pick_machine(category: str, era: str, use_electric_furnace: bool = False) -> str:
    tier_map = _CATEGORY_TO_MACHINE.get(category)
    if tier_map is None:
        raise ValueError(f"No machine tier map registered for recipe category {category!r}.")
    if category == "smelting" and use_electric_furnace and era in ("mid", "end"):
        return tier_map.get("mid_electric", "stone_furnace")
    if era not in tier_map:
        raise ValueError(f"No machine registered for category {category!r} in era {era!r}.")
    return tier_map[era]


def _get_valid_machine(machine_name: str, category: str, recipe_name: str) -> Machine:
    machine = get_machine(machine_name)
    if category not in machine.allowed_categories:
        raise ValueError(
            f"Machine {machine.name!r} cannot craft recipe {recipe_name!r} "
            f"with category {category!r}. Allowed categories: {machine.allowed_categories}."
        )
    return machine


def _compute_single_machine_rate(
    recipe_name: str,
    machine: Machine,
    modules: list[ModuleConfig],
) -> tuple[float, float, float, float, float, float]:
    from factorio_optimizer.data.recipes import get_recipe

    recipe = get_recipe(recipe_name)
    speed_b, prod_b, energy_b = compute_module_effects(modules, machine.machine_type)
    effective_speed = machine.crafting_speed * (1.0 + speed_b)
    effective_power = machine.power_kw * (1.0 + energy_b)
    crafts_per_second = effective_speed / recipe.crafting_time_seconds

    if recipe_name not in recipe.outputs:
        if len(recipe.outputs) != 1:
            raise NotImplementedError(
                f"Recipe {recipe_name!r} has multiple outputs and cannot be solved as item {recipe_name!r} yet."
            )
        output_amount = next(iter(recipe.outputs.values()))
    else:
        output_amount = recipe.outputs[recipe_name]

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
    from factorio_optimizer.data.items import get_item
    from factorio_optimizer.data.recipes import get_recipe

    modules = modules or []
    _visited = _visited or set()
    saved_layouts = saved_layouts or {}
    if target_per_second <= 0:
        raise DomainError("target_per_second must be greater than zero.")
    item_meta = get_item(item)

    if item in saved_layouts and item not in _visited:
        layout = saved_layouts[item]
        output_per_second_each = layout.get("target_per_second", 1.0)
        base_power_each = layout.get("total_energy_kw", 0.0)
        machine_count_exact = target_per_second / output_per_second_each if output_per_second_each else 0.0
        machine_count_ceil = max(1, ceil(machine_count_exact))
        uptime_pct = machine_count_exact / machine_count_ceil if machine_count_ceil > 0 else 1.0
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

    if item in _visited:
        cycle = " -> ".join([*_visited, item])
        raise DomainError(f"Recipe dependency cycle detected: {cycle}.")

    if is_raw_resource(item):
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

    if not has_recipe(item):
        raise DomainError(f"Item {item!r} is not raw and has no known recipe.")

    _visited = _visited | {item}
    recipe = get_recipe(item)
    category = _recipe_category(item, recipe.category)
    machine_name = _pick_machine(category, era, use_electric_furnace)
    machine = _get_valid_machine(machine_name, category, item)

    applicable_modules = [
        cfg for cfg in modules
        if machine.machine_type in cfg.module.allowed_machine_types
    ]
    total_slots_used = sum(cfg.count for cfg in applicable_modules)
    if total_slots_used > machine.module_slots:
        clamped: list[ModuleConfig] = []
        slots_remaining = machine.module_slots
        for cfg in applicable_modules:
            use = min(cfg.count, slots_remaining)
            if use > 0:
                from factorio_optimizer.data.modules import ModuleConfig as MC
                clamped.append(MC(module=cfg.module, count=use))
            slots_remaining -= use
        applicable_modules = clamped

    output_per_second_each, speed_b, prod_b, energy_b, _eff_speed, effective_power_each = _compute_single_machine_rate(
        item,
        machine,
        applicable_modules,
    )

    machine_count_exact = target_per_second / output_per_second_each
    machine_count_ceil = max(1, ceil(machine_count_exact))
    uptime_pct = machine_count_exact / machine_count_ceil
    capacity_per_second = output_per_second_each * machine_count_ceil
    base_power = machine.power_kw * machine_count_ceil
    effective_power = effective_power_each * machine_count_ceil

    output_amount = recipe.outputs[item]
    crafts_per_second_needed = target_per_second / (output_amount * (1.0 + prod_b))

    children: list[ChainNode] = []
    for ingredient, amount_per_craft in recipe.inputs.items():
        child = solve_chain(
            item=ingredient,
            target_per_second=amount_per_craft * crafts_per_second_needed,
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


def total_machines(node: ChainNode) -> int:
    if node.is_raw:
        return 0
    return node.machine_count_ceil + sum(total_machines(c) for c in node.children)


def total_energy_kw(node: ChainNode) -> float:
    if node.is_raw:
        return 0.0
    return node.effective_power_kw + sum(total_energy_kw(c) for c in node.children)


def collect_raw_inputs(node: ChainNode) -> dict[str, float]:
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
