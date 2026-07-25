#!/usr/bin/env python3
"""Extract stable target fields from ``system_profiler`` hardware JSON."""
from __future__ import annotations

import json
import sys
from typing import Any, Iterable


def walk(value: Any) -> Iterable[dict[str, Any]]:
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk(child)


def first_scalar(data: Any, names: tuple[str, ...]) -> str | None:
    lowered = {name.lower() for name in names}
    for item in walk(data):
        for key, value in item.items():
            if str(key).lower() in lowered and isinstance(value, (str, int, float)):
                text = str(value).strip()
                if text:
                    return text
    return None


def main() -> int:
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError as exc:
        raise SystemExit(f'ERROR: invalid system_profiler JSON: {exc}') from exc
    model_name = first_scalar(data, ('machine_name', 'model_name'))
    model_identifier = first_scalar(data, ('machine_model', 'model_identifier'))
    chip = first_scalar(data, ('chip_type', 'chip'))
    if not model_name or not model_identifier or not chip:
        raise SystemExit(
            'ERROR: system_profiler JSON did not contain machine_name, machine_model and chip_type'
        )
    print(json.dumps({
        'model_name': model_name,
        'model_identifier': model_identifier,
        'chip': chip,
    }, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
