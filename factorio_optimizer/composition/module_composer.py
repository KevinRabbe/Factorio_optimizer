from __future__ import annotations

from dataclasses import dataclass, field

from factorio_optimizer.core.objects import Position
from factorio_optimizer.modules.module_base import FactoryModule


@dataclass(frozen=True)
class RecipeRequest:
    output_item: str
    amount_per_second: float = 1.0
    allow_internal_intermediates: bool = True


@dataclass
class CompositionPlan:
    plan_id: str
    requested_output: str
    modules: list[FactoryModule] = field(default_factory=list)

    def add_module(self, module: FactoryModule) -> None:
        self.modules.append(module)


class ModuleComposer:
    def __init__(self) -> None:
        self._module_factories: dict[str, callable] = {}

    def register_module_factory(self, output_item: str, factory: callable) -> None:
        self._module_factories[output_item] = factory

    def compose(self, request: RecipeRequest, origin: Position | None = None) -> CompositionPlan:
        origin = origin or Position(0, 0)
        plan = CompositionPlan(
            plan_id=f"compose_{request.output_item}",
            requested_output=request.output_item,
        )

        factory = self._module_factories.get(request.output_item)
        if factory is None:
            raise ValueError(f"No module factory registered for {request.output_item}.")

        plan.add_module(factory(origin=origin))
        return plan
