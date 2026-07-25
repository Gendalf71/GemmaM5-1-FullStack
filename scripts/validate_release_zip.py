#!/usr/bin/env python3
"""Fail-closed structural and inventory validation for a release ZIP."""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path, PurePosixPath
import stat
import sys
import zipfile

FIXED_ZIP_TIME = (1980, 1, 1, 0, 0, 0)


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def safe_member(name: str) -> PurePosixPath:
    if not name or "\\" in name or name.startswith("/") or name.endswith("/") or "//" in name:
        fail(f"unsafe or non-file ZIP member: {name!r}")
    path = PurePosixPath(name)
    if any(part in {"", ".", ".."} for part in path.parts):
        fail(f"non-canonical ZIP member: {name!r}")
    if path.as_posix() != name:
        fail(f"non-canonical ZIP member spelling: {name!r}")
    return path


def manifest_paths(path: Path) -> list[str]:
    rows: list[str] = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        try:
            digest, relative = line.split("  ", 1)
        except ValueError:
            fail(f"malformed manifest line {number}")
        if len(digest) != 64 or any(ch not in "0123456789abcdef" for ch in digest):
            fail(f"malformed digest at manifest line {number}")
        safe_member(relative)
        rows.append(relative)
    if rows != sorted(rows, key=lambda value: value.encode("utf-8")) or len(rows) != len(set(rows)):
        fail("manifest paths must be unique and bytewise sorted")
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    parser.add_argument("--expected-root", required=True)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--repository-root", type=Path)
    args = parser.parse_args()

    expected_root = args.expected_root
    if "/" in expected_root or expected_root in {"", ".", ".."}:
        fail("expected root must be one canonical path component")
    manifest = args.manifest.resolve()
    repository_root = args.repository_root.resolve() if args.repository_root else None
    expected_relative = sorted(manifest_paths(manifest) + ["SHA256SUMS"], key=lambda value: value.encode("utf-8"))
    expected_names = [f"{expected_root}/{relative}" for relative in expected_relative]

    try:
        archive = zipfile.ZipFile(args.archive.resolve(), "r")
    except (OSError, zipfile.BadZipFile) as exc:
        fail(f"cannot open ZIP: {exc}")

    with archive:
        infos = archive.infolist()
        names = [info.filename for info in infos]
        for name in names:
            path = safe_member(name)
            if path.parts[0] != expected_root:
                fail(f"unexpected ZIP package root: {path.parts[0]!r}")
        if len(names) != len(set(names)):
            fail("duplicate ZIP member names are forbidden")
        if names != expected_names:
            missing = sorted(set(expected_names) - set(names))
            extra = sorted(set(names) - set(expected_names))
            fail(f"ZIP inventory differs from manifest; missing={missing}, extra={extra}")

        for info in infos:
            if info.flag_bits & 0x1:
                fail(f"encrypted ZIP member is forbidden: {info.filename}")
            if info.compress_type != zipfile.ZIP_STORED:
                fail(f"release member must use ZIP_STORED: {info.filename}")
            if info.date_time != FIXED_ZIP_TIME:
                fail(f"non-deterministic ZIP timestamp: {info.filename}")
            mode = (info.external_attr >> 16) & 0xFFFF
            if info.create_system != 3 or not stat.S_ISREG(mode):
                fail(f"ZIP member is not a Unix regular file: {info.filename}")

            relative = PurePosixPath(info.filename).relative_to(expected_root).as_posix()
            payload = archive.read(info)
            if relative == "SHA256SUMS":
                if payload != manifest.read_bytes():
                    fail("embedded SHA256SUMS differs from the supplied manifest")
                continue
            manifest_line = next(line for line in manifest.read_text(encoding="utf-8").splitlines() if line.endswith(f"  {relative}"))
            expected_digest = manifest_line[:64]
            if hashlib.sha256(payload).hexdigest() != expected_digest:
                fail(f"ZIP payload checksum mismatch: {relative}")
            if repository_root is not None:
                source = repository_root / relative
                if not source.is_file() or payload != source.read_bytes():
                    fail(f"ZIP payload differs from repository source: {relative}")
                if stat.S_IMODE(mode) != stat.S_IMODE(source.stat().st_mode):
                    fail(f"ZIP mode differs from repository source: {relative}")

    print(f"Release ZIP verified: {args.archive} ({len(expected_names)} files, root {expected_root})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
