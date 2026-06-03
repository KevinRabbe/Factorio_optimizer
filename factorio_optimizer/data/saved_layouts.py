from __future__ import annotations

import json
from pathlib import Path
import uuid
from datetime import datetime
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
RUNTIME_DIR = PROJECT_ROOT / "runtime"
DB_PATH = RUNTIME_DIR / "saved_layouts.json"


def _load_db() -> dict[str, Any]:
    if not DB_PATH.exists():
        return {}
    try:
        with DB_PATH.open("r", encoding="utf-8") as file:
            return json.load(file)
    except Exception:
        return {}


def _save_db(data: dict[str, Any]) -> None:
    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
    with DB_PATH.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=2)


def get_all_layouts() -> list[dict[str, Any]]:
    db = _load_db()
    layouts = list(db.values())
    layouts.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return layouts


def save_layout(plan_data: dict[str, Any], custom_name: str = "") -> dict[str, Any]:
    db = _load_db()
    layout_id = str(uuid.uuid4())
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
    db = _load_db()
    if layout_id in db:
        del db[layout_id]
        _save_db(db)
        return True
    return False
