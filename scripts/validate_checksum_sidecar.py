#!/usr/bin/env python3
"""Validate an exact one-line SHA-256 sidecar for one named archive."""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import re
import sys

LINE_RE = re.compile(r"^([0-9a-f]{64})  ([A-Za-z0-9._-]+)\n$")


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("sidecar", type=Path)
    parser.add_argument("archive", type=Path)
    args = parser.parse_args()
    sidecar = args.sidecar.resolve()
    archive = args.archive.resolve()
    try:
        raw = sidecar.read_text(encoding="ascii")
    except (OSError, UnicodeError) as exc:
        fail(f"cannot read ASCII checksum sidecar: {exc}")
    match = LINE_RE.fullmatch(raw)
    if not match:
        fail("checksum sidecar must be exactly one LF-terminated lowercase SHA-256 line")
    digest, basename = match.groups()
    if basename != archive.name:
        fail(f"checksum sidecar names {basename!r}, expected {archive.name!r}")
    try:
        actual = hashlib.sha256(archive.read_bytes()).hexdigest()
    except OSError as exc:
        fail(f"cannot read archive: {exc}")
    if digest != actual:
        fail(f"archive SHA-256 mismatch: expected {digest}, actual {actual}")
    print(f"Checksum sidecar verified: {sidecar.name} -> {archive.name} ({actual})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
