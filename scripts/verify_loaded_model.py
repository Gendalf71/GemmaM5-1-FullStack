#!/usr/bin/env python3
"""Validate preconditions or postconditions for one managed LM Studio load."""
from __future__ import annotations

import argparse
import json
import sys
from typing import Any


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def load_payload() -> list[dict[str, Any]]:
    try:
        payload: Any = json.load(sys.stdin)
    except json.JSONDecodeError as exc:
        fail(f"lms ps --json returned invalid JSON: {exc}")
    if not isinstance(payload, list) or not all(isinstance(item, dict) for item in payload):
        fail("lms ps --json must return a JSON array of model objects")
    return payload


def describe(item: dict[str, Any]) -> str:
    return (
        f"identifier={item.get('identifier')!r}, path={item.get('path')!r}, "
        f"modelKey={item.get('modelKey')!r}, parallel={item.get('parallel')!r}"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", choices=("pre", "post"), default="post")
    parser.add_argument("--expected-model-path", required=True)
    parser.add_argument("--expected-model-key", required=True)
    parser.add_argument("--expected-identifier", required=True)
    parser.add_argument("--expected-parallel", required=True, type=int)
    args = parser.parse_args()
    payload = load_payload()

    by_identifier = [item for item in payload if item.get("identifier") == args.expected_identifier]
    by_path = [item for item in payload if item.get("path") == args.expected_model_path]
    by_key = [item for item in payload if item.get("modelKey") == args.expected_model_key]
    exact = [
        item
        for item in payload
        if item.get("identifier") == args.expected_identifier
        and item.get("path") == args.expected_model_path
        and item.get("modelKey") == args.expected_model_key
    ]
    relevant_ids = {id(item) for item in [*by_identifier, *by_path, *by_key]}
    exact_ids = {id(item) for item in exact}
    conflicts = [item for item in payload if id(item) in relevant_ids - exact_ids]

    if args.phase == "pre":
        if not by_identifier and not by_path and not by_key:
            print("ready")
            return 0
        if len(exact) == 1 and not conflicts and len(relevant_ids) == 1:
            model = exact[0]
            if model.get("parallel") != args.expected_parallel:
                fail(
                    "the exact model is already loaded with a conflicting concurrency setting: "
                    + describe(model)
                )
            print("already-loaded")
            return 0
        rendered = "; ".join(describe(item) for item in [*exact, *conflicts]) or "unknown conflict"
        fail(
            "a loaded identifier/path/modelKey conflict exists; unload it explicitly before the "
            f"managed load: {rendered}"
        )

    if len(exact) != 1:
        fail(
            "expected exactly one loaded instance with the exact identifier, path and modelKey; "
            f"found {len(exact)}"
        )
    if conflicts or len(relevant_ids) != 1:
        rendered = "; ".join(describe(item) for item in conflicts)
        fail(f"loaded identity is not unique; conflicting instances: {rendered}")
    model = exact[0]
    if model.get("parallel") != args.expected_parallel:
        fail(
            f"loaded model reports parallel={model.get('parallel')!r}; "
            f"expected {args.expected_parallel}"
        )
    print(
        "Loaded model verified: "
        f"{args.expected_identifier} -> path={args.expected_model_path}, "
        f"modelKey={args.expected_model_key}, parallel={args.expected_parallel}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
