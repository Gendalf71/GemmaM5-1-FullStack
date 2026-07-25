#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from typing import Any, Iterable

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
from resolve_model_identity import resolve as resolve_model_identity

TARGET = "gemma-4-26b-a4b"
SAFE_KEYS = (
    "modelKey", "model_key", "key", "id", "identifier",
    "displayName", "display_name", "format", "quantization",
    "sizeBytes", "size_bytes", "contextLength", "context_length", "status",
)


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


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
        if key.lower() in {"path", "modelpath", "model_path", "downloadpath", "download_path"}:
            continue
        if isinstance(value, (str, int, float, bool)):
            parts.append(str(value))
    return " ".join(parts).lower()


def clean_quantization(value: Any) -> Any:
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, dict):
        return {
            str(key): clean_quantization(child)
            for key, child in value.items()
            if str(key).lower() not in {"path", "modelpath", "model_path"}
            and isinstance(child, (str, int, float, bool, type(None)))
        }
    return None


def safe_subset(item: dict[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key in SAFE_KEYS:
        if key not in item:
            continue
        value = item[key]
        if key == "quantization":
            value = clean_quantization(value)
        if isinstance(value, (str, int, float, bool, type(None), dict)):
            result[key] = value
    return result


def select_candidates(data: Any) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in walk(data):
        if TARGET not in searchable(item):
            continue
        subset = safe_subset(item)
        if not subset:
            continue
        encoded = json.dumps(subset, ensure_ascii=False, sort_keys=True)
        if encoded in seen:
            continue
        seen.add(encoded)
        rows.append(subset)
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description="Write a privacy-filtered GemmaM5 model provenance record")
    parser.add_argument("--inventory", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--repository-version", required=True)
    parser.add_argument("--catalog-id", required=True)
    parser.add_argument("--required-quantization", required=True)
    parser.add_argument("--resolved-model-key", required=True)
    parser.add_argument("--resolved-model-path", required=True)
    parser.add_argument("--collected-utc")
    args = parser.parse_args()

    if args.catalog_id != "google/gemma-4-26b-a4b-qat":
        fail("catalog ID does not match the supported profile")
    if args.required_quantization.lower() != "q4_0":
        fail("required quantization does not match Q4_0")
    try:
        inventory = json.loads(args.inventory.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"cannot read LM Studio inventory JSON: {exc}")
    try:
        resolved = resolve_model_identity(inventory, args.resolved_model_key)
    except SystemExit as exc:
        fail(f"inventory does not prove the exact model identity: exit {exc.code}")
    if resolved.path != args.resolved_model_path or resolved.model_key != args.resolved_model_key:
        fail("resolved path/modelKey arguments do not match the exact inventory identity")
    candidates = select_candidates(inventory)
    if not candidates:
        fail("LM Studio inventory contains no Gemma 4 26B A4B candidate")

    collected = args.collected_utc or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    payload = {
        "schema_version": 1,
        "collected_utc": collected,
        "repository_version": args.repository_version,
        "catalog_id": args.catalog_id,
        "required_quantization": "q4_0",
        "resolved_model_key": args.resolved_model_key,
        "resolved_model_path_sha256": hashlib.sha256(args.resolved_model_path.encode("utf-8")).hexdigest(),
        "inventory_candidates": candidates,
        "privacy": {
            "local_paths_included": False,
            "credentials_included": False,
        },
        "scope": "Repeatable configuration evidence; not a cryptographic digest of external model weights.",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
