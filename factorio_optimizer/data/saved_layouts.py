from __future__ import annotations

import json
import os
import uuid
from datetime import datetime
from typing import Any

# Use a local JSON file in the project directory for simple persistence
DATA_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(DATA_DIR, "saved_layouts.json")


def _load_db() -> dict[str, Any]:
    if not os.path.exists(DB_PATH):
        return {}
    try:
        with open(DB_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_db(data: dict[str, Any]) -> None:
    with open(DB_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def get_all_layouts() -> list[dict[str, Any]]:
    """Return all saved layouts, sorted newest first."""
    db = _load_db()
    layouts = list(db.values())
    layouts.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return layouts


def save_layout(plan_data: dict[str, Any], custom_name: str = "") -> dict[str, Any]:
    """Save a FactoryPlan dictionary into the database."""
    db = _load_db()
    
    layout_id = str(uuid.uuid4())
    
    # Store metadata alongside the raw plan
    layout_record = {
        "id": layout_id,
        "created_at": datetime.utcnow().isoformat() + "Z",
        "custom_name": custom_name or f"Saved {plan_data.get('item', 'Item')} Plan",
        "plan_data": plan_data,
    }
    
    db[layout_id] = layout_record
    _save_db(db)
    
    return layout_record


def delete_layout(layout_id: str) -> bool:
    """Delete a layout by ID. Returns True if deleted, False if not found."""
    db = _load_db()
    if layout_id in db:
        del db[layout_id]
        _save_db(db)
        return True
    return False
