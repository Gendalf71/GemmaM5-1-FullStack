#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from typing import Any, Iterable

TARGET = "gemma-4-26b-a4b"
VISIBLE_KEYS = (
    "modelKey",
    "model_key",
    "key",
    "id",
    "identifier",
    "displayName",
    "display_name",
    "format",
    "quantization",
    "sizeBytes",
    "size_bytes",
    "contextLength",
    "context_length",
    "status",
)


def walk(value: Any) -> Iterable[dict[str, Any]]:
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk(child)


def searchable(item: dict[str, Any]) -> str:
    parts: list[str] = []
    for key, value in item.items():
        if key.lower() in {"path", "modelpath", "model_path"}:
            continue
        if isinstance(value, (str, int, float, bool)):
            parts.append(str(value))
    return " ".join(parts).lower()


def safe_subset(item: dict[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key in VISIBLE_KEYS:
        value = item.get(key)
        if isinstance(value, (str, int, float, bool, type(None), dict)):
            if key in item:
                result[key] = value
    return result


def main() -> int:
    try:
        data = json.load(sys.stdin)
    except Exception as exc:  # Environment collection remains best-effort.
        print(f"Unable to parse lms JSON: {exc}")
        return 0

    unique: set[str] = set()
    rows: list[dict[str, Any]] = []
    for item in walk(data):
        if TARGET not in searchable(item):
            continue
        subset = safe_subset(item)
        if not subset:
            continue
        encoded = json.dumps(subset, ensure_ascii=False, sort_keys=True)
        if encoded not in unique:
            unique.add(encoded)
            rows.append(subset)

    if not rows:
        print("No Gemma 4 26B A4B candidate found.")
        return 0

    for row in rows:
        print(json.dumps(row, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
