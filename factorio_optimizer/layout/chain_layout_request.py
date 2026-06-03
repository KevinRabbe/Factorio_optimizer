from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class LayoutModuleRequest:
    item: str
    recipe_name: str
    machine_name: str
    machine_count: int
    target_per_second: float
    capacity_per_second: float


@dataclass(frozen=True)
class LayoutExternalInput:
    item: str
    required_per_second: float


@dataclass(frozen=True)
class LayoutExternalOutput:
    item: str
    target_per_second: float


@dataclass(frozen=True)
class ChainLayoutRequest:
    target_item: str
    target_per_second: float
    modules: tuple[LayoutModuleRequest, ...] = field(default_factory=tuple)
    external_inputs: tuple[LayoutExternalInput, ...] = field(default_factory=tuple)
    external_outputs: tuple[LayoutExternalOutput, ...] = field(default_factory=tuple)


def format_chain_layout_request(request: ChainLayoutRequest) -> str:
    lines = [
        f"Layout request for {request.target_item}: {request.target_per_second:.3f}/s",
        "Modules:",
    ]

    if request.modules:
        for module in request.modules:
            lines.append(
                f"- {module.item}: {module.machine_count}x {module.machine_name} "
                f"target={module.target_per_second:.3f}/s "
                f"capacity={module.capacity_per_second:.3f}/s"
            )
    else:
        lines.append("- none")

    lines.append("External inputs:")
    if request.external_inputs:
        for input_item in request.external_inputs:
            lines.append(f"- {input_item.item}: {input_item.required_per_second:.3f}/s")
    else:
        lines.append("- none")

    lines.append("External outputs:")
    if request.external_outputs:
        for output_item in request.external_outputs:
            lines.append(f"- {output_item.item}: {output_item.target_per_second:.3f}/s")
    else:
        lines.append("- none")

    return "\n".join(lines)
