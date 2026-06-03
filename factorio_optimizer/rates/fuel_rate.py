from __future__ import annotations

from dataclasses import dataclass

from factorio_optimizer.data.fuels import Fuel, get_fuel
from factorio_optimizer.data.machines import Machine, get_machine
from factorio_optimizer.rates.mining_rate import calculate_mining_rate
from factorio_optimizer.data.resources import get_resource


@dataclass(frozen=True)
class FuelConsumptionRate:
    machine_name: str
    fuel_item: str
    machine_count: int
    fuel_per_second: float

    @property
    def fuel_per_minute(self) -> float:
        return self.fuel_per_second * 60.0

    @property
    def fuel_per_hour(self) -> float:
        return self.fuel_per_second * 3600.0


def calculate_fuel_consumption_rate(
    machine: Machine,
    fuel: Fuel,
    machine_count: int = 1,
    load_factor: float = 1.0,
) -> FuelConsumptionRate:
    if machine_count < 1:
        raise ValueError("machine_count must be at least 1.")
    if not 0.0 <= load_factor <= 1.0:
        raise ValueError("load_factor must be between 0.0 and 1.0.")

    power_mj_per_second = (machine.power_kw / 1000.0) * machine_count * load_factor
    fuel_per_second = power_mj_per_second / fuel.energy_mj

    return FuelConsumptionRate(
        machine_name=machine.name,
        fuel_item=fuel.item,
        machine_count=machine_count,
        fuel_per_second=fuel_per_second,
    )


def calculate_burner_coal_miner_net_output() -> tuple[float, float, float]:
    miner = get_machine("burner_mining_drill")
    coal = get_fuel("coal")
    gross = calculate_mining_rate(
        resource=get_resource("coal"),
        miner=miner,
        miner_count=1,
    )
    fuel_use = calculate_fuel_consumption_rate(
        machine=miner,
        fuel=coal,
        machine_count=1,
    )
    net = gross.output_per_second - fuel_use.fuel_per_second
    return gross.output_per_second, fuel_use.fuel_per_second, net
