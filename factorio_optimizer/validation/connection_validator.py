from __future__ import annotations

from typing import Any

from factorio_optimizer.modules.module_base import FactoryModule
from factorio_optimizer.segments.ports import SegmentPort
from factorio_optimizer.validation.static_validator import ValidationResult


def validate_module_connections(module: FactoryModule) -> ValidationResult:
    result = ValidationResult()
    ports_by_id = {port.port_id: port for port in module.ports}
    links: list[Any] = getattr(module, "flow_links", [])

    for link in links:
        source_port = ports_by_id.get(link.source_port_id)
        target_port = ports_by_id.get(link.target_port_id)

        if source_port is None:
            result.add_error(f"Connection {link.flow_id} has unknown source port {link.source_port_id}.")
            continue

        if target_port is None:
            result.add_error(f"Connection {link.flow_id} has unknown target port {link.target_port_id}.")
            continue

        _validate_connection_ports(link.flow_id, link.item, source_port, target_port, result)

    return result


def validate_modules_connections(modules: list[FactoryModule]) -> ValidationResult:
    result = ValidationResult()

    for module in modules:
        module_result = validate_module_connections(module)
        for error in module_result.errors:
            result.add_error(f"{module.module_id}: {error}")

    return result


def _validate_connection_ports(
    flow_id: str,
    item: str,
    source_port: SegmentPort,
    target_port: SegmentPort,
    result: ValidationResult,
) -> None:
    if source_port.kind != "output":
        result.add_error(f"Connection {flow_id} source port is not an output port.")

    if target_port.kind != "input":
        result.add_error(f"Connection {flow_id} target port is not an input port.")

    if source_port.item != target_port.item:
        result.add_error(
            f"Connection {flow_id} item mismatch: "
            f"source={source_port.item}, target={target_port.item}."
        )

    if source_port.item != item:
        result.add_error(
            f"Connection {flow_id} declared item {item} does not match source port item {source_port.item}."
        )
