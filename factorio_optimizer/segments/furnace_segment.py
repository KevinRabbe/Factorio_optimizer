from __future__ import annotations

from dataclasses import dataclass

from factorio_optimizer.core.objects import Direction, FactoryObject, Position
from factorio_optimizer.segments.ports import SegmentPort
from factorio_optimizer.segments.segment_base import Segment


@dataclass
class FurnaceSegment(Segment):
    recipe: str = ""
    input_items: tuple[str, ...] = ()
    output_item: str = ""
    machine_type: str = "stone_furnace"
    width: int = 2
    height: int = 2

    def __post_init__(self) -> None:
        self.segment_type = "furnace_segment"
        self.ports = self._build_ports()

    def expand(self) -> list[FactoryObject]:
        return [
            FactoryObject(
                object_id=f"{self.segment_id}_furnace",
                object_type="furnace",
                position=self.position,
                direction=self.direction,
                width=self.width,
                height=self.height,
                recipe=self.recipe,
                role="producer",
                entity_name=self.machine_type.replace("_", "-"),
            )
        ]

    def _build_ports(self) -> list[SegmentPort]:
        center_y = self.position.y + self.height // 2
        left_x = self.position.x - 1
        right_x = self.position.x + self.width

        ports: list[SegmentPort] = []

        for item in self.input_items:
            ports.append(
                SegmentPort(
                    port_id=f"{self.segment_id}_{item}_input",
                    item=item,
                    kind="input",
                    position=Position(left_x, center_y),
                    direction="east",
                )
            )

        if self.output_item:
            ports.append(
                SegmentPort(
                    port_id=f"{self.segment_id}_{self.output_item}_output",
                    item=self.output_item,
                    kind="output",
                    position=Position(right_x, center_y),
                    direction="east",
                )
            )

        return ports


def create_furnace_segment(
    segment_id: str,
    recipe: str,
    input_items: tuple[str, ...],
    output_item: str,
    position: Position,
    machine_type: str = "stone_furnace",
    direction: Direction = "north",
) -> FurnaceSegment:
    return FurnaceSegment(
        segment_id=segment_id,
        segment_type="furnace_segment",
        position=position,
        direction=direction,
        recipe=recipe,
        input_items=input_items,
        output_item=output_item,
        machine_type=machine_type,
    )
