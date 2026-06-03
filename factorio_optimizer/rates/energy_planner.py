from __future__ import annotations

from dataclasses import dataclass
from math import ceil


# ── Power constants (vanilla Factorio) ──────────────────────────────────────

# Steam setup
BOILER_POWER_KW = 1800.0          # 1 boiler produces 1.8 MW of heat
STEAM_ENGINE_POWER_KW = 900.0     # 1 steam engine outputs 900 kW
BOILERS_PER_ENGINE = 0.5          # 1 boiler feeds exactly 2 engines

# Solar setup
SOLAR_PANEL_KW = 60.0             # average output including night = 42 kW effective
SOLAR_PANEL_EFFECTIVE_KW = 42.0   # ~70% average accounting for night/dusk/dawn
ACCUMULATOR_CAPACITY_MJ = 5.0     # 5 MJ per accumulator
ACCUMULATOR_CHARGE_KW = 300.0     # max charge/discharge rate

# The canonical Factorio solar ratio for continuous factory power:
# ~23.8 solar panels + 21.4 accumulators per 1 MW  (1 engine = 900 kW)
# Simplified: 0.84 solar panels / kW effective, 0.75 accumulators / kW
SOLAR_PANELS_PER_KW = 1.0 / SOLAR_PANEL_EFFECTIVE_KW   # panels per kW demand
ACCUMULATORS_PER_KW = 0.75                               # accumulators per kW demand


@dataclass
class SteamPowerPlan:
    total_demand_kw: float
    boilers: int
    steam_engines: int
    steam_capacity_kw: float
    headroom_pct: float             # extra capacity above demand


@dataclass
class SolarPowerPlan:
    total_demand_kw: float
    solar_panels: int
    accumulators: int
    solar_capacity_kw: float        # at peak (daytime)
    accumulator_stored_mj: float


@dataclass
class EnergyPlan:
    total_demand_kw: float
    total_demand_mw: float
    steam: SteamPowerPlan
    solar: SolarPowerPlan
    kw_per_output: float            # energy efficiency metric


def plan_steam(demand_kw: float) -> SteamPowerPlan:
    """Calculate boilers + steam engines needed to satisfy demand."""
    engines_needed = ceil(demand_kw / STEAM_ENGINE_POWER_KW)
    boilers_needed = ceil(engines_needed * BOILERS_PER_ENGINE)
    capacity_kw = engines_needed * STEAM_ENGINE_POWER_KW
    headroom = (capacity_kw - demand_kw) / demand_kw * 100.0 if demand_kw > 0 else 0.0
    return SteamPowerPlan(
        total_demand_kw=demand_kw,
        boilers=boilers_needed,
        steam_engines=engines_needed,
        steam_capacity_kw=capacity_kw,
        headroom_pct=round(headroom, 1),
    )


def plan_solar(demand_kw: float) -> SolarPowerPlan:
    """Calculate solar panels + accumulators needed for 24h continuous power."""
    panels = ceil(demand_kw * SOLAR_PANELS_PER_KW)
    accumulators = ceil(demand_kw * ACCUMULATORS_PER_KW)
    peak_capacity = panels * SOLAR_PANEL_KW
    stored_mj = accumulators * ACCUMULATOR_CAPACITY_MJ
    return SolarPowerPlan(
        total_demand_kw=demand_kw,
        solar_panels=panels,
        accumulators=accumulators,
        solar_capacity_kw=peak_capacity,
        accumulator_stored_mj=stored_mj,
    )


def plan_energy(total_demand_kw: float, target_per_second: float) -> EnergyPlan:
    """Build a full energy plan for a given power demand."""
    steam = plan_steam(total_demand_kw)
    solar = plan_solar(total_demand_kw)
    kw_per_output = total_demand_kw / target_per_second if target_per_second > 0 else 0.0
    return EnergyPlan(
        total_demand_kw=round(total_demand_kw, 1),
        total_demand_mw=round(total_demand_kw / 1000.0, 3),
        steam=steam,
        solar=solar,
        kw_per_output=round(kw_per_output, 2),
    )


def energy_plan_to_dict(ep: EnergyPlan) -> dict:
    return {
        "total_demand_kw": ep.total_demand_kw,
        "total_demand_mw": ep.total_demand_mw,
        "kw_per_output": ep.kw_per_output,
        "steam": {
            "boilers": ep.steam.boilers,
            "steam_engines": ep.steam.steam_engines,
            "capacity_kw": round(ep.steam.steam_capacity_kw, 1),
            "headroom_pct": ep.steam.headroom_pct,
        },
        "solar": {
            "solar_panels": ep.solar.solar_panels,
            "accumulators": ep.solar.accumulators,
            "peak_capacity_kw": round(ep.solar.solar_capacity_kw, 1),
            "stored_mj": round(ep.solar.accumulator_stored_mj, 1),
        },
    }
