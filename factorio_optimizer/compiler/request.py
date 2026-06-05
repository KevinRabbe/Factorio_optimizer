from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from factorio_optimizer.config.generation_config import Era, GenerationConfig, PowerMode
from factorio_optimizer.data.modules import ModuleConfig


LogisticsStrategy = Literal["central_smelting", "local_smelting", "outpost_smelting"]


@dataclass(frozen=True)
class OptimizationRequest:
    target_item: str
    target_rate_per_second: float
    era: Era = "mid"
    power_mode: PowerMode = "external"
    module_configs: list[ModuleConfig] = field(default_factory=list)
    use_electric_furnace: bool = False
    compare_furnace_modes: bool = False
    belt_name: str | None = None
    inserter_name: str | None = None
    logistics_strategy: LogisticsStrategy = "central_smelting"
    config: GenerationConfig = field(default_factory=GenerationConfig)

    @property
    def target_rate_per_minute(self) -> float:
        return self.target_rate_per_second * 60.0

    @property
    def target_rate_per_hour(self) -> float:
        return self.target_rate_per_second * 3600.0
