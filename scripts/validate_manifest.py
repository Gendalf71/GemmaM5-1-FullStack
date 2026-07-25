#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path, PurePosixPath
import re
import sys

LINE_RE = re.compile(r"^([0-9a-f]{64})  ([A-Za-z0-9._/-]+)$")


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def validate_path(relative: str) -> None:
    if relative == "SHA256SUMS":
        fail("SHA256SUMS must not contain a checksum entry for itself")
    if relative.startswith("/") or relative.endswith("/") or "//" in relative:
        fail(f"unsafe release-manifest path: {relative}")
    parts = relative.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        fail(f"non-canonical release-manifest path: {relative}")
    if PurePosixPath(relative).as_posix() != relative:
        fail(f"non-canonical release-manifest path: {relative}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate and print a canonical SHA256SUMS inventory")
    parser.add_argument("manifest", nargs="?", type=Path, default=Path("SHA256SUMS"))
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--require-files", action="store_true")
    parser.add_argument("--print-paths", action="store_true")
    args = parser.parse_args()

    manifest = args.manifest.resolve()
    root = args.root.resolve()
    try:
        lines = manifest.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        fail(f"cannot read checksum manifest: {exc}")

    if not lines:
        fail("checksum manifest is empty")

    paths: list[str] = []
    for number, line in enumerate(lines, 1):
        match = LINE_RE.fullmatch(line)
        if not match:
            fail(f"malformed SHA256SUMS line {number}")
        relative = match.group(2)
        validate_path(relative)
        candidate = root.joinpath(*relative.split("/"))
        try:
            candidate.resolve().relative_to(root)
        except ValueError:
            fail(f"release-manifest path escapes the repository root: {relative}")
        if candidate.is_symlink():
            fail(f"symbolic links are not permitted in the release manifest: {relative}")
        if args.require_files and not candidate.is_file():
            fail(f"manifest file is missing: {relative}")
        paths.append(relative)

    seen: set[str] = set()
    duplicates: set[str] = set()
    for path in paths:
        if path in seen:
            duplicates.add(path)
        else:
            seen.add(path)
    if duplicates:
        fail("duplicate release-manifest path(s): " + ", ".join(sorted(duplicates)))
    if paths != sorted(paths):
        fail("SHA256SUMS paths must be sorted in bytewise lexical order")

    if args.print_paths:
        print("\n".join(paths))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
