#!/usr/bin/env python3
"""Validate GemmaM5 benchmark evidence without inventing measurements."""
from __future__ import annotations

import argparse
from datetime import datetime
import json
import re
from pathlib import Path
import sys
from typing import Any


def fail(message: str) -> None:
    print(f'ERROR: {message}', file=sys.stderr)
    raise SystemExit(1)


def require_object(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        fail(f'{label} must be a JSON object')
    return value


def require_positive_number(value: Any, label: str) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or value <= 0:
        fail(f'{label} must be a positive number')


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('path', type=Path)
    parser.add_argument('--expected-repository-version')
    args = parser.parse_args()
    try:
        data = json.loads(args.path.read_text(encoding='utf-8'))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f'cannot read benchmark JSON: {exc}')
    root = require_object(data, 'benchmark')
    if root.get('schema_version') != 1:
        fail('schema_version must be 1')
    status = root.get('status')
    if status not in {'not_measured', 'measured', 'rejected'}:
        fail('status must be not_measured, measured or rejected')
    repository_version = root.get('repository_version')
    if not isinstance(repository_version, str) or not repository_version.strip():
        fail('repository_version must be a non-empty string')
    if args.expected_repository_version and repository_version != args.expected_repository_version:
        fail(f'repository_version is {repository_version!r}, expected {args.expected_repository_version!r}')

    hardware = require_object(root.get('hardware'), 'hardware')
    if hardware.get('model') != 'MacBook Air' or hardware.get('chip') != 'Apple M5' or hardware.get('unified_memory_gb') != 24:
        fail('hardware must identify MacBook Air, Apple M5 and 24 GB')
    model = require_object(root.get('model'), 'model')
    exact = {
        'catalog_id': 'google/gemma-4-26b-a4b-qat',
        'format': 'gguf',
        'quantization': 'q4_0',
        'identifier': 'gemma4-local',
    }
    for key, expected in exact.items():
        if str(model.get(key, '')).lower() != expected.lower():
            fail(f'model.{key} must be {expected!r}')
    context = model.get('context_length')
    if not isinstance(context, int) or isinstance(context, bool) or not 1 <= context <= 262144:
        fail('model.context_length must be an integer between 1 and 262144')

    if status == 'not_measured':
        if root.get('date_utc') is not None:
            fail('date_utc must be null while status is not_measured')
        for section_name in ('software', 'memory', 'tests', 'performance', 'protocol'):
            section = require_object(root.get(section_name), section_name)
            non_null = [key for key, value in section.items() if value is not None]
            if non_null:
                fail(f'{section_name} must contain only null values while status is not_measured: {non_null}')
        print('Benchmark template verified: explicitly not measured.')
        return 0

    date_utc = root.get('date_utc')
    if not isinstance(date_utc, str):
        fail('date_utc is required for measured or rejected evidence')
    try:
        datetime.fromisoformat(date_utc.replace('Z', '+00:00'))
    except ValueError as exc:
        fail(f'date_utc is not ISO 8601: {exc}')
    if status == 'rejected':
        notes = root.get('notes')
        if not isinstance(notes, str) or not notes.strip():
            fail('rejected evidence requires explanatory notes')
        print('Rejected benchmark record verified as a documented non-result.')
        return 0

    protocol = require_object(root.get('protocol'), 'protocol')
    if not isinstance(protocol.get('profile_id'), str) or not protocol['profile_id'].strip():
        fail('protocol.profile_id is required for measured evidence')
    run_count = protocol.get('run_count')
    if isinstance(run_count, bool) or not isinstance(run_count, int) or run_count < 3:
        fail('protocol.run_count must be an integer of at least 3 for measured evidence')
    prompt_sha256 = protocol.get('prompt_sha256')
    if not isinstance(prompt_sha256, str) or re.fullmatch(r'[0-9a-f]{64}', prompt_sha256) is None:
        fail('protocol.prompt_sha256 must be a lowercase SHA-256 digest')
    if not isinstance(protocol.get('cold_start'), bool):
        fail('protocol.cold_start must be true or false for measured evidence')

    software = require_object(root.get('software'), 'software')
    for key in ('macos', 'macos_build', 'lm_studio', 'lms_cli', 'runtime'):
        if not isinstance(software.get(key), str) or not software[key].strip():
            fail(f'software.{key} is required for measured evidence')
    if not isinstance(model.get('model_key'), str) or 'q4_0' not in model['model_key'].lower():
        fail('model.model_key must identify the resolved Q4_0 variant')
    tests = require_object(root.get('tests'), 'tests')
    for key in ('text', 'vision', 'tool_schema', 'document', 'mixed_load_15_min'):
        if not isinstance(tests.get(key), bool):
            fail(f'tests.{key} must be true or false for measured evidence')
    performance = require_object(root.get('performance'), 'performance')
    for key in ('prompt_tokens', 'generated_tokens', 'time_to_first_token_seconds', 'tokens_per_second', 'prefill_tokens_per_second', 'decode_tokens_per_second'):
        require_positive_number(performance.get(key), f'performance.{key}')
    if not isinstance(performance.get('thermal_state'), str) or not performance['thermal_state'].strip():
        fail('performance.thermal_state is required for measured evidence')
    memory = require_object(root.get('memory'), 'memory')
    for key in ('pressure_before', 'pressure_loaded', 'pressure_peak'):
        if not isinstance(memory.get(key), str) or not memory[key].strip():
            fail(f'memory.{key} is required for measured evidence')
    for key in ('swap_before_gb', 'swap_after_gb'):
        value = memory.get(key)
        if isinstance(value, bool) or not isinstance(value, (int, float)) or value < 0:
            fail(f'memory.{key} must be a non-negative number')
    print('Measured benchmark evidence passed structural validation.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
