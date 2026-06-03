from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


EnergySource = Literal["electric", "burner", "none"]
MachineType = Literal["assembler", "furnace", "miner", "chemical_plant", "refinery"]


@dataclass(frozen=True)
class Machine:
    name: str
    machine_type: MachineType
    crafting_speed: float = 0.0
    mining_speed: float = 0.0
    power_kw: float = 0.0
    energy_source: EnergySource = "electric"
    allowed_categories: tuple[str, ...] = ()
    module_slots: int = 0
    era: str = "early"
    display_name: str = ""

    def __post_init__(self) -> None:
        if not self.display_name:
            object.__setattr__(self, "display_name", self.name.replace("_", " ").title())


MACHINES: dict[str, Machine] = {
    "assembling_machine_1": Machine(
        name="assembling_machine_1",
        display_name="Assembling Machine 1",
        machine_type="assembler",
        crafting_speed=0.5,
        power_kw=75.0,
        energy_source="electric",
        allowed_categories=("crafting",),
        module_slots=0,
        era="early",
    ),
    "assembling_machine_2": Machine(
        name="assembling_machine_2",
        display_name="Assembling Machine 2",
        machine_type="assembler",
        crafting_speed=0.75,
        power_kw=150.0,
        energy_source="electric",
        allowed_categories=("crafting", "crafting-with-fluid"),
        module_slots=2,
        era="mid",
    ),
    "assembling_machine_3": Machine(
        name="assembling_machine_3",
        display_name="Assembling Machine 3",
        machine_type="assembler",
        crafting_speed=1.25,
        power_kw=375.0,
        energy_source="electric",
        allowed_categories=("crafting", "crafting-with-fluid"),
        module_slots=4,
        era="end",
    ),
    "stone_furnace": Machine(
        name="stone_furnace",
        display_name="Stone Furnace",
        machine_type="furnace",
        crafting_speed=1.0,
        power_kw=90.0,
        energy_source="burner",
        allowed_categories=("smelting",),
        module_slots=0,
        era="early",
    ),
    "steel_furnace": Machine(
        name="steel_furnace",
        display_name="Steel Furnace",
        machine_type="furnace",
        crafting_speed=2.0,
        power_kw=90.0,
        energy_source="burner",
        allowed_categories=("smelting",),
        module_slots=0,
        era="mid",
    ),
    "electric_furnace": Machine(
        name="electric_furnace",
        display_name="Electric Furnace",
        machine_type="furnace",
        crafting_speed=2.0,
        power_kw=180.0,
        energy_source="electric",
        allowed_categories=("smelting",),
        module_slots=2,
        era="mid",
    ),
    "burner_mining_drill": Machine(
        name="burner_mining_drill",
        display_name="Burner Mining Drill",
        machine_type="miner",
        mining_speed=0.25,
        power_kw=150.0,
        energy_source="burner",
        era="early",
    ),
    "electric_mining_drill": Machine(
        name="electric_mining_drill",
        display_name="Electric Mining Drill",
        machine_type="miner",
        mining_speed=0.5,
        power_kw=90.0,
        energy_source="electric",
        module_slots=3,
        era="early",
    ),
    "chemical_plant": Machine(
        name="chemical_plant",
        display_name="Chemical Plant",
        machine_type="chemical_plant",
        crafting_speed=1.25,
        power_kw=210.0,
        energy_source="electric",
        allowed_categories=("chemistry",),
        module_slots=3,
        era="mid",
    ),
    "oil_refinery": Machine(
        name="oil_refinery",
        display_name="Oil Refinery",
        machine_type="refinery",
        crafting_speed=1.0,
        power_kw=420.0,
        energy_source="electric",
        allowed_categories=("oil_processing",),
        module_slots=3,
        era="mid",
    ),
}


def get_machine(machine_name: str) -> Machine:
    try:
        return MACHINES[machine_name]
    except KeyError as exc:
        raise ValueError(f"Unknown machine: {machine_name!r}") from exc


def get_machines_for_era(era: str) -> list[Machine]:
    order = ["early", "mid", "end"]
    cutoff = order.index(era)
    return [m for m in MACHINES.values() if order.index(m.era) <= cutoff]


def get_best_machine_for_category(category: str, era: str) -> Machine | None:
    era_order = ["early", "mid", "end"]
    cutoff = era_order.index(era)
    candidates = [
        m for m in MACHINES.values()
        if category in m.allowed_categories and era_order.index(m.era) <= cutoff
    ]
    if not candidates:
        return None
    return max(candidates, key=lambda m: m.crafting_speed)
