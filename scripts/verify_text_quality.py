#!/usr/bin/env python3
"""Fail closed on text corruption without requiring a Git worktree."""
from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
TEXT_NAMES = {'.editorconfig', '.gitattributes', '.gitignore', 'Makefile', 'VERSION'}
TEXT_SUFFIXES = {'.md', '.txt', '.json', '.yml', '.yaml', '.py', '.sh', '.conf', '.cff'}
SKIP_PARTS = {'.git', 'dist', 'artifacts', '__pycache__'}


def candidates(root: Path):
    for path in sorted((p for p in root.rglob('*') if p.is_file()), key=lambda p: p.relative_to(root).as_posix().encode()):
        relative = path.relative_to(root)
        if any(part in SKIP_PARTS for part in relative.parts):
            continue
        if path.name in TEXT_NAMES or path.suffix.lower() in TEXT_SUFFIXES:
            yield path


def validate(path: Path) -> list[str]:
    data = path.read_bytes()
    errors: list[str] = []
    if data.startswith(b'\xef\xbb\xbf'):
        errors.append('UTF-8 BOM is forbidden')
    if b'\x00' in data:
        errors.append('NUL byte is forbidden')
    if b'\r' in data:
        errors.append('CR/CRLF line endings are forbidden')
    try:
        text = data.decode('utf-8')
    except UnicodeDecodeError as exc:
        return [f'not valid UTF-8: {exc}']
    if text and not text.endswith('\n'):
        errors.append('missing final LF')
    for number, line in enumerate(text.splitlines(), 1):
        if line.rstrip(' \t') != line:
            errors.append(f'trailing whitespace on line {number}')
        for ch in line:
            code = ord(ch)
            if code < 32 and ch != '\t':
                errors.append(f'control character U+{code:04X} on line {number}')
                break
        if '\t' in line and path.suffix.lower() in {'.md', '.json', '.yml', '.yaml', '.cff'}:
            errors.append(f'tab character on line {number}')
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    args = parser.parse_args()
    root = args.root.resolve()
    failures: list[str] = []
    count = 0
    for path in candidates(root):
        count += 1
        for error in validate(path):
            failures.append(f'{path.relative_to(root).as_posix()}: {error}')
    if failures:
        for item in failures:
            print(f'ERROR: {item}', file=sys.stderr)
        return 1
    print(f'Text quality passed: {count} files')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
