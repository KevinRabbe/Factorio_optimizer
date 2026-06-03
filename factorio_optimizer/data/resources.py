from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Resource:
    name: str
    output_item: str
    mining_time_seconds: float


RESOURCES: dict[str, Resource] = {
    "iron_ore": Resource(
        name="iron_ore",
        output_item="iron_ore",
        mining_time_seconds=1.0,
    ),
    "copper_ore": Resource(
        name="copper_ore",
        output_item="copper_ore",
        mining_time_seconds=1.0,
    ),
    "coal": Resource(
        name="coal",
        output_item="coal",
        mining_time_seconds=1.0,
    ),
    "stone": Resource(
        name="stone",
        output_item="stone",
        mining_time_seconds=1.0,
    ),
}


def get_resource(resource_name: str) -> Resource:
    try:
        return RESOURCES[resource_name]
    except KeyError as exc:
        raise ValueError(f"Unknown resource: {resource_name}") from exc
