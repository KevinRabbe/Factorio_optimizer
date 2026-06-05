from __future__ import annotations

import os

from flask import Flask, jsonify, request, send_from_directory

from factorio_optimizer.config.generation_config import Era
from factorio_optimizer.core.errors import DomainError, InputError
from factorio_optimizer.compiler.module_blueprint_compiler import (
    ModuleBlueprintRequest,
    compile_module_blueprint,
)
from factorio_optimizer.compiler.request import OptimizationRequest
from factorio_optimizer.compiler.simple_compiler import compile_optimization_request
from factorio_optimizer.compiler.smelting_block_compiler import (
    SmeltingBlockRequest,
    compile_smelting_block,
)
from factorio_optimizer.compiler.green_circuit_compiler import (
    GreenCircuitBlockRequest,
    compile_green_circuit_block,
)
from factorio_optimizer.compiler.red_science_compiler import (
    RedScienceBlockRequest,
    compile_red_science_block,
)
from factorio_optimizer.compiler.mid_tier_compiler import (
    MidBlockRequest,
    MidTierSliceRequest,
    ScienceSliceRequest,
    compile_blue_science_slice,
    compile_early_science_slice,
    compile_mid_block,
    compile_mid_tier_slice,
)
from factorio_optimizer.compiler.scaling_planner import (
    ScaledEarlyScienceRequest,
    ScaledGreenCircuitRequest,
    plan_scaled_early_science,
    plan_scaled_green_circuits,
)
from factorio_optimizer.config.generation_config import GenerationConfig
from factorio_optimizer.data.items import get_optimizable_items, has_item
from factorio_optimizer.data.modules import MODULES, ModuleConfig, get_module
from factorio_optimizer.data.recipes import has_recipe
from factorio_optimizer.data.saved_layouts import delete_layout, get_all_layouts, save_layout


app = Flask(
    __name__,
    static_folder=os.path.join(os.path.dirname(__file__), "static"),
    template_folder=os.path.join(os.path.dirname(__file__), "static"),
    static_url_path="/",
)


@app.route("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


@app.route("/api/items")
def api_items():
    return jsonify(get_optimizable_items())


@app.route("/api/modules")
def api_modules():
    result = {}
    for mod in MODULES.values():
        era = mod.era
        if era not in result:
            result[era] = []
        result[era].append({
            "name": mod.name,
            "display_name": mod.display_name,
            "tier": mod.tier,
            "module_type": mod.module_type,
            "speed_bonus_pct": round(mod.speed_bonus * 100, 1),
            "productivity_bonus_pct": round(mod.productivity_bonus * 100, 1),
            "energy_bonus_pct": round(mod.energy_bonus * 100, 1),
            "allowed_machine_types": list(mod.allowed_machine_types),
        })
    return jsonify(result)


@app.route("/api/optimize", methods=["POST"])
def api_optimize():
    try:
        data = _json_payload()
        item = _parse_recipe_item(data.get("item", "automation_science_pack"))
        rate = _parse_positive_float(data.get("rate", 1.0), "rate")
        unit = _parse_unit(data.get("unit", "per_minute"))
        era = _parse_era(data.get("era", "mid"))
        power_mode = data.get("power_mode", "external")
        seed = _parse_int(data.get("seed", 0), "seed")
        use_electric_furnace = _parse_bool(data.get("use_electric_furnace", False))
        compare_furnace_modes = _parse_bool(data.get("compare_furnace_modes", False))
        belt_name = data.get("belt_name") or None
        inserter_name = data.get("inserter_name") or None
        logistics_strategy = data.get("logistics_strategy") or "central_smelting"
        rate_ps = _rate_per_second(rate, unit)
        module_configs = _parse_module_configs(data.get("modules", []))
        furnace_mode = _furnace_mode_label(
            era=era,
            use_electric_furnace=use_electric_furnace,
            compare_furnace_modes=compare_furnace_modes,
        )
        furnace_mode_note = _furnace_mode_note(
            era=era,
            use_electric_furnace=use_electric_furnace,
            compare_furnace_modes=compare_furnace_modes,
        )
        report = compile_optimization_request(
            OptimizationRequest(
                target_item=item,
                target_rate_per_second=rate_ps,
                era=era,
                power_mode=power_mode,
                module_configs=module_configs,
                use_electric_furnace=use_electric_furnace,
                compare_furnace_modes=compare_furnace_modes,
                belt_name=belt_name,
                inserter_name=inserter_name,
                logistics_strategy=logistics_strategy,
                config=GenerationConfig(seed=seed, era=era, power_mode=power_mode),
            )
        )
    except (DomainError, ValueError) as exc:
        return jsonify({"error": str(exc)}), 400

    report_dict = report.to_dict()
    plans = report_dict["plans"]

    return jsonify({
        "item": item,
        "rate": rate,
        "unit": unit,
        "rate_per_second": round(rate_ps, 6),
        "era": era,
        "use_electric_furnace": use_electric_furnace,
        "compare_furnace_modes": compare_furnace_modes,
        "belt_name": belt_name,
        "inserter_name": inserter_name,
        "logistics_strategy": logistics_strategy,
        "furnace_mode": furnace_mode,
        "furnace_mode_note": furnace_mode_note,
        "plans": plans[:5],
        "report": report_dict,
        "best_plan": report_dict["best_plan"],
        "summary": report_dict["summary"],
        "diagnostics": report_dict["diagnostics"],
    })


@app.route("/api/generate-module-blueprint", methods=["POST"])
def api_generate_module_blueprint():
    try:
        data = _json_payload()
        recipe_name = data.get("recipe_name") or data.get("item")
        if not recipe_name:
            raise InputError("Missing recipe_name or item.")
        recipe_name = _parse_recipe_item(recipe_name)
        era = _parse_era(data.get("era", "early"))
        machine_name = data.get("machine_name") or None
        seed = _parse_int(data.get("seed", 0), "seed")
        report = compile_module_blueprint(
            ModuleBlueprintRequest(
                recipe_name=recipe_name,
                era=era,
                machine_name=machine_name,
                seed=seed,
            )
        )
    except (DomainError, ValueError) as exc:
        return jsonify({"error": str(exc)}), 400

    return jsonify(report.to_dict())


@app.route("/api/generate-smelting-block", methods=["POST"])
def api_generate_smelting_block():
    try:
        data = _json_payload()
        recipe_name = data.get("recipe_name") or data.get("item")
        if not recipe_name:
            raise InputError("Missing recipe_name or item.")
        recipe_name = _parse_recipe_item(recipe_name)
        rate = _parse_positive_float(data.get("rate", data.get("target_rate", 30.0)), "rate")
        unit = _parse_unit(data.get("unit", "per_minute"))
        rate_ps = _rate_per_second(rate, unit)
        machine_name = data.get("machine_name") or "stone_furnace"
        belt_name = data.get("belt_name") or "transport_belt"
        inserter_name = data.get("inserter_name") or "inserter"
        max_furnaces_per_row = _parse_int(data.get("max_furnaces_per_row", 12), "max_furnaces_per_row")
        report = compile_smelting_block(
            SmeltingBlockRequest(
                recipe_name=recipe_name,
                target_rate_per_second=rate_ps,
                machine_name=machine_name,
                belt_name=belt_name,
                inserter_name=inserter_name,
                max_furnaces_per_row=max_furnaces_per_row,
            )
        )
    except (DomainError, ValueError) as exc:
        return jsonify({"error": str(exc)}), 400

    return jsonify(report.to_dict())


@app.route("/api/generate-green-circuit-block", methods=["POST"])
def api_generate_green_circuit_block():
    try:
        data = _json_payload()
        rate = _parse_positive_float(data.get("rate", data.get("target_rate", 60.0)), "rate")
        unit = _parse_unit(data.get("unit", "per_minute"))
        era = _parse_era(data.get("era", "mid"))
        machine_name = data.get("machine_name") or None
        belt_name = data.get("belt_name") or "transport_belt"
        inserter_name = data.get("inserter_name") or "inserter"
        include_power_poles = _parse_bool(data.get("include_power_poles", True))
        report = compile_green_circuit_block(
            GreenCircuitBlockRequest(
                target_rate_per_second=_rate_per_second(rate, unit),
                era=era,
                machine_name=machine_name,
                belt_name=belt_name,
                inserter_name=inserter_name,
                include_power_poles=include_power_poles,
            )
        )
    except (DomainError, ValueError) as exc:
        return jsonify({"error": str(exc)}), 400

    return jsonify(report.to_dict())


@app.route("/api/generate-red-science-block", methods=["POST"])
def api_generate_red_science_block():
    try:
        data = _json_payload()
        rate = _parse_positive_float(data.get("rate", data.get("target_rate", 30.0)), "rate")
        unit = _parse_unit(data.get("unit", "per_minute"))
        era = _parse_era(data.get("era", "early"))
        machine_name = data.get("machine_name") or None
        belt_name = data.get("belt_name") or "transport_belt"
        inserter_name = data.get("inserter_name") or "inserter"
        include_power_poles = _parse_bool(data.get("include_power_poles", True))
        report = compile_red_science_block(
            RedScienceBlockRequest(
                target_rate_per_second=_rate_per_second(rate, unit),
                era=era,
                machine_name=machine_name,
                belt_name=belt_name,
                inserter_name=inserter_name,
                include_power_poles=include_power_poles,
            )
        )
    except (DomainError, ValueError) as exc:
        return jsonify({"error": str(exc)}), 400

    return jsonify(report.to_dict())


@app.route("/api/generate-early-science-slice", methods=["POST"])
def api_generate_early_science_slice():
    try:
        data = _json_payload()
        rate = _parse_positive_float(data.get("rate", data.get("target_rate", 30.0)), "rate")
        unit = _parse_unit(data.get("unit", "per_minute"))
        machine_tier = _parse_machine_tier(data.get("machine_tier", data.get("era", "mid")))
        transport_tier = _parse_transport_tier(data.get("transport_tier", "mid"))
        fluid_mode = _parse_fluid_mode(data.get("fluid_mode", "external"))
        include_power_poles = _parse_bool(data.get("include_power_poles", True))
        report = compile_early_science_slice(
            ScienceSliceRequest(
                target_rate_per_second=_rate_per_second(rate, unit),
                machine_tier=machine_tier,
                transport_tier=transport_tier,
                fluid_mode=fluid_mode,
                include_power_poles=include_power_poles,
            )
        )
    except (DomainError, ValueError) as exc:
        return jsonify({"error": str(exc)}), 400

    return jsonify(report.to_dict())


@app.route("/api/generate-mid-block", methods=["POST"])
def api_generate_mid_block():
    try:
        data = _json_payload()
        item = _parse_recipe_item(data.get("item"))
        rate = _parse_positive_float(data.get("rate", data.get("target_rate", 30.0)), "rate")
        unit = _parse_unit(data.get("unit", "per_minute"))
        machine_tier = _parse_machine_tier(data.get("machine_tier", data.get("era", "mid")))
        transport_tier = _parse_transport_tier(data.get("transport_tier", "mid"))
        fluid_mode = _parse_fluid_mode(data.get("fluid_mode", "external"))
        include_power_poles = _parse_bool(data.get("include_power_poles", True))
        report = compile_mid_block(
            MidBlockRequest(
                item=item,
                target_rate_per_second=_rate_per_second(rate, unit),
                machine_tier=machine_tier,
                transport_tier=transport_tier,
                fluid_mode=fluid_mode,
                include_power_poles=include_power_poles,
            )
        )
    except (DomainError, ValueError) as exc:
        return jsonify({"error": str(exc)}), 400

    return jsonify(report.to_dict())


@app.route("/api/generate-blue-science-slice", methods=["POST"])
def api_generate_blue_science_slice():
    try:
        data = _json_payload()
        rate = _parse_positive_float(data.get("rate", data.get("target_rate", 30.0)), "rate")
        unit = _parse_unit(data.get("unit", "per_minute"))
        machine_tier = _parse_machine_tier(data.get("machine_tier", data.get("era", "mid")))
        transport_tier = _parse_transport_tier(data.get("transport_tier", "mid"))
        fluid_mode = _parse_fluid_mode(data.get("fluid_mode", "external"))
        include_power_poles = _parse_bool(data.get("include_power_poles", True))
        report = compile_blue_science_slice(
            ScienceSliceRequest(
                target_rate_per_second=_rate_per_second(rate, unit),
                machine_tier=machine_tier,
                transport_tier=transport_tier,
                fluid_mode=fluid_mode,
                include_power_poles=include_power_poles,
            )
        )
    except (DomainError, ValueError) as exc:
        return jsonify({"error": str(exc)}), 400

    return jsonify(report.to_dict())


@app.route("/api/generate-mid-tier-slice", methods=["POST"])
def api_generate_mid_tier_slice():
    try:
        data = _json_payload()
        item = _parse_recipe_item(data.get("item"))
        rate = _parse_positive_float(data.get("rate", data.get("target_rate", 30.0)), "rate")
        unit = _parse_unit(data.get("unit", "per_minute"))
        machine_tier = _parse_machine_tier(data.get("machine_tier", data.get("era", "mid")))
        transport_tier = _parse_transport_tier(data.get("transport_tier", "mid"))
        fluid_mode = _parse_fluid_mode(data.get("fluid_mode", "external"))
        strategy = _parse_mid_strategy(data.get("strategy", "readable"))
        include_power_poles = _parse_bool(data.get("include_power_poles", True))
        report = compile_mid_tier_slice(
            MidTierSliceRequest(
                item=item,
                target_rate_per_second=_rate_per_second(rate, unit),
                machine_tier=machine_tier,
                transport_tier=transport_tier,
                fluid_mode=fluid_mode,
                strategy=strategy,
                include_power_poles=include_power_poles,
            )
        )
    except (DomainError, ValueError) as exc:
        return jsonify({"error": str(exc)}), 400

    return jsonify(report.to_dict())


@app.route("/api/generate-scaled-early-science-plan", methods=["POST"])
def api_generate_scaled_early_science_plan():
    try:
        data = _json_payload()
        rate = _parse_positive_float(data.get("rate", data.get("target_rate", 300.0)), "rate")
        unit = _parse_unit(data.get("unit", "per_minute"))
        block_rate = _parse_positive_float(data.get("block_rate", 30.0), "block_rate")
        block_unit = _parse_unit(data.get("block_unit", unit))
        machine_tier = _parse_machine_tier(data.get("machine_tier", data.get("era", "mid")))
        transport_tier = _parse_transport_tier(data.get("transport_tier", "mid"))
        include_power_poles = _parse_bool(data.get("include_power_poles", True))
        report = plan_scaled_early_science(
            ScaledEarlyScienceRequest(
                target_rate_per_second=_rate_per_second(rate, unit),
                block_rate_per_second=_rate_per_second(block_rate, block_unit),
                machine_tier=machine_tier,
                transport_tier=transport_tier,
                include_power_poles=include_power_poles,
            )
        )
    except (DomainError, ValueError) as exc:
        return jsonify({"error": str(exc)}), 400

    return jsonify(report.to_dict())


@app.route("/api/generate-scaled-green-circuit-plan", methods=["POST"])
def api_generate_scaled_green_circuit_plan():
    try:
        data = _json_payload()
        rate = _parse_positive_float(data.get("rate", data.get("target_rate", 300.0)), "rate")
        unit = _parse_unit(data.get("unit", "per_minute"))
        block_rate = _parse_positive_float(data.get("block_rate", 60.0), "block_rate")
        block_unit = _parse_unit(data.get("block_unit", unit))
        era = _parse_era(data.get("era", "mid"))
        include_power_poles = _parse_bool(data.get("include_power_poles", True))
        report = plan_scaled_green_circuits(
            ScaledGreenCircuitRequest(
                target_rate_per_second=_rate_per_second(rate, unit),
                block_rate_per_second=_rate_per_second(block_rate, block_unit),
                era=era,
                include_power_poles=include_power_poles,
            )
        )
    except (DomainError, ValueError) as exc:
        return jsonify({"error": str(exc)}), 400

    return jsonify(report.to_dict())


def _furnace_mode_label(era: str, use_electric_furnace: bool, compare_furnace_modes: bool) -> str:
    if era == "early":
        return "burner_only"
    if compare_furnace_modes:
        return "compared"
    return "electric_furnace" if use_electric_furnace else "burner_furnace"


def _furnace_mode_note(era: str, use_electric_furnace: bool, compare_furnace_modes: bool) -> str:
    if era == "early":
        return "Early-game plans use burner furnaces only."
    if compare_furnace_modes:
        return "Plans compare available burner/electric furnace alternatives automatically."
    if use_electric_furnace:
        return "Plans respect the selected electric furnace mode."
    return "Plans respect the selected burner/steel furnace mode."


def _json_payload() -> dict:
    data = request.get_json(force=True, silent=True)
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise InputError("Request JSON body must be an object.")
    return data


def _parse_recipe_item(item: object) -> str:
    if not isinstance(item, str) or not item:
        raise InputError("item must be a non-empty string.")
    if not has_item(item):
        raise InputError(f"Unknown item: {item!r}.")
    if not has_recipe(item):
        raise InputError(f"Item {item!r} has no known recipe.")
    return item


def _parse_positive_float(value: object, field_name: str) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError) as exc:
        raise InputError(f"{field_name} must be a number.") from exc
    if parsed <= 0:
        raise InputError(f"{field_name} must be greater than zero.")
    return parsed


def _parse_int(value: object, field_name: str) -> int:
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise InputError(f"{field_name} must be an integer.") from exc


def _parse_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"true", "1", "yes", "on"}:
            return True
        if normalized in {"false", "0", "no", "off"}:
            return False
    return bool(value)


def _parse_unit(value: object) -> str:
    if value not in {"per_second", "per_minute", "per_hour"}:
        raise InputError("unit must be one of: per_second, per_minute, per_hour.")
    return str(value)


def _parse_era(value: object) -> Era:
    if value not in {"early", "mid", "end"}:
        raise InputError("era must be one of: early, mid, end.")
    return value


def _parse_machine_tier(value: object) -> str:
    if value not in {"early", "mid"}:
        raise InputError("machine_tier must be one of: early, mid.")
    return str(value)


def _parse_transport_tier(value: object) -> str:
    if value not in {"early", "mid"}:
        raise InputError("transport_tier must be one of: early, mid.")
    return str(value)


def _parse_fluid_mode(value: object) -> str:
    if value != "external":
        raise InputError("fluid_mode must be 'external' for mid-tier v1.")
    return str(value)


def _parse_mid_strategy(value: object) -> str:
    allowed = {"readable", "compact", "external_fluids", "external_plates", "include_smelting"}
    if value not in allowed:
        raise InputError("strategy must be one of: readable, compact, external_fluids, external_plates, include_smelting.")
    return str(value)


def _rate_per_second(rate: float, unit: str) -> float:
    if unit == "per_minute":
        return rate / 60.0
    if unit == "per_hour":
        return rate / 3600.0
    return rate


def _parse_module_configs(raw_modules: object) -> list[ModuleConfig]:
    if raw_modules is None:
        return []
    if not isinstance(raw_modules, list):
        raise InputError("modules must be a list.")
    module_configs: list[ModuleConfig] = []
    for entry in raw_modules:
        if not isinstance(entry, dict):
            raise InputError("each module entry must be an object.")
        name = entry.get("name")
        if not isinstance(name, str):
            raise InputError("module entry name must be a string.")
        count = _parse_int(entry.get("count", 1), "module count")
        if count < 1:
            raise InputError("module count must be at least 1.")
        module_configs.append(ModuleConfig(module=get_module(name), count=count))
    return module_configs


@app.route("/api/layouts", methods=["GET"])
def api_get_layouts():
    return jsonify(get_all_layouts())


@app.route("/api/layouts/save", methods=["POST"])
def api_save_layout():
    data = request.get_json(force=True, silent=True) or {}
    custom_name = data.get("custom_name", "")
    plan_data = data.get("plan_data")

    if not plan_data:
        return jsonify({"error": "Missing plan_data"}), 400

    record = save_layout(plan_data, custom_name)
    return jsonify(record)


@app.route("/api/layouts/<layout_id>", methods=["DELETE"])
def api_delete_layout(layout_id):
    success = delete_layout(layout_id)
    if success:
        return jsonify({"status": "deleted"})
    return jsonify({"error": "Not found"}), 404
