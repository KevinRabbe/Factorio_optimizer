from __future__ import annotations

from dataclasses import dataclass
from math import ceil
from typing import Any, Callable

from factorio_optimizer.compiler.green_circuit_compiler import (
    GreenCircuitBlockRequest,
    compile_green_circuit_block,
)
from factorio_optimizer.compiler.mid_tier_compiler import (
    FactoryBlueprintReport,
    ScienceSliceRequest,
    compile_early_science_slice,
)


@dataclass(frozen=True)
class ScaledEarlyScienceRequest:
    target_rate_per_second: float = 5.0
    block_rate_per_second: float | None = None
    machine_tier: str = "mid"
    transport_tier: str = "mid"
    include_power_poles: bool = True


@dataclass(frozen=True)
class ScaledGreenCircuitRequest:
    target_rate_per_second: float = 5.0
    block_rate_per_second: float | None = None
    era: str = "mid"
    belt_name: str = "transport_belt"
    inserter_name: str = "inserter"
    include_power_poles: bool = True


def plan_scaled_early_science(request: ScaledEarlyScienceRequest) -> FactoryBlueprintReport:
    _validate_target_rate(request.target_rate_per_second)

    selection = _choose_block_variant(
        target_rate_per_second=request.target_rate_per_second,
        requested_block_rate_per_second=request.block_rate_per_second,
        candidate_block_rates_per_minute=[15, 30, 45, 60],
        compile_block=lambda block_rate_per_second: compile_early_science_slice(
            ScienceSliceRequest(
                target_rate_per_second=block_rate_per_second,
                machine_tier=request.machine_tier,
                transport_tier=request.transport_tier,
                include_power_poles=request.include_power_poles,
            )
        ),
    )

    return _build_scaled_report(
        item="scaled_early_science",
        planner_mode="scaled_repeatable_early_science",
        target_rate_per_second=request.target_rate_per_second,
        requested_block_rate_per_second=request.block_rate_per_second,
        selected=selection,
        machine_count_getter=lambda build_list, _block: sum(
            count
            for key, count in build_list.items()
            if "assembling_machine" in key or key == "labs"
        ),
        section_name="Early Science Slice",
        blueprint_label="repeat representative early science blueprint",
        output_items=["automation_science_pack", "logistic_science_pack"],
        ascii_label="R+G",
    )


def plan_scaled_green_circuits(request: ScaledGreenCircuitRequest) -> FactoryBlueprintReport:
    _validate_target_rate(request.target_rate_per_second)

    selection = _choose_block_variant(
        target_rate_per_second=request.target_rate_per_second,
        requested_block_rate_per_second=request.block_rate_per_second,
        candidate_block_rates_per_minute=[30, 45, 60, 90],
        compile_block=lambda block_rate_per_second: compile_green_circuit_block(
            GreenCircuitBlockRequest(
                target_rate_per_second=block_rate_per_second,
                era=request.era,
                belt_name=request.belt_name,
                inserter_name=request.inserter_name,
                include_power_poles=request.include_power_poles,
            )
        ),
    )

    return _build_scaled_report(
        item="scaled_green_circuits",
        planner_mode="scaled_repeatable_green_circuits",
        target_rate_per_second=request.target_rate_per_second,
        requested_block_rate_per_second=request.block_rate_per_second,
        selected=selection,
        machine_count_getter=lambda build_list, _block: int(build_list.get("assemblers", 0)),
        section_name="Green Circuit Block",
        blueprint_label="repeat representative green circuit blueprint",
        output_items=["electronic_circuit"],
        ascii_label="GC",
    )


def _validate_target_rate(target_rate_per_second: float) -> None:
    if target_rate_per_second <= 0:
        raise ValueError("target_rate_per_second must be greater than zero.")


def _choose_block_variant(
    target_rate_per_second: float,
    requested_block_rate_per_second: float | None,
    candidate_block_rates_per_minute: list[float],
    compile_block: Callable[[float], FactoryBlueprintReport],
) -> dict[str, Any]:
    if requested_block_rate_per_second is not None:
        if requested_block_rate_per_second <= 0:
            raise ValueError("block_rate_per_second must be greater than zero.")
        if requested_block_rate_per_second > target_rate_per_second:
            raise ValueError("block_rate_per_second cannot be greater than target_rate_per_second.")
        candidate_rates = [requested_block_rate_per_second]
        mode = "fixed"
    else:
        candidate_rates = [
            rate_per_minute / 60.0
            for rate_per_minute in candidate_block_rates_per_minute
            if (rate_per_minute / 60.0) <= target_rate_per_second
        ] or [target_rate_per_second]
        mode = "auto"

    candidates: list[dict[str, Any]] = []
    for candidate_rate in candidate_rates:
        block = compile_block(candidate_rate)
        block_capacity_per_second = float(block.summary["capacity_per_second"])
        block_count = ceil(target_rate_per_second / block_capacity_per_second)
        total_capacity_per_second = block_count * block_capacity_per_second
        candidates.append({
            "requested_block_rate_per_second": candidate_rate,
            "requested_block_rate_per_minute": round(candidate_rate * 60.0, 4),
            "block": block,
            "block_count": block_count,
            "block_capacity_per_second": block_capacity_per_second,
            "total_capacity_per_second": total_capacity_per_second,
            "overbuild_per_second": round(total_capacity_per_second - target_rate_per_second, 6),
        })

    candidates.sort(
        key=lambda option: (
            option["overbuild_per_second"],
            option["block_count"],
            -option["block_capacity_per_second"],
        )
    )

    selected = candidates[0]
    selected["selection_mode"] = mode
    selected["alternatives"] = [
        {
            "requested_block_rate_per_minute": option["requested_block_rate_per_minute"],
            "actual_block_rate_per_minute": round(option["block"].summary["capacity_per_minute"], 4),
            "block_count": option["block_count"],
            "capacity_per_minute": round(option["total_capacity_per_second"] * 60.0, 4),
            "overbuild_per_minute": round(option["overbuild_per_second"] * 60.0, 4),
        }
        for option in candidates
    ]
    return selected


def _build_scaled_report(
    item: str,
    planner_mode: str,
    target_rate_per_second: float,
    requested_block_rate_per_second: float | None,
    selected: dict[str, Any],
    machine_count_getter: Callable[[dict[str, int], FactoryBlueprintReport], int],
    section_name: str,
    blueprint_label: str,
    output_items: list[str],
    ascii_label: str,
) -> FactoryBlueprintReport:
    block = selected["block"]
    block_count = selected["block_count"]
    total_capacity_per_second = selected["total_capacity_per_second"]
    total_build_list = _multiply_counts(block.build_list, block_count)
    total_machine_count = machine_count_getter(total_build_list, block)
    external_inputs = _multiply_rates(block.diagnostics.get("external_inputs", {}), block_count)
    belt_capacity = float(block.diagnostics.get("belt_capacity_per_second", 15.0))
    input_lanes = {
        input_item: {
            "rate_per_second": rate,
            "rate_per_minute": round(rate * 60.0, 4),
            "minimum_belts": max(1, ceil(rate / belt_capacity)),
        }
        for input_item, rate in external_inputs.items()
    }
    external_input_lanes = {
        input_item: [
            {
                "pattern": f"{lane['minimum_belts']} belt lane(s) feeding {input_item.replace('_', ' ')} across {block_count} repeated blocks",
            }
        ]
        for input_item, lane in input_lanes.items()
    }
    sections = [
        {
            "name": f"{section_name} #{index + 1}",
            "blueprint": blueprint_label,
            "target_per_minute": round(block.summary["capacity_per_minute"], 4),
            "outputs": {
                output_item: round(block.summary["capacity_per_minute"], 4)
                for output_item in output_items
            },
        }
        for index in range(block_count)
    ]
    warnings = _warnings(target_rate_per_second, total_capacity_per_second, block_count)
    diagnostics = {
        "planner_mode": planner_mode,
        "representative_block": {
            "capacity_per_minute": block.summary["capacity_per_minute"],
            "machine_count": machine_count_getter(block.build_list, block),
            "valid": block.valid,
        },
        "selection_mode": selected["selection_mode"],
        "requested_block_rate_per_minute": round((requested_block_rate_per_second or selected["requested_block_rate_per_second"]) * 60.0, 4),
        "selected_block_rate_per_minute": round(block.summary["capacity_per_minute"], 4),
        "candidate_options": selected["alternatives"],
        "repeatable_blocks": block_count,
        "external_inputs": external_inputs,
        "input_lanes": input_lanes,
        "external_input_lanes": external_input_lanes,
        "train_readiness": _train_readiness(input_lanes),
        "sections": sections,
        "warnings": warnings,
    }
    summary = {
        "item": item,
        "target_rate_per_second": round(target_rate_per_second, 6),
        "target_rate_per_minute": round(target_rate_per_second * 60.0, 4),
        "capacity_per_second": round(total_capacity_per_second, 6),
        "capacity_per_minute": round(total_capacity_per_second * 60.0, 4),
        "machine_count": total_machine_count,
        "block_count": block_count,
        "block_rate_per_minute": round(block.summary["capacity_per_minute"], 4),
    }

    return FactoryBlueprintReport(
        valid=block.valid,
        validation_errors=block.validation_errors,
        validation_confidence=block.validation_confidence,
        blueprint_string=block.blueprint_string,
        blueprint_json=block.blueprint_json,
        ascii=_scaled_ascii(block_count, block.summary["capacity_per_second"], ascii_label),
        summary=summary,
        build_list=total_build_list,
        diagnostics=diagnostics,
    )


def _multiply_counts(build_list: dict[str, Any], multiplier: int) -> dict[str, int]:
    return {
        item: int(count) * multiplier
        for item, count in build_list.items()
        if isinstance(count, int | float)
    }


def _multiply_rates(rates: dict[str, Any], multiplier: int) -> dict[str, float]:
    return {
        item: round(float(rate) * multiplier, 6)
        for item, rate in rates.items()
    }


def _train_readiness(input_lanes: dict[str, dict[str, float]]) -> dict[str, Any]:
    high_throughput_inputs = [
        item
        for item, lane in input_lanes.items()
        if lane["minimum_belts"] >= 2
    ]
    return {
        "recommended": bool(high_throughput_inputs),
        "reason": "Use chunk-aligned unload stations for multi-belt inputs."
        if high_throughput_inputs
        else "Belts are sufficient for this target rate.",
        "station_blocks": [
            {
                "item": item,
                "suggested_station": f"{item} unload",
                "minimum_output_belts": input_lanes[item]["minimum_belts"],
                "notes": "Prefer a stacker and train limits instead of feeding one giant bus directly.",
            }
            for item in high_throughput_inputs
        ],
    }


def _warnings(target_rate_per_second: float, total_capacity_per_second: float, block_count: int) -> list[str]:
    warnings = []
    if total_capacity_per_second > target_rate_per_second:
        warnings.append("Capacity is rounded up to whole repeatable blocks.")
    if block_count > 8:
        warnings.append("Large targets should be pasted as chunk-aligned sections or blueprint-book pages.")
    return warnings


def _scaled_ascii(block_count: int, block_rate_per_second: float, label: str) -> str:
    block_label = f"{round(block_rate_per_second * 60.0)}m"
    chunks = [f"[{label} {block_label}]" for _ in range(block_count)]
    lines = [
        f"Scaled {label} Plan",
        " ".join(chunks),
        "I: iron/copper/cable inputs  O: science outputs",
        "Use the representative blueprint string once, then paste it for each block.",
    ]
    return "\n".join(lines)
