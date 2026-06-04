from __future__ import annotations

from dataclasses import dataclass
from random import Random
from typing import Literal


Era = Literal["early", "mid", "end"]
PowerMode = Literal["external", "burner", "steam"]
MachinePreference = Literal["lowest_tier", "fastest_available"]
BeltPreference = Literal["transport_belt", "fast_transport_belt", "express_transport_belt"]


@dataclass(frozen=True)
class GenerationConfig:
    seed: int = 0
    era: Era = "early"
    power_mode: PowerMode = "external"
    machine_preference: MachinePreference = "lowest_tier"
    belt_preference: BeltPreference = "transport_belt"
    allow_randomness: bool = False

    def create_rng(self, salt: str = "") -> Random:
        seed_value = self.seed if not salt else _stable_seed(self.seed, salt)
        return Random(seed_value)


def _stable_seed(seed: int, salt: str) -> int:
    value = seed
    for char in salt:
        value = ((value * 31) + ord(char)) & 0xFFFFFFFF
    return value
