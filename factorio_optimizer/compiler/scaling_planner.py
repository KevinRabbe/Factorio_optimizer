from __future__ import annotations

from dataclasses import dataclass
from math import ceil
from typing import Any

from factorio_optimizer.compiler.mid_tier_compiler import (
    FactoryBlueprintReport,
    ScienceSliceRequest,
    compile_early_science_slice,
)


@dataclass(frozen=True)
class ScaledEarlyScienceRequest:
    target_rate_per_second: float = 5.0
    block_rate_per_second: float = 1.0
    machine_tier: str = "mid"
    transport_tier: str = "mid"
    include_power_poles: bool = True


def plan_scaled_early_science(request: ScaledEarlyScienceRequest) -> FactoryBlueprintReport:
    if request.target_rate_per_second <= 0:
        raise ValueError("target_rate_per_second must be greater than zero.")
    if request.block_rate_per_second <= 0:
        raise ValueError("block_rate_per_second must be greater than zero.")
    if request.block_rate_per_second > request.target_rate_per_second:
        raise ValueError("block_rate_per_second cannot be greater than target_rate_per_second.")

    block = compile_early_science_slice(
        ScienceSliceRequest(
            target_rate_per_second=request.block_rate_per_second,
            machine_tier=request.machine_tier,
            transport_tier=request.transport_tier,
            include_power_poles=request.include_power_poles,
        )
    )
    block_count = ceil(request.target_rate_per_second / block.summary["capacity_per_second"])
    total_capacity_per_second = block_count * block.summary["capacity_per_second"]
    total_build_list = _multiply_counts(block.build_list, block_count)
    total_machine_count = sum(
        count
        for key, count in total_build_list.items()
        if "assembling_machine" in key or key == "labs"
    )
    external_inputs = _multiply_rates(block.diagnostics.get("external_inputs", {}), block_count)
    belt_capacity = float(block.diagnostics.get("belt_capacity_per_second", 15.0))
    input_lanes = {
        item: {
            "rate_per_second": rate,
            "rate_per_minute": round(rate * 60.0, 4),
            "minimum_belts": max(1, ceil(rate / belt_capacity)),
        }
        for item, rate in external_inputs.items()
    }
    external_input_lanes = {
        item: [
            {
                "pattern": f"{lane['minimum_belts']} belt lane(s) feeding {item.replace('_', ' ')} across {block_count} repeated blocks",
            }
        ]
        for item, lane in input_lanes.items()
    }
    sections = [
        {
            "name": f"Early Science Slice #{index + 1}",
            "blueprint": "repeat representative early science blueprint",
            "target_per_minute": round(request.block_rate_per_second * 60.0, 4),
            "outputs": {
                "automation_science_pack": round(request.block_rate_per_second * 60.0, 4),
                "logistic_science_pack": round(request.block_rate_per_second * 60.0, 4),
            },
        }
        for index in range(block_count)
    ]
    diagnostics = {
        "planner_mode": "scaled_repeatable_early_science",
        "representative_block": {
            "capacity_per_minute": block.summary["capacity_per_minute"],
            "machine_count": block.summary["machine_count"],
            "valid": block.valid,
        },
        "repeatable_blocks": block_count,
        "external_inputs": external_inputs,
        "input_lanes": input_lanes,
        "external_input_lanes": external_input_lanes,
        "train_readiness": _train_readiness(input_lanes),
        "sections": sections,
        "warnings": _warnings(request, total_capacity_per_second, block_count),
    }
    summary = {
        "item": "scaled_early_science",
        "target_rate_per_second": round(request.target_rate_per_second, 6),
        "target_rate_per_minute": round(request.target_rate_per_second * 60.0, 4),
        "capacity_per_second": round(total_capacity_per_second, 6),
        "capacity_per_minute": round(total_capacity_per_second * 60.0, 4),
        "machine_count": total_machine_count,
        "block_count": block_count,
        "block_rate_per_minute": round(request.block_rate_per_second * 60.0, 4),
    }

    return FactoryBlueprintReport(
        valid=block.valid,
        validation_errors=block.validation_errors,
        validation_confidence=block.validation_confidence,
        blueprint_string=block.blueprint_string,
        blueprint_json=block.blueprint_json,
        ascii=_scaled_ascii(block_count, request.block_rate_per_second),
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


def _warnings(
    request: ScaledEarlyScienceRequest,
    total_capacity_per_second: float,
    block_count: int,
) -> list[str]:
    warnings = []
    if total_capacity_per_second > request.target_rate_per_second:
        warnings.append("Capacity is rounded up to whole repeatable blocks.")
    if block_count > 8:
        warnings.append("Large targets should be pasted as chunk-aligned sections or blueprint-book pages.")
    return warnings


def _scaled_ascii(block_count: int, block_rate_per_second: float) -> str:
    block_label = f"{round(block_rate_per_second * 60.0)}m"
    chunks = [f"[R+G {block_label}]" for _ in range(block_count)]
    lines = [
        "Scaled Red + Green Science Plan",
        " ".join(chunks),
        "I: iron/copper/cable inputs  O: science outputs",
        "Use the representative blueprint string once, then paste it for each block.",
    ]
    return "\n".join(lines)
