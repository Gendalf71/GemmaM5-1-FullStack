#!/usr/bin/env python3
"""Validate the terminal release-assurance record and all cross-links."""
from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
version = (ROOT / 'VERSION').read_text(encoding='utf-8').strip()
path = ROOT / f'docs/audit/release-assurance-{version}.json'


def fail(message: str) -> None:
    print(f'ERROR: {message}', file=sys.stderr)
    raise SystemExit(1)


try:
    record = json.loads(path.read_text(encoding='utf-8'))
    matrix = json.loads((ROOT / f'docs/audit/iteration-matrix-{version}.json').read_text(encoding='utf-8'))
    ledger = json.loads((ROOT / f'docs/audit/revision-ledger-{version}.json').read_text(encoding='utf-8'))
    evidence = json.loads((ROOT / f'docs/audit/external-evidence-{version}.json').read_text(encoding='utf-8'))
except Exception as exc:
    fail(str(exc))

expected = {
    'repository_version': version,
    'terminal_release': version,
    'critical_findings_remaining': 0,
    'major_findings_remaining': 0,
    'hardware_benchmark_status': 'not_measured',
    'runtime_screenshot_status': 'not_captured',
    'owner_acceptance_required': True,
}
for key, value in expected.items():
    if record.get(key) != value:
        fail(f'assurance drift: {key}')

matrix_summary = record.get('matrix', {})
for key in ('outer_cycles', 'domains_per_cycle', 'total_control_passes', 'state_digest_sha256'):
    if matrix_summary.get(key) != matrix.get(key):
        fail(f'assurance matrix cross-link drift: {key}')
if matrix.get('summary', {}).get('failed') != 0 or matrix.get('summary', {}).get('critical_findings_remaining') != 0:
    fail('matrix is not closed')
if record.get('revision_count') != len(ledger.get('revisions', [])):
    fail('revision_count cross-link drift')
if record.get('external_source_count') != len(evidence.get('sources', [])):
    fail('external_source_count cross-link drift')
if record.get('unit_tests_expected') != 91:
    fail('unit_tests_expected drift')
if ledger.get('target_version') != version or ledger.get('summary', {}).get('critical_findings_remaining') != 0:
    fail('revision ledger is not closed')
if evidence.get('repository_version') != version:
    fail('external evidence version drift')
print(f'Release assurance passed: {path}')
