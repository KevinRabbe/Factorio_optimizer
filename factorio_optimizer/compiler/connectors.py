from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, TypedDict


ConnectorKind = Literal[
    "belt_input",
    "belt_output",
    "fluid_input",
    "fluid_output",
    "power_input",
    "train_input",
    "train_output",
    "bus_input_tap",
    "bus_output_return",
    "manual_input",
    "chest_output",
]


class ConnectorDict(TypedDict, total=False):
    id: str
    kind: str
    item: str
    side: str
    direction: str
    rate_per_second: float
    rate_per_minute: float
    belt_tier: str
    lane_count: int
    required: bool
    description: str
    connects_to: list[str]


@dataclass(frozen=True)
class Connector:
    id: str
    kind: ConnectorKind
    item: str
    side: str
    direction: str
    rate_per_second: float = 0.0
    belt_tier: str = "transport_belt"
    lane_count: int = 1
    required: bool = True
    description: str = ""
    connects_to: tuple[str, ...] = ()

    def to_dict(self) -> ConnectorDict:
        return {
            "id": self.id,
            "kind": self.kind,
            "item": self.item,
            "side": self.side,
            "direction": self.direction,
            "rate_per_second": round(self.rate_per_second, 6),
            "rate_per_minute": round(self.rate_per_second * 60.0, 4),
            "belt_tier": self.belt_tier,
            "lane_count": self.lane_count,
            "required": self.required,
            "description": self.description,
            "connects_to": list(self.connects_to),
        }


def belt_input(
    connector_id: str,
    item: str,
    *,
    side: str = "left",
    direction: str = "east",
    rate_per_second: float = 0.0,
    belt_tier: str = "transport_belt",
    lane_count: int = 1,
    description: str = "",
    connects_to: tuple[str, ...] = (),
) -> ConnectorDict:
    return Connector(
        id=connector_id,
        kind="belt_input",
        item=item,
        side=side,
        direction=direction,
        rate_per_second=rate_per_second,
        belt_tier=belt_tier,
        lane_count=lane_count,
        description=description,
        connects_to=connects_to,
    ).to_dict()


def belt_output(
    connector_id: str,
    item: str,
    *,
    side: str = "right",
    direction: str = "east",
    rate_per_second: float = 0.0,
    belt_tier: str = "transport_belt",
    lane_count: int = 1,
    description: str = "",
    connects_to: tuple[str, ...] = (),
) -> ConnectorDict:
    return Connector(
        id=connector_id,
        kind="belt_output",
        item=item,
        side=side,
        direction=direction,
        rate_per_second=rate_per_second,
        belt_tier=belt_tier,
        lane_count=lane_count,
        description=description,
        connects_to=connects_to,
    ).to_dict()


def manual_input(
    connector_id: str,
    item: str,
    *,
    description: str,
    required: bool = True,
) -> ConnectorDict:
    return Connector(
        id=connector_id,
        kind="manual_input",
        item=item,
        side="local",
        direction="manual",
        required=required,
        description=description,
    ).to_dict()


def chest_output(
    connector_id: str,
    item: str,
    *,
    description: str,
    required: bool = False,
) -> ConnectorDict:
    return Connector(
        id=connector_id,
        kind="chest_output",
        item=item,
        side="local",
        direction="chest",
        required=required,
        description=description,
    ).to_dict()
