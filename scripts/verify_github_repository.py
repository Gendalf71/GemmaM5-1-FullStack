#!/usr/bin/env python3
"""Validate GitHub repository identity and publication postconditions."""
from __future__ import annotations

import argparse
import json
import sys


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--expected-name', required=True)
    parser.add_argument('--expected-visibility', choices=('public', 'private', 'internal'), required=True)
    parser.add_argument('--expected-description')
    parser.add_argument('--expected-default-branch')
    parser.add_argument('--expected-topic', action='append', default=[])
    args = parser.parse_args()
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError as exc:
        raise SystemExit(f'ERROR: invalid GitHub repository JSON: {exc}') from exc
    if not isinstance(data, dict):
        raise SystemExit('ERROR: GitHub repository inspection did not return an object')
    if data.get('nameWithOwner') != args.expected_name:
        raise SystemExit(f"ERROR: unexpected GitHub repository identity: {data.get('nameWithOwner')!r}")
    visibility = str(data.get('visibility', '')).lower()
    if visibility != args.expected_visibility:
        raise SystemExit(f'ERROR: repository visibility is {visibility!r}, expected {args.expected_visibility!r}')
    if data.get('isArchived') is not False:
        raise SystemExit('ERROR: GitHub repository is archived or archived state is unknown')
    if args.expected_description is not None and data.get('description') != args.expected_description:
        raise SystemExit('ERROR: GitHub repository description does not match the canonical description')
    if args.expected_default_branch is not None:
        ref = data.get('defaultBranchRef')
        branch = ref.get('name') if isinstance(ref, dict) else None
        if branch != args.expected_default_branch:
            raise SystemExit(f'ERROR: default branch is {branch!r}, expected {args.expected_default_branch!r}')
    if args.expected_topic:
        raw_topics = data.get('repositoryTopics')
        if not isinstance(raw_topics, list) or any(not isinstance(topic, str) for topic in raw_topics):
            raise SystemExit('ERROR: repository topics are missing or not a string list')
        actual_topics = set(raw_topics)
        missing_topics = sorted(set(args.expected_topic) - actual_topics)
        if missing_topics:
            raise SystemExit('ERROR: repository is missing canonical topics: ' + ', '.join(missing_topics))
    print('GitHub repository postcondition verified.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
