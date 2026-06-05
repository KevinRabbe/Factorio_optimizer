from __future__ import annotations

from dataclasses import dataclass

from factorio_optimizer.core.objects import Direction, FactoryObject, Position
from factorio_optimizer.data.entities import get_entity_spec
from factorio_optimizer.segments.ports import SegmentPort
from factorio_optimizer.segments.segment_base import Segment


@dataclass
class AssemblerSegment(Segment):
    recipe: str = ""
    input_items: tuple[str, ...] = ()
    output_item: str = ""
    machine_type: str = "assembling_machine_1"
    width: int = 3
    height: int = 3

    def __post_init__(self) -> None:
        self.segment_type = "assembler_segment"
        spec = get_entity_spec(self.machine_type.replace("_", "-"))
        self.width = spec.width
        self.height = spec.height
        self.ports = self._build_ports()

    def expand(self) -> list[FactoryObject]:
        return [
            FactoryObject(
                object_id=f"{self.segment_id}_assembler",
                object_type="assembler",
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


def create_assembler_segment(
    segment_id: str,
    recipe: str,
    input_items: tuple[str, ...],
    output_item: str,
    position: Position,
    machine_type: str = "assembling_machine_1",
    direction: Direction = "north",
) -> AssemblerSegment:
    return AssemblerSegment(
        segment_id=segment_id,
        segment_type="assembler_segment",
        position=position,
        direction=direction,
        recipe=recipe,
        input_items=input_items,
        output_item=output_item,
        machine_type=machine_type,
    )
