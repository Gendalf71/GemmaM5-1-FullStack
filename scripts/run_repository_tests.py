#!/usr/bin/env python3
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
from pathlib import Path
import signal
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]


def flatten(suite: unittest.TestSuite):
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            yield from flatten(item)
        else:
            yield item


def discover_test_ids() -> list[str]:
    loader = unittest.TestLoader()
    suite = loader.discover(str(ROOT / 'tests'), pattern='test_*.py')
    result: list[str] = []
    for test in sorted(flatten(suite), key=lambda item: item.id()):
        test_id = test.id()
        result.append(test_id if test_id.startswith('tests.') else f'tests.{test_id}')
    return result


def terminate_process_group(process: subprocess.Popen[str]) -> None:
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    process.wait()


def run_isolated(test_id: str, timeout: float) -> tuple[int, str, str, bool]:
    process = subprocess.Popen(
        [sys.executable, '-m', 'unittest', '-q', test_id],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        start_new_session=True,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
    )
    try:
        stdout, stderr = process.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        terminate_process_group(process)
        return 124, '', f'exceeded {timeout:g} seconds', True
    return process.returncode, stdout, stderr, False


def main() -> int:
    parser = argparse.ArgumentParser(
        description='Run repository regressions in isolated, bounded process groups'
    )
    parser.add_argument(
        '--timeout', type=float,
        default=float(os.environ.get('GEMMAM5_TEST_TIMEOUT', '60')),
        help='maximum seconds allowed for each individual test (default: 60)',
    )
    parser.add_argument(
        '--jobs', type=int,
        default=int(os.environ.get('GEMMAM5_TEST_JOBS', '4')),
        help='maximum isolated tests running concurrently (default: 4)',
    )
    parser.add_argument(
        '--batch-size', type=int,
        default=int(os.environ.get('GEMMAM5_TEST_BATCH_SIZE', '11')),
        help='maximum tests submitted to one executor batch (default: 11)',
    )
    parser.add_argument('--from-index', type=int, default=1, help='first one-based test index')
    parser.add_argument('--to-index', type=int, help='last one-based test index (inclusive)')
    args = parser.parse_args()
    if args.timeout <= 0:
        parser.error('--timeout must be positive')
    if args.jobs <= 0:
        parser.error('--jobs must be positive')
    if args.batch_size <= 0:
        parser.error('--batch-size must be positive')

    tests = discover_test_ids()
    if not tests:
        print('ERROR: no repository tests were discovered', file=sys.stderr)
        return 2
    end = len(tests) if args.to_index is None else args.to_index
    if args.from_index < 1 or end < args.from_index or end > len(tests):
        parser.error(f'test index range must satisfy 1 <= from <= to <= {len(tests)}')
    selected = tests[args.from_index - 1:end]

    for batch_offset in range(0, len(selected), args.batch_size):
        batch = selected[batch_offset:batch_offset + args.batch_size]
        batch_first = args.from_index + batch_offset
        outcomes: dict[int, tuple[str, tuple[int, str, str, bool]]] = {}
        with ThreadPoolExecutor(max_workers=min(args.jobs, len(batch))) as executor:
            futures = {
                executor.submit(run_isolated, test_id, args.timeout): (absolute_index, test_id)
                for absolute_index, test_id in enumerate(batch, start=batch_first)
            }
            for future in as_completed(futures):
                absolute_index, test_id = futures[future]
                outcomes[absolute_index] = (test_id, future.result())

        for absolute_index in range(batch_first, batch_first + len(batch)):
            test_id, (returncode, stdout, stderr, timed_out) = outcomes[absolute_index]
            print(f'[{absolute_index:02d}/{len(tests):02d}] {test_id}', flush=True)
            if timed_out:
                print(f'ERROR: timeout: {test_id}: {stderr}', file=sys.stderr)
                return 124
            if returncode != 0:
                print(f'ERROR: test failure: {test_id}', file=sys.stderr)
                if stdout:
                    print(stdout, file=sys.stderr, end='' if stdout.endswith('\n') else '\n')
                if stderr:
                    print(stderr, file=sys.stderr, end='' if stderr.endswith('\n') else '\n')
                return returncode or 1

    print(
        f'Repository unit checks: {len(selected)} passed '
        f'(indices {args.from_index}-{end} of {len(tests)}, jobs={min(args.jobs, len(selected))}, '
        f'batch_size={args.batch_size})'
    )
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
