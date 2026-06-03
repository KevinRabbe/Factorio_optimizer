from __future__ import annotations

import base64
import json
import zlib
from typing import Any


def encode_blueprint_string(blueprint_json: dict[str, Any]) -> str:
    raw_json = json.dumps(
        blueprint_json,
        separators=(",", ":"),
    ).encode("utf-8")

    compressed = zlib.compress(raw_json)
    encoded = base64.b64encode(compressed).decode("utf-8")

    return "0" + encoded
