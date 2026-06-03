from __future__ import annotations

from dataclasses import dataclass

from factorio_optimizer.data.modules import GameModule, ModuleConfig, get_module, get_modules_for_era
from factorio_optimizer.rates.chain_solver import (
    ProductionChain,
    build_production_chain,
    chain_node_to_dict,
    collect_raw_inputs,
    total_energy_kw,
    total_machines,
)
from factorio_optimizer.rates.energy_planner import energy_plan_to_dict, plan_energy


@dataclass
class FactoryPlan:
    """A scored factory configuration."""
    name: str                   # human-readable label e.g. "Assembler 2 + Prod 1 ×2"
    era: str
    module_configs: list[ModuleConfig]
    use_electric_furnace: bool

    chain: ProductionChain
    score: float                # higher = better

    # Breakdown scores
    avg_uptime_pct: float       # weighted average uptime across all non-raw nodes
    energy_kw_per_output: float
    total_machines_count: int
    total_energy_kw: float


def _collect_uptimes(chain: ProductionChain) -> list[float]:
    """Walk the chain tree and collect uptime values for non-raw nodes."""
    results: list[float] = []

    def _walk(node):
        if not node.is_raw:
            results.append(node.uptime_pct)
        for c in node.children:
            _walk(c)

    _walk(chain.root)
    return results


def _score(
    avg_uptime: float,
    kw_per_output: float,
    machine_count: int,
    w_uptime: float = 0.60,
    w_energy: float = 0.30,
    w_count: float = 0.10,
) -> float:
    """
    Score a factory plan. Higher is better.
    Uptime is good (want it high), energy and machine count are costs.
    We normalise energy to a 0-100 scale (100 kW/output = score 0).
    """
    uptime_score = avg_uptime * 100.0 * w_uptime
    energy_score = max(0.0, 100.0 - kw_per_output) * w_energy
    count_score = max(0.0, 100.0 - machine_count) * w_count
    return round(uptime_score + energy_score + count_score, 2)


def optimize_factory(
    item: str,
    target_per_second: float,
    era: str = "mid",
    module_configs: list[ModuleConfig] | None = None,
    use_electric_furnace: bool = False,
) -> FactoryPlan:
    """
    Build and score one factory plan for the given configuration.
    """
    if module_configs is None:
        module_configs = []

    chain = build_production_chain(
        item=item,
        target_per_second=target_per_second,
        era=era,
        modules=module_configs,
        use_electric_furnace=use_electric_furnace,
    )

    uptimes = _collect_uptimes(chain)
    avg_uptime = sum(uptimes) / len(uptimes) if uptimes else 1.0
    machines = total_machines(chain.root)
    energy = total_energy_kw(chain.root)
    kw_per_out = energy / target_per_second if target_per_second > 0 else 0.0
    score = _score(avg_uptime, kw_per_out, machines)

    # Build a human-readable name for this configuration
    module_parts = []
    for cfg in module_configs:
        module_parts.append(f"{cfg.module.display_name} ×{cfg.count}")
    furnace_note = " (electric furnace)" if use_electric_furnace else ""
    era_label = {"early": "Early", "mid": "Mid", "end": "End"}[era]
    module_str = ", ".join(module_parts) if module_parts else "no modules"
    name = f"{era_label} game — {module_str}{furnace_note}"

    return FactoryPlan(
        name=name,
        era=era,
        module_configs=module_configs,
        use_electric_furnace=use_electric_furnace,
        chain=chain,
        score=score,
        avg_uptime_pct=round(avg_uptime * 100, 1),
        energy_kw_per_output=round(kw_per_out, 2),
        total_machines_count=machines,
        total_energy_kw=round(energy, 1),
    )


def compare_plans(
    item: str,
    target_per_second: float,
    era: str = "mid",
    user_modules: list[ModuleConfig] | None = None,
) -> list[FactoryPlan]:
    """
    Generate and rank the top factory configurations for the given item and era.
    Always includes the user's custom config as well as automatic alternatives.
    """
    from factorio_optimizer.data.modules import ModuleConfig as MC, get_module

    plans: list[FactoryPlan] = []

    # ── 1. No modules baseline ───────────────────────────────────────────
    for electric in ([False, True] if era in ("mid", "end") else [False]):
        plans.append(optimize_factory(item, target_per_second, era, [], electric))

    # ── 2. User-specified modules config ─────────────────────────────────
    if user_modules:
        plans.append(optimize_factory(item, target_per_second, era, user_modules, False))
        if era in ("mid", "end"):
            plans.append(optimize_factory(item, target_per_second, era, user_modules, True))

    # ── 3. Pre-set mid-game alternatives ─────────────────────────────────
    if era == "mid":
        speed1 = get_module("speed_module_1")
        prod1 = get_module("productivity_module_1")
        eff1 = get_module("efficiency_module_1")

        # Speed-focused (2× speed modules in assembler 2 = 2 slots)
        plans.append(optimize_factory(
            item, target_per_second, era,
            [MC(speed1, 2)], False,
        ))
        # Productivity-focused
        plans.append(optimize_factory(
            item, target_per_second, era,
            [MC(prod1, 2)], False,
        ))
        # Energy-saving
        plans.append(optimize_factory(
            item, target_per_second, era,
            [MC(eff1, 2)], True,
        ))
        # Mixed speed + prod
        plans.append(optimize_factory(
            item, target_per_second, era,
            [MC(speed1, 1), MC(prod1, 1)], False,
        ))

    # ── 4. Modular Setup (Using Saved Blueprints) ────────────────────────
    from factorio_optimizer.data.saved_layouts import get_all_layouts
    all_saved = get_all_layouts()
    saved_layouts = {}
    for l in all_saved:
        p_data = l.get("plan_data", {})
        item_name = p_data.get("chain", {}).get("item")
        if item_name:
            saved_layouts[item_name] = {
                "target_per_second": p_data.get("target_per_second", 1.0),
                "total_energy_kw": p_data.get("total_energy_kw", 0.0),
                "raw_inputs": p_data.get("raw_inputs", {}),
                "name": l.get("custom_name", "Saved Blueprint")
            }
    
    if saved_layouts:
        mod_chain = build_production_chain(
            item=item,
            target_per_second=target_per_second,
            era=era,
            modules=user_modules,
            use_electric_furnace=False,
            saved_layouts=saved_layouts
        )
        uptimes = _collect_uptimes(mod_chain)
        avg_uptime = sum(uptimes) / len(uptimes) if uptimes else 1.0
        machines = total_machines(mod_chain.root)
        energy = total_energy_kw(mod_chain.root)
        kw_per_out = energy / target_per_second if target_per_second > 0 else 0.0
        score = _score(avg_uptime, kw_per_out, machines)
        
        plans.append(FactoryPlan(
            name="📦 Modular Setup (Saved Layouts)",
            era=era,
            module_configs=user_modules or [],
            use_electric_furnace=False,
            chain=mod_chain,
            score=score,
            avg_uptime_pct=round(avg_uptime * 100, 1),
            energy_kw_per_output=round(kw_per_out, 2),
            total_machines_count=machines,
            total_energy_kw=round(energy, 1),
        ))

    # Deduplicate by name, rank by score
    seen: set[str] = set()
    unique: list[FactoryPlan] = []
    for p in plans:
        if p.name not in seen:
            seen.add(p.name)
            unique.append(p)

    return sorted(unique, key=lambda p: p.score, reverse=True)


def factory_plan_to_dict(plan: FactoryPlan) -> dict:
    """Serialise a FactoryPlan to JSON for the web API."""
    raw_inputs = collect_raw_inputs(plan.chain.root)
    energy_plan = plan_energy(plan.total_energy_kw, plan.chain.target_per_second)

    return {
        "name": plan.name,
        "era": plan.era,
        "score": plan.score,
        "avg_uptime_pct": plan.avg_uptime_pct,
        "energy_kw_per_output": plan.energy_kw_per_output,
        "total_machines": plan.total_machines_count,
        "total_energy_kw": plan.total_energy_kw,
        "target_per_second": round(plan.chain.target_per_second, 4),
        "target_per_minute": round(plan.chain.target_per_minute, 2),
        "chain": chain_node_to_dict(plan.chain.root),
        "raw_inputs": {k: round(v, 4) for k, v in raw_inputs.items()},
        "energy_plan": energy_plan_to_dict(energy_plan),
    }
