from __future__ import annotations

from dataclasses import dataclass
from math import ceil

from factorio_optimizer.data.machines import Machine, get_machine
from factorio_optimizer.data.resources import Resource, get_resource


@dataclass(frozen=True)
class MiningRate:
    resource_name: str
    miner_name: str
    miner_count: int
    output_item: str
    output_per_second: float

    @property
    def output_per_minute(self) -> float:
        return self.output_per_second * 60.0

    @property
    def output_per_hour(self) -> float:
        return self.output_per_second * 3600.0


def calculate_mining_rate(
    resource: Resource,
    miner: Machine,
    miner_count: int = 1,
) -> MiningRate:
    if miner.machine_type != "miner":
        raise ValueError(f"Machine {miner.name} is not a miner.")
    if miner_count < 1:
        raise ValueError("miner_count must be at least 1.")

    output_per_second = (miner.mining_speed / resource.mining_time_seconds) * miner_count

    return MiningRate(
        resource_name=resource.name,
        miner_name=miner.name,
        miner_count=miner_count,
        output_item=resource.output_item,
        output_per_second=output_per_second,
    )


def calculate_required_miners(
    resource_name: str,
    miner_name: str,
    required_output_per_second: float,
) -> int:
    if required_output_per_second <= 0:
        return 0

    single_miner_rate = calculate_mining_rate(
        resource=get_resource(resource_name),
        miner=get_machine(miner_name),
        miner_count=1,
    )
    return ceil(required_output_per_second / single_miner_rate.output_per_second)
