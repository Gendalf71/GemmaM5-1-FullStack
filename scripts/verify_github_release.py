#!/usr/bin/env python3
"""Validate the postconditions of a newly created GitHub Release."""
from __future__ import annotations

import argparse
import json
import sys


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--expected-tag', required=True)
    parser.add_argument('--archive-name', required=True)
    parser.add_argument('--sidecar-name', required=True)
    args = parser.parse_args()
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError as exc:
        raise SystemExit(f'ERROR: invalid GitHub Release JSON: {exc}') from exc
    if not isinstance(data, dict):
        raise SystemExit('ERROR: GitHub Release inspection did not return an object')
    if data.get('tagName') != args.expected_tag:
        raise SystemExit('ERROR: created GitHub Release has an unexpected tag')
    if data.get('isDraft') is not False or data.get('isPrerelease') is not False:
        raise SystemExit('ERROR: created GitHub Release is not a published stable release')
    assets = data.get('assets')
    if not isinstance(assets, list):
        raise SystemExit('ERROR: created GitHub Release assets are missing')
    names = {asset.get('name') for asset in assets if isinstance(asset, dict)}
    expected = {args.archive_name, args.sidecar_name}
    missing = sorted(expected - names)
    if missing:
        raise SystemExit('ERROR: created GitHub Release is missing assets: ' + ', '.join(missing))
    print('GitHub Release postcondition verified: tag, publication state and assets are exact.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
