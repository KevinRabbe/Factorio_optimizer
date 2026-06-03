from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class GameModule:
    """Represents a Factorio module that can be inserted into machines."""

    name: str
    display_name: str
    era: str                   # "mid" or "end"
    tier: int                  # 1, 2, or 3
    module_type: str           # "speed", "productivity", "efficiency"
    speed_bonus: float         # fraction, e.g. +0.2 = +20% crafting speed
    productivity_bonus: float  # fraction, e.g. +0.04 = +4% output
    energy_bonus: float        # fraction, e.g. +0.5 = +50% power draw
    # productivity modules cannot be used in chemical plants, mining drills, etc.
    allowed_machine_types: tuple[str, ...]


# Machine types that allow productivity modules (vanilla Factorio rules)
_PROD_ALLOWED = ("assembler", "furnace", "chemical_plant", "refinery")
_ALL_TYPES = ("assembler", "furnace", "chemical_plant", "refinery", "miner")


MODULES: dict[str, GameModule] = {
    # ── Speed modules ──────────────────────────────────────────────────────
    "speed_module_1": GameModule(
        name="speed_module_1",
        display_name="Speed Module 1",
        era="mid",
        tier=1,
        module_type="speed",
        speed_bonus=0.20,
        productivity_bonus=0.0,
        energy_bonus=0.50,
        allowed_machine_types=_ALL_TYPES,
    ),
    "speed_module_2": GameModule(
        name="speed_module_2",
        display_name="Speed Module 2",
        era="mid",
        tier=2,
        module_type="speed",
        speed_bonus=0.30,
        productivity_bonus=0.0,
        energy_bonus=0.60,
        allowed_machine_types=_ALL_TYPES,
    ),
    "speed_module_3": GameModule(
        name="speed_module_3",
        display_name="Speed Module 3",
        era="end",
        tier=3,
        module_type="speed",
        speed_bonus=0.50,
        productivity_bonus=0.0,
        energy_bonus=0.70,
        allowed_machine_types=_ALL_TYPES,
    ),
    # ── Productivity modules ───────────────────────────────────────────────
    "productivity_module_1": GameModule(
        name="productivity_module_1",
        display_name="Productivity Module 1",
        era="mid",
        tier=1,
        module_type="productivity",
        speed_bonus=-0.05,
        productivity_bonus=0.04,
        energy_bonus=0.40,
        allowed_machine_types=_PROD_ALLOWED,
    ),
    "productivity_module_2": GameModule(
        name="productivity_module_2",
        display_name="Productivity Module 2",
        era="mid",
        tier=2,
        module_type="productivity",
        speed_bonus=-0.10,
        productivity_bonus=0.06,
        energy_bonus=0.60,
        allowed_machine_types=_PROD_ALLOWED,
    ),
    "productivity_module_3": GameModule(
        name="productivity_module_3",
        display_name="Productivity Module 3",
        era="end",
        tier=3,
        module_type="productivity",
        speed_bonus=-0.15,
        productivity_bonus=0.10,
        energy_bonus=0.80,
        allowed_machine_types=_PROD_ALLOWED,
    ),
    # ── Efficiency modules ─────────────────────────────────────────────────
    "efficiency_module_1": GameModule(
        name="efficiency_module_1",
        display_name="Efficiency Module 1",
        era="mid",
        tier=1,
        module_type="efficiency",
        speed_bonus=0.0,
        productivity_bonus=0.0,
        energy_bonus=-0.30,
        allowed_machine_types=_ALL_TYPES,
    ),
    "efficiency_module_2": GameModule(
        name="efficiency_module_2",
        display_name="Efficiency Module 2",
        era="mid",
        tier=2,
        module_type="efficiency",
        speed_bonus=0.0,
        productivity_bonus=0.0,
        energy_bonus=-0.40,
        allowed_machine_types=_ALL_TYPES,
    ),
    "efficiency_module_3": GameModule(
        name="efficiency_module_3",
        display_name="Efficiency Module 3",
        era="end",
        tier=3,
        module_type="efficiency",
        speed_bonus=0.0,
        productivity_bonus=0.0,
        energy_bonus=-0.50,
        allowed_machine_types=_ALL_TYPES,
    ),
}


@dataclass(frozen=True)
class ModuleConfig:
    """A module inserted into a machine slot (module + quantity)."""
    module: GameModule
    count: int


def get_module(module_name: str) -> GameModule:
    try:
        return MODULES[module_name]
    except KeyError as exc:
        raise ValueError(f"Unknown module: {module_name!r}") from exc


def get_modules_for_era(era: str) -> list[GameModule]:
    """Return modules unlocked at or before the given era."""
    order = ["early", "mid", "end"]
    cutoff = order.index(era)
    return [m for m in MODULES.values() if order.index(m.era) <= cutoff]


def compute_module_effects(
    configs: list[ModuleConfig],
    machine_type: str,
) -> tuple[float, float, float]:
    """
    Return (total_speed_bonus, total_productivity_bonus, total_energy_bonus)
    as additive fractions, filtering out modules not allowed for this machine type.
    Energy bonus is clamped so power never drops below 20% of base.
    """
    speed = 0.0
    prod = 0.0
    energy = 0.0
    for cfg in configs:
        if machine_type in cfg.module.allowed_machine_types:
            speed += cfg.module.speed_bonus * cfg.count
            prod += cfg.module.productivity_bonus * cfg.count
            energy += cfg.module.energy_bonus * cfg.count

    # Minimum power floor: -80% (energy bonus cannot go below -0.8)
    energy = max(energy, -0.80)
    return speed, prod, energy
