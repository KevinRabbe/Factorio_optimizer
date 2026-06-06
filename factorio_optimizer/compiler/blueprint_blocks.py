from __future__ import annotations

import base64
import json
import zlib
from dataclasses import dataclass
from typing import Any

from factorio_optimizer.core.blueprint_plan import BlueprintPlan
from factorio_optimizer.core.objects import Direction, FactoryObject, Position
from factorio_optimizer.data.entities import get_entity_spec
from factorio_optimizer.export.blueprint_json_exporter import export_plan_to_blueprint_json
from factorio_optimizer.export.blueprint_string_encoder import encode_blueprint_string
from factorio_optimizer.render.ascii_renderer import render_ascii
from factorio_optimizer.validation.blueprint_validator import (
    ValidationConfidence,
    validate_blueprint_confidence,
)


_DIRECTION_DELTAS: dict[Direction, tuple[int, int]] = {
    "north": (0, -1),
    "east": (1, 0),
    "south": (0, 1),
    "west": (-1, 0),
}


@dataclass(frozen=True)
class BlueprintArtifacts:
    validation: ValidationConfidence
    ascii: str
    blueprint_json: dict[str, Any]
    blueprint_string: str

    @property
    def valid(self) -> bool:
        return self.validation.passed

    @property
    def validation_errors(self) -> list[str]:
        return self.validation.errors


def belt(
    object_id: str,
    x: int,
    y: int,
    item: str,
    direction: Direction = "east",
    belt_name: str = "transport_belt",
    role: str = "transport",
) -> FactoryObject:
    return FactoryObject(
        object_id=object_id,
        object_type="belt",
        position=Position(x, y),
        direction=direction,
        item=item,
        role=role,
        entity_name=to_entity_name(belt_name),
    )


def belt_line(
    prefix: str,
    x: int,
    y: int,
    length: int,
    item: str,
    direction: Direction = "east",
    belt_name: str = "transport_belt",
) -> list[FactoryObject]:
    if length < 1:
        return []
    dx, dy = _DIRECTION_DELTAS[direction]
    return [
        belt(
            object_id=f"{prefix}_{index}",
            x=x + dx * index,
            y=y + dy * index,
            item=item,
            direction=direction,
            belt_name=belt_name,
        )
        for index in range(length)
    ]


def inserter(
    object_id: str,
    x: int,
    y: int,
    direction: Direction,
    item: str,
    role: str,
    inserter_name: str = "inserter",
) -> FactoryObject:
    return FactoryObject(
        object_id=object_id,
        object_type="inserter",
        position=Position(x, y),
        direction=direction,
        item=item,
        role=role,
        entity_name=to_entity_name(inserter_name),
    )


def assembler(
    object_id: str,
    x: int,
    y: int,
    recipe: str,
    machine_name: str,
    direction: Direction = "north",
) -> FactoryObject:
    entity_name = to_entity_name(machine_name)
    spec = get_entity_spec(entity_name)
    return FactoryObject(
        object_id=object_id,
        object_type="assembler",
        position=Position(x, y),
        direction=direction,
        width=spec.width,
        height=spec.height,
        recipe=recipe,
        role="producer",
        entity_name=entity_name,
    )


def assembler_row(
    prefix: str,
    x: int,
    y: int,
    count: int,
    recipe: str,
    machine_name: str,
    spacing: int = 5,
) -> list[FactoryObject]:
    return [
        assembler(
            object_id=f"{prefix}_{index}",
            x=x + index * spacing,
            y=y,
            recipe=recipe,
            machine_name=machine_name,
        )
        for index in range(count)
    ]


def furnace(
    object_id: str,
    x: int,
    y: int,
    recipe: str,
    machine_name: str,
    width: int = 2,
    height: int = 2,
    direction: Direction = "north",
) -> FactoryObject:
    entity_name = to_entity_name(machine_name)
    spec = get_entity_spec(entity_name)
    return FactoryObject(
        object_id=object_id,
        object_type="furnace",
        position=Position(x, y),
        direction=direction,
        width=width if width != 2 else spec.width,
        height=height if height != 2 else spec.height,
        recipe=recipe,
        role="producer",
        entity_name=entity_name,
    )


def furnace_row(
    prefix: str,
    x: int,
    y: int,
    count: int,
    recipe: str,
    machine_name: str,
    spacing: int = 4,
) -> list[FactoryObject]:
    return [
        furnace(
            object_id=f"{prefix}_{index}",
            x=x + index * spacing,
            y=y,
            recipe=recipe,
            machine_name=machine_name,
        )
        for index in range(count)
    ]


def miner(
    object_id: str,
    x: int,
    y: int,
    item: str,
    machine_name: str,
    direction: Direction = "east",
) -> FactoryObject:
    entity_name = to_entity_name(machine_name)
    spec = get_entity_spec(entity_name)
    return FactoryObject(
        object_id=object_id,
        object_type="miner",
        position=Position(x, y),
        direction=direction,
        width=spec.width,
        height=spec.height,
        item=item,
        role="ore_producer",
        entity_name=entity_name,
    )


def electric_pole(
    object_id: str,
    x: int,
    y: int,
    pole_name: str = "small_electric_pole",
) -> FactoryObject:
    return FactoryObject(
        object_id=object_id,
        object_type="electric_pole",
        position=Position(x, y),
        direction="north",
        role="power",
        entity_name=to_entity_name(pole_name),
    )


def chest(
    object_id: str,
    x: int,
    y: int,
    item: str | None = None,
    role: str = "buffer",
    chest_name: str = "iron_chest",
) -> FactoryObject:
    return FactoryObject(
        object_id=object_id,
        object_type="chest",
        position=Position(x, y),
        direction="north",
        item=item,
        role=role,
        entity_name=to_entity_name(chest_name),
    )


def power_row(
    prefix: str,
    x: int,
    y: int,
    count: int,
    spacing: int = 6,
    pole_name: str = "small_electric_pole",
) -> list[FactoryObject]:
    return [
        electric_pole(
            object_id=f"{prefix}_{index}",
            x=x + index * spacing,
            y=y,
            pole_name=pole_name,
        )
        for index in range(count)
    ]


def pipe(
    object_id: str,
    x: int,
    y: int,
    fluid: str,
    direction: Direction = "east",
    pipe_name: str = "pipe",
) -> FactoryObject:
    return FactoryObject(
        object_id=object_id,
        object_type="pipe",
        position=Position(x, y),
        direction=direction,
        item=fluid,
        role="fluid_transport",
        entity_name=to_entity_name(pipe_name),
    )


def pipe_line(
    prefix: str,
    x: int,
    y: int,
    length: int,
    fluid: str,
    direction: Direction = "east",
    pipe_name: str = "pipe",
) -> list[FactoryObject]:
    if length < 1:
        return []
    dx, dy = _DIRECTION_DELTAS[direction]
    return [
        pipe(
            object_id=f"{prefix}_{index}",
            x=x + dx * index,
            y=y + dy * index,
            fluid=fluid,
            direction=direction,
            pipe_name=pipe_name,
        )
        for index in range(length)
    ]


def chemical_plant(
    object_id: str,
    x: int,
    y: int,
    recipe: str,
    direction: Direction = "north",
) -> FactoryObject:
    spec = get_entity_spec("chemical-plant")
    return FactoryObject(
        object_id=object_id,
        object_type="chemical_plant",
        position=Position(x, y),
        direction=direction,
        width=spec.width,
        height=spec.height,
        recipe=recipe,
        role="producer",
        entity_name="chemical-plant",
    )


def refinery(
    object_id: str,
    x: int,
    y: int,
    recipe: str,
    direction: Direction = "north",
) -> FactoryObject:
    spec = get_entity_spec("oil-refinery")
    return FactoryObject(
        object_id=object_id,
        object_type="refinery",
        position=Position(x, y),
        direction=direction,
        width=spec.width,
        height=spec.height,
        recipe=recipe,
        role="producer",
        entity_name="oil-refinery",
    )


def lab(
    object_id: str,
    x: int,
    y: int,
    direction: Direction = "north",
) -> FactoryObject:
    spec = get_entity_spec("lab")
    return FactoryObject(
        object_id=object_id,
        object_type="lab",
        position=Position(x, y),
        direction=direction,
        width=spec.width,
        height=spec.height,
        role="science_consumer",
        entity_name="lab",
    )


def io_lane(
    object_id: str,
    x: int,
    y: int,
    item: str,
    role: str,
) -> FactoryObject:
    if role not in {"input_interface", "output_interface"}:
        raise ValueError("io_lane role must be input_interface or output_interface.")
    return FactoryObject(
        object_id=object_id,
        object_type=role,
        position=Position(x, y),
        direction="east",
        item=item,
        role=role,
    )


def compile_blueprint_artifacts(plan: BlueprintPlan) -> BlueprintArtifacts:
    validation = validate_blueprint_confidence(plan)
    blueprint_json = export_plan_to_blueprint_json(plan)
    return BlueprintArtifacts(
        validation=validation,
        ascii=render_ascii(plan),
        blueprint_json=blueprint_json,
        blueprint_string=encode_blueprint_string(blueprint_json),
    )


def build_entity_counts(plan: BlueprintPlan) -> dict[str, int]:
    counts: dict[str, int] = {}
    for obj in plan.objects:
        if obj.object_type in {"input_interface", "output_interface"}:
            continue
        entity_name = obj.entity_name or obj.object_type
        key = entity_name.replace("-", "_") + "s"
        counts[key] = counts.get(key, 0) + 1
    return counts


def decode_blueprint_string(blueprint_string: str) -> dict[str, Any]:
    if not blueprint_string.startswith("0"):
        raise ValueError("Blueprint string must start with version prefix '0'.")
    compressed = base64.b64decode(blueprint_string[1:])
    return json.loads(zlib.decompress(compressed).decode("utf-8"))


def to_entity_name(name: str) -> str:
    return name.replace("_", "-")
