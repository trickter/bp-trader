from __future__ import annotations

import json
from collections.abc import Mapping
from urllib.parse import quote


def serialize_scalar(value: object) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if value is None:
        return ""
    if isinstance(value, (int, float, str)):
        return str(value)
    if isinstance(value, (list, tuple)):
        return json.dumps(value, separators=(",", ":"), ensure_ascii=False)
    if isinstance(value, Mapping):
        return json.dumps(dict(sorted(value.items())), separators=(",", ":"), ensure_ascii=False)
    return str(value)


def _filtered_items(params: Mapping[str, object | None]) -> list[tuple[str, str]]:
    return sorted(
        (key, serialize_scalar(value))
        for key, value in params.items()
        if value is not None
    )


def canonical_query_string(params: Mapping[str, object | None]) -> str:
    pairs = _filtered_items(params)
    return "&".join(
        f"{quote(key, safe='-_.~')}={quote(value, safe='-_.~')}"
        for key, value in pairs
    )


def signature_payload(
    instruction: str,
    params: Mapping[str, object | None],
    timestamp_ms: int,
    window_ms: int,
) -> str:
    components = [f"instruction={instruction}"]
    serialized = canonical_query_string(params)
    if serialized:
        components.append(serialized)
    components.append(f"timestamp={timestamp_ms}")
    components.append(f"window={window_ms}")
    return "&".join(components)
