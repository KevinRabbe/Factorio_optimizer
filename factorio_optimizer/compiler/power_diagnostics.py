from __future__ import annotations

from dataclasses import dataclass
from math import ceil
from typing import Literal


PowerLevel = Literal["ok", "warning", "critical"]

# Vanilla-ish first-pass constants.
# One boiler consumes about 1.8 MW heat. Coal fuel value is 4 MJ.
COAL_MJ = 4.0
BOILER_HEAT_KW = 1800.0
BOILER_COAL_PER_SECOND_FULL_LOAD = BOILER_HEAT_KW / (COAL_MJ * 1000.0)

# Existing console reports used ~0.212/s net coal per burner coal miner.
BURNER_MINER_COAL_GROSS_PER_SECOND = 0.25
BURNER_MINER_SELF_FUEL_PER_SECOND = 0.0375
BURNER_MINER_COAL_NET_PER_SECOND = BURNER_MINER_COAL_GROSS_PER_SECOND - BURNER_MINER_SELF_FUEL_PER_SECOND


@dataclass(frozen=True)
class PowerDiagnostic:
    level: PowerLevel
    total_demand_kw: float
    total_demand_mw: float
    steam_engines: int
    boilers: int
    steam_capacity_kw: float
    headroom_pct: float
    coal_per_second: float
    coal_per_minute: float
    coal_per_hour: float
    burner_coal_miners_required: int
    recommendation: str

    def to_dict(self) -> dict:
        return {
            "level": self.level,
            "total_demand_kw": round(self.total_demand_kw, 2),
            "total_demand_mw": round(self.total_demand_mw, 4),
            "steam_engines": self.steam_engines,
            "boilers": self.boilers,
            "steam_capacity_kw": round(self.steam_capacity_kw, 2),
            "headroom_pct": round(self.headroom_pct, 2),
            "coal_per_second": round(self.coal_per_second, 4),
            "coal_per_minute": round(self.coal_per_minute, 2),
            "coal_per_hour": round(self.coal_per_hour, 1),
            "burner_coal_miners_required": self.burner_coal_miners_required,
            "recommendation": self.recommendation,
        }


def build_power_diagnostics(best_plan: dict) -> dict:
    energy_plan = best_plan.get("energy_plan") if best_plan else None
    if not energy_plan:
        return _empty_power_diagnostic().to_dict()

    total_demand_kw = float(energy_plan.get("total_demand_kw", 0.0) or 0.0)
    total_demand_mw = float(energy_plan.get("total_demand_mw", total_demand_kw / 1000.0) or 0.0)
    steam = energy_plan.get("steam", {}) or {}
    boilers = int(steam.get("boilers", 0) or 0)
    engines = int(steam.get("steam_engines", 0) or 0)
    capacity_kw = float(steam.get("capacity_kw", 0.0) or 0.0)
    headroom_pct = float(steam.get("headroom_pct", 0.0) or 0.0)

    coal_per_second = boilers * BOILER_COAL_PER_SECOND_FULL_LOAD
    coal_per_minute = coal_per_second * 60.0
    coal_per_hour = coal_per_second * 3600.0
    miners_required = ceil(coal_per_second / BURNER_MINER_COAL_NET_PER_SECOND) if coal_per_second > 0 else 0
    level = _power_level(total_demand_kw, headroom_pct)
    recommendation = _power_recommendation(
        total_demand_kw=total_demand_kw,
        engines=engines,
        boilers=boilers,
        coal_per_second=coal_per_second,
        miners_required=miners_required,
        headroom_pct=headroom_pct,
    )

    return PowerDiagnostic(
        level=level,
        total_demand_kw=total_demand_kw,
        total_demand_mw=total_demand_mw,
        steam_engines=engines,
        boilers=boilers,
        steam_capacity_kw=capacity_kw,
        headroom_pct=headroom_pct,
        coal_per_second=coal_per_second,
        coal_per_minute=coal_per_minute,
        coal_per_hour=coal_per_hour,
        burner_coal_miners_required=miners_required,
        recommendation=recommendation,
    ).to_dict()


def build_power_summary(power: dict) -> dict:
    return {
        "status": power.get("level", "ok"),
        "total_demand_kw": power.get("total_demand_kw", 0.0),
        "steam_engines": power.get("steam_engines", 0),
        "boilers": power.get("boilers", 0),
        "coal_per_second": power.get("coal_per_second", 0.0),
        "burner_coal_miners_required": power.get("burner_coal_miners_required", 0),
    }


def _empty_power_diagnostic() -> PowerDiagnostic:
    return PowerDiagnostic(
        level="ok",
        total_demand_kw=0.0,
        total_demand_mw=0.0,
        steam_engines=0,
        boilers=0,
        steam_capacity_kw=0.0,
        headroom_pct=0.0,
        coal_per_second=0.0,
        coal_per_minute=0.0,
        coal_per_hour=0.0,
        burner_coal_miners_required=0,
        recommendation="No power demand found for this plan.",
    )


def _power_level(total_demand_kw: float, headroom_pct: float) -> PowerLevel:
    if total_demand_kw <= 0:
        return "ok"
    if headroom_pct < 5.0:
        return "warning"
    return "ok"


def _power_recommendation(
    total_demand_kw: float,
    engines: int,
    boilers: int,
    coal_per_second: float,
    miners_required: int,
    headroom_pct: float,
) -> str:
    if total_demand_kw <= 0:
        return "No electric power required by this plan."

    base = (
        f"Build {engines} steam engine(s) and {boilers} boiler(s) for {total_demand_kw:.1f} kW demand. "
        f"At full load this burns about {coal_per_second:.3f} coal/s, requiring {miners_required} burner coal miner(s)."
    )
    if headroom_pct < 5.0:
        return base + " Headroom is low; add one extra steam engine/boiler block if you want safety margin."
    return base
