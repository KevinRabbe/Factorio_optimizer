from __future__ import annotations

from dataclasses import dataclass
from math import ceil

from factorio_optimizer.data.fuels import get_fuel
from factorio_optimizer.data.power import get_power_producer
from factorio_optimizer.rates.fuel_rate import calculate_burner_coal_miner_net_output


@dataclass(frozen=True)
class StarterPowerEstimate:
    target_power_kw: float
    steam_engines: int
    produced_power_kw: float
    coal_per_second_at_full_load: float
    coal_miners_required: int

    @property
    def coal_per_minute_at_full_load(self) -> float:
        return self.coal_per_second_at_full_load * 60.0

    @property
    def coal_per_hour_at_full_load(self) -> float:
        return self.coal_per_second_at_full_load * 3600.0


def estimate_starter_steam_power(target_power_kw: float) -> StarterPowerEstimate:
    if target_power_kw < 0:
        raise ValueError("target_power_kw cannot be negative.")

    steam_engine = get_power_producer("steam_engine")
    coal = get_fuel("coal")
    steam_engines = max(1, ceil(target_power_kw / steam_engine.power_kw))
    produced_power_kw = steam_engines * steam_engine.power_kw

    # This intentionally estimates fuel use at produced capacity.
    # Later this can be replaced by boiler-specific heat and load logic.
    produced_mj_per_second = produced_power_kw / 1000.0
    coal_per_second = produced_mj_per_second / coal.energy_mj

    _gross, _fuel_use, net_coal_per_second = calculate_burner_coal_miner_net_output()
    coal_miners_required = max(1, ceil(coal_per_second / net_coal_per_second))

    return StarterPowerEstimate(
        target_power_kw=target_power_kw,
        steam_engines=steam_engines,
        produced_power_kw=produced_power_kw,
        coal_per_second_at_full_load=coal_per_second,
        coal_miners_required=coal_miners_required,
    )


def format_starter_power_estimate(estimate: StarterPowerEstimate) -> str:
    return "\n".join(
        [
            f"Target power: {estimate.target_power_kw:.1f} kW",
            f"Steam engines: {estimate.steam_engines}",
            f"Produced power: {estimate.produced_power_kw:.1f} kW",
            f"Coal use at full load: {estimate.coal_per_second_at_full_load:.3f}/s, "
            f"{estimate.coal_per_minute_at_full_load:.1f}/min, "
            f"{estimate.coal_per_hour_at_full_load:.1f}/hour",
            f"Burner coal miners required: {estimate.coal_miners_required}",
        ]
    )
