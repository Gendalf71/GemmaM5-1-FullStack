#!/usr/bin/env python3
"""Resolve one exact local Gemma 4 QAT Q4_0 LM Studio identity.

The current ``lms load --exact`` implementation matches its positional argument
against ``ModelInfo.path``.  ``ModelInfo.modelKey`` is a separate identity used
by the SDK and reported after loading.  This resolver therefore returns and
validates both fields as one indivisible pair.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass
from typing import Any, Iterable

TARGET = "gemma-4-26b-a4b"
TARGET_CATALOG = "google/gemma-4-26b-a4b-qat"
QUANTIZATION_TOKENS = ("q4_0", "q4-0", "q4 0")
MODEL_KEY_NAMES = ("modelKey", "model_key")
PATH_NAMES = ("path",)
EVIDENCE_NAMES = (
    "modelKey", "model_key", "path", "filename", "displayName", "display_name",
    "name", "format", "quantization", "selectedVariant", "selected_variant",
    "architecture", "type",
)


@dataclass(frozen=True, order=True)
class ModelIdentity:
    path: str
    model_key: str


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


def scalar_strings(value: Any) -> Iterable[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, (int, float, bool)):
        yield str(value)
    elif isinstance(value, dict):
        for child in value.values():
            yield from scalar_strings(child)
    elif isinstance(value, list):
        for child in value:
            yield from scalar_strings(child)


def first_nonempty_string(item: dict[str, Any], names: tuple[str, ...]) -> str | None:
    for name in names:
        value = item.get(name)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def candidate_strings(item: dict[str, Any]) -> list[str]:
    values: list[str] = []
    for name in EVIDENCE_NAMES:
        if name in item:
            values.extend(scalar_strings(item[name]))
    return values


def catalog_id_from_model_key(model_key: str) -> str:
    """Return the catalog part of an LM Studio modelKey.

    Variant-qualified keys such as ``google/gemma-4-26b-a4b-qat@q4_0``
    retain the exact publisher/name identity before the first ``@``.
    """
    return model_key.split("@", 1)[0].strip().lower()


def exact_evidence(item: dict[str, Any], path: str, model_key: str) -> bool:
    text = " ".join([path, model_key, *candidate_strings(item)]).lower()
    return (
        catalog_id_from_model_key(model_key) == TARGET_CATALOG
        and TARGET in text
        and "qat" in text
        and any(token in text for token in QUANTIZATION_TOKENS)
        and ("gguf" in text or path.lower().endswith(".gguf"))
    )


def is_local(item: dict[str, Any]) -> bool:
    # Current LM Studio ModelInfo uses null for a local model and a non-null
    # device identifier for LM Link.  Missing fields are tolerated only because
    # older machine-readable inventories did not always expose this property;
    # the actual load still passes --local and therefore fails closed.
    for name in ("deviceIdentifier", "device_identifier"):
        if name in item:
            return item[name] is None
    return True


def validate_identity_text(label: str, value: str) -> None:
    if not value:
        fail(f"resolved {label} is empty")
    if any(ord(character) < 32 or ord(character) == 127 for character in value):
        fail(f"resolved {label} contains a control character")


def choose_identities(data: Any) -> list[ModelIdentity]:
    identities: set[ModelIdentity] = set()
    for item in walk(data):
        path = first_nonempty_string(item, PATH_NAMES)
        model_key = first_nonempty_string(item, MODEL_KEY_NAMES)
        if path is None or model_key is None or not is_local(item):
            continue
        if not exact_evidence(item, path, model_key):
            continue
        validate_identity_text("model path", path)
        validate_identity_text("model key", model_key)
        identities.add(ModelIdentity(path=path, model_key=model_key))
    return sorted(identities)


def load_inventory() -> Any:
    completed = subprocess.run(
        ["lms", "ls", "--json"],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if completed.returncode != 0:
        fail(
            "lms ls --json failed; update LM Studio, launch it once, and retry. "
            f"CLI output: {completed.stderr.strip() or 'no diagnostic'}"
        )
    try:
        return json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        fail(f"lms ls --json returned invalid JSON: {exc}")


def resolve(data: Any, verify_model_key: str | None = None) -> ModelIdentity:
    identities = choose_identities(data)
    if verify_model_key is not None:
        requested = verify_model_key.strip()
        identities = [identity for identity in identities if identity.model_key == requested]
    if not identities:
        qualifier = f" matching MODEL_KEY {verify_model_key!r}" if verify_model_key else ""
        fail(
            "no unique local Gemma 4 26B A4B QAT GGUF Q4_0 identity"
            f"{qualifier} was found in lms ls --json"
        )
    if len(identities) != 1:
        rendered = "; ".join(
            f"path={identity.path!r}, modelKey={identity.model_key!r}" for identity in identities
        )
        fail(
            "multiple exact local Gemma 4 Q4_0 identities were found; remove or disambiguate "
            f"duplicates before loading: {rendered}"
        )
    return identities[0]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--verify-model-key",
        metavar="MODEL_KEY",
        help="accept only when the exact local identity reports this modelKey",
    )
    parser.add_argument(
        "--format",
        choices=("tsv", "json", "path", "model-key"),
        default="model-key",
    )
    args = parser.parse_args()
    try:
        identity = resolve(load_inventory(), args.verify_model_key)
    except FileNotFoundError:
        fail("lms is not available")

    if args.format == "path":
        print(identity.path)
    elif args.format == "model-key":
        print(identity.model_key)
    elif args.format == "tsv":
        if "\t" in identity.path or "\t" in identity.model_key:
            fail("resolved identity contains a tab and cannot be represented as TSV")
        print(f"{identity.path}\t{identity.model_key}")
    else:
        print(json.dumps({"path": identity.path, "modelKey": identity.model_key}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
