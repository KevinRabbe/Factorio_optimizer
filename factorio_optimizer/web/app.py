from __future__ import annotations

import os

from flask import Flask, jsonify, request, send_from_directory

from factorio_optimizer.data.items import get_optimizable_items
from factorio_optimizer.data.modules import MODULES, ModuleConfig, get_module
from factorio_optimizer.data.saved_layouts import delete_layout, get_all_layouts, save_layout
from factorio_optimizer.optimizer.factory_optimizer import compare_plans, factory_plan_to_dict


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
    data = request.get_json(force=True, silent=True) or {}

    item = data.get("item", "automation_science_pack")
    rate = float(data.get("rate", 1.0))
    unit = data.get("unit", "per_minute")
    era = data.get("era", "mid")
    raw_modules = data.get("modules", [])

    if unit == "per_minute":
        rate_ps = rate / 60.0
    elif unit == "per_hour":
        rate_ps = rate / 3600.0
    else:
        rate_ps = rate

    module_configs: list[ModuleConfig] = []
    for entry in raw_modules:
        try:
            mod = get_module(entry["name"])
            count = max(1, int(entry.get("count", 1)))
            module_configs.append(ModuleConfig(module=mod, count=count))
        except (ValueError, KeyError):
            continue

    furnace_mode = "compared"
    furnace_mode_note = "Mid/end plans compare available steel/electric furnace alternatives automatically."
    if era == "early":
        furnace_mode = "burner_only"
        furnace_mode_note = "Early-game plans use burner furnaces only."

    try:
        plans = compare_plans(
            item=item,
            target_per_second=rate_ps,
            era=era,
            user_modules=module_configs if module_configs else None,
        )
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400

    top_plans = [factory_plan_to_dict(p) for p in plans[:5]]

    return jsonify({
        "item": item,
        "rate": rate,
        "unit": unit,
        "rate_per_second": round(rate_ps, 6),
        "era": era,
        "furnace_mode": furnace_mode,
        "furnace_mode_note": furnace_mode_note,
        "plans": top_plans,
    })


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
