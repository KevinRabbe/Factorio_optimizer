from __future__ import annotations

from factorio_optimizer.compiler.request import OptimizationRequest
from factorio_optimizer.compiler.result import OptimizationReport
from factorio_optimizer.optimizer.factory_optimizer import compare_plans, factory_plan_to_dict


def compile_optimization_request(request: OptimizationRequest) -> OptimizationReport:
    plans = compare_plans(
        item=request.target_item,
        target_per_second=request.target_rate_per_second,
        era=request.era,
        user_modules=request.module_configs if request.module_configs else None,
    )
    plan_dicts = [factory_plan_to_dict(plan) for plan in plans]
    best_plan = plan_dicts[0] if plan_dicts else {}

    summary = _build_summary(best_plan=best_plan, plan_count=len(plan_dicts))
    diagnostics = {
        "compiler": "simple_compiler",
        "report_schema_version": 1,
        "deterministic_seed": request.config.seed,
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


def _build_summary(best_plan: dict, plan_count: int) -> dict:
    if not best_plan:
        return {
            "plan_count": plan_count,
            "avg_uptime_pct": 0.0,
            "total_machines": 0,
            "total_energy_kw": 0.0,
            "efficiency_score": 0.0,
        }

    return {
        "plan_count": plan_count,
        "avg_uptime_pct": best_plan.get("avg_uptime_pct", 0.0),
        "total_machines": best_plan.get("total_machines", 0),
        "total_energy_kw": best_plan.get("total_energy_kw", 0.0),
        "efficiency_score": best_plan.get("score", 0.0),
        "raw_inputs": best_plan.get("raw_inputs", {}),
        "energy_plan": best_plan.get("energy_plan", {}),
    }
