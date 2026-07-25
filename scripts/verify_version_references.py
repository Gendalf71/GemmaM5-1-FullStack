#!/usr/bin/env python3
"""Fail closed when operational documentation names a stale release version."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys

CANONICAL_VERSION = re.compile(r'^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$')
RELEASE_REFERENCE = re.compile(r'(?<![0-9A-Za-z])v?(1\.1\.\d+)(?![0-9A-Za-z])')
OPERATIONAL_FILES = (
    'README.md',
    'CITATION.cff',
    'benchmarks/m5-air-24gb.template.json',
    'docs/RELEASE.md',
    'docs/INSTALL_MODEL.md',
    'docs/SCREENSHOTS.md',
    'docs/INSTALL_GITHUB_SSH.md',
    'docs/COMPATIBILITY.md',
    'docs/BENCHMARK_PROTOCOL.md',
    'docs/BACKEND_PORTABILITY.md',
    'docs/ACCEPTANCE_CHECKLIST.md',
    'docs/GITHUB_METADATA.md',
    'docs/THREAT_MODEL.md',
    'SUPPORT.md',
    'docs/assets/assets-manifest.json',
    'docs/screenshot-manifest.template.json',
    'docs/ru/RELEASE.md',
    'docs/ru/INSTALL_MODEL.md',
    'docs/ru/SCREENSHOTS.md',
    'docs/ru/INSTALL_GITHUB_SSH.md',
    'docs/ru/COMPATIBILITY.md',
    'docs/ru/BENCHMARK_PROTOCOL.md',
    'docs/ru/BACKEND_PORTABILITY.md',
    'docs/ru/ACCEPTANCE_CHECKLIST.md',
    'docs/ru/GITHUB_METADATA.md',
    'docs/ru/THREAT_MODEL.md',
)


def fail(message: str) -> None:
    print(f'ERROR: {message}', file=sys.stderr)
    raise SystemExit(1)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    root = args.root.resolve()
    try:
        version = (root / 'VERSION').read_text(encoding='utf-8').strip()
    except OSError as exc:
        fail(f'cannot read VERSION: {exc}')
    if not CANONICAL_VERSION.fullmatch(version):
        fail(f'VERSION is not canonical X.Y.Z: {version!r}')

    stale: list[str] = []
    missing: list[str] = []
    for relative in OPERATIONAL_FILES:
        path = root / relative
        if not path.is_file():
            missing.append(relative)
            continue
        text = path.read_text(encoding='utf-8')
        references = {match.group(1) for match in RELEASE_REFERENCE.finditer(text)}
        wrong = sorted(reference for reference in references if reference != version)
        if wrong:
            stale.append(f'{relative}: {", ".join(wrong)}')
        if relative != 'CITATION.cff' and relative != 'benchmarks/m5-air-24gb.template.json' and version not in text:
            missing.append(f'{relative} (does not name {version})')
    if stale:
        fail('stale release references: ' + '; '.join(stale))
    if missing:
        fail('missing operational version evidence: ' + '; '.join(missing))

    citation = (root / 'CITATION.cff').read_text(encoding='utf-8')
    if f'version: {version}' not in citation:
        fail('CITATION.cff does not contain the exact release version')
    try:
        benchmark = json.loads((root / 'benchmarks/m5-air-24gb.template.json').read_text(encoding='utf-8'))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f'cannot parse benchmark template: {exc}')
    if benchmark.get('repository_version') != version:
        fail('benchmark repository_version does not match VERSION')
    changelog = (root / 'CHANGELOG.md').read_text(encoding='utf-8')
    if changelog.count(f'## {version} ') != 1:
        fail('CHANGELOG must contain exactly one current-version heading')
    print(f'Operational version references verified: {version}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
