from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


EnergySource = Literal["electric", "burner", "none"]
MachineType = Literal["assembler", "furnace", "miner"]


@dataclass(frozen=True)
class Machine:
    name: str
    machine_type: MachineType
    crafting_speed: float = 0.0
    mining_speed: float = 0.0
    power_kw: float = 0.0
    energy_source: EnergySource = "electric"
    allowed_categories: tuple[str, ...] = ()


MACHINES: dict[str, Machine] = {
    "assembling_machine_1": Machine(
        name="assembling_machine_1",
        machine_type="assembler",
        crafting_speed=0.5,
        power_kw=75.0,
        energy_source="electric",
        allowed_categories=("crafting",),
    ),
    "stone_furnace": Machine(
        name="stone_furnace",
        machine_type="furnace",
        crafting_speed=1.0,
        power_kw=90.0,
        energy_source="burner",
        allowed_categories=("smelting",),
    ),
    "electric_mining_drill": Machine(
        name="electric_mining_drill",
        machine_type="miner",
        mining_speed=0.5,
        power_kw=90.0,
        energy_source="electric",
    ),
    "burner_mining_drill": Machine(
        name="burner_mining_drill",
        machine_type="miner",
        mining_speed=0.25,
        power_kw=150.0,
        energy_source="burner",
    ),
}


def get_machine(machine_name: str) -> Machine:
    try:
        return MACHINES[machine_name]
    except KeyError as exc:
        raise ValueError(f"Unknown machine: {machine_name}") from exc
