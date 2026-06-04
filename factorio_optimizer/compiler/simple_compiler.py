from __future__ import annotations

from factorio_optimizer.compiler.bottleneck_diagnostics import (
    build_bottleneck_diagnostics,
    build_bottleneck_summary,
)
from factorio_optimizer.compiler.power_diagnostics import (
    build_power_diagnostics,
    build_power_summary,
)
from factorio_optimizer.compiler.request import OptimizationRequest
from factorio_optimizer.compiler.result import OptimizationReport
from factorio_optimizer.compiler.transport_diagnostics import (
    build_transport_diagnostics,
    build_transport_summary,
)
from factorio_optimizer.optimizer.factory_optimizer import compare_plans, factory_plan_to_dict


def compile_optimization_request(request: OptimizationRequest) -> OptimizationReport:
    plans = compare_plans(
        item=request.target_item,
        target_per_second=request.target_rate_per_second,
        era=request.era,
        user_modules=request.module_configs if request.module_configs else None,
        use_electric_furnace=request.use_electric_furnace,
        compare_furnace_modes=request.compare_furnace_modes,
    )
    plan_dicts = [factory_plan_to_dict(plan) for plan in plans]
    best_plan = plan_dicts[0] if plan_dicts else {}

    bottlenecks = build_bottleneck_diagnostics(best_plan)
    bottleneck_summary = build_bottleneck_summary(bottlenecks)
    transport = build_transport_diagnostics(
        best_plan,
        request.era,
        belt_name=request.belt_name,
        inserter_name=request.inserter_name,
    )
    transport_summary = build_transport_summary(transport)
    power = build_power_diagnostics(best_plan)
    power_summary = build_power_summary(power)
    summary = _build_summary(
        best_plan=best_plan,
        plan_count=len(plan_dicts),
        bottleneck_summary=bottleneck_summary,
        transport_summary=transport_summary,
        power_summary=power_summary,
    )
    diagnostics = {
        "compiler": "simple_compiler",
        "report_schema_version": 6,
        "deterministic_seed": request.config.seed,
        "use_electric_furnace": request.use_electric_furnace,
        "compare_furnace_modes": request.compare_furnace_modes,
        "belt_name": request.belt_name,
        "inserter_name": request.inserter_name,
        "bottlenecks": bottlenecks,
        "bottleneck_summary": bottleneck_summary,
        "transport": transport,
        "transport_summary": transport_summary,
        "power": power,
        "power_summary": power_summary,
    }

    return OptimizationReport(
        target_item=request.target_item,
        target_rate_per_second=request.target_rate_per_second,
        target_rate_per_minute=request.target_rate_per_minute,
        target_rate_per_hour=request.target_rate_per_hour,
        era=request.era,
        power_mode=request.power_mode,
        best_plan=best_plan,
        plans=plan_dicts,
        summary=summary,
        diagnostics=diagnostics,
    )


def _build_summary(
    best_plan: dict,
    plan_count: int,
    bottleneck_summary: dict | None = None,
    transport_summary: dict | None = None,
    power_summary: dict | None = None,
) -> dict:
    if not best_plan:
        return {
            "plan_count": plan_count,
            "avg_uptime_pct": 0.0,
            "total_machines": 0,
            "total_energy_kw": 0.0,
            "efficiency_score": 0.0,
            "bottleneck_summary": bottleneck_summary or {},
            "transport_summary": transport_summary or {},
            "power_summary": power_summary or {},
        }

    return {
        "plan_count": plan_count,
        "avg_uptime_pct": best_plan.get("avg_uptime_pct", 0.0),
        "total_machines": best_plan.get("total_machines", 0),
        "total_energy_kw": best_plan.get("total_energy_kw", 0.0),
        "efficiency_score": best_plan.get("score", 0.0),
        "raw_inputs": best_plan.get("raw_inputs", {}),
        "energy_plan": best_plan.get("energy_plan", {}),
        "bottleneck_summary": bottleneck_summary or {},
        "transport_summary": transport_summary or {},
        "power_summary": power_summary or {},
    }
