#!/usr/bin/env python3
"""Validate the versioned primary-source ledger; optionally probe URLs."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
EXACT_URLS = {
    'google-gemma4-model-card': 'https://ai.google.dev/gemma/docs/core/model_card_4',
    'lmstudio-target-model': 'https://lmstudio.ai/models/google/gemma-4-26b-a4b-qat',
    'lmstudio-gemma4-family': 'https://lmstudio.ai/models/gemma-4',
    'lmstudio-cli-load-source': 'https://github.com/lmstudio-ai/lms/blob/71bd99ccf882a0410cfd574ee220a99083608930/src/subcommands/load.ts',
    'lmstudio-server-status-source': 'https://github.com/lmstudio-ai/lms/blob/71bd99ccf882a0410cfd574ee220a99083608930/src/subcommands/server.ts',
    'lmstudio-authentication': 'https://lmstudio.ai/docs/developer/core/authentication',
    'lmstudio-parallel-requests': 'https://lmstudio.ai/docs/app/advanced/parallel-requests',
    'apple-macbook-air-identification': 'https://support.apple.com/en-us/102869',
    'apple-m5-air-13': 'https://support.apple.com/en-us/126320',
    'apple-m5-air-15': 'https://support.apple.com/en-us/126321',
    'github-host-fingerprints': 'https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/githubs-ssh-key-fingerprints',
    'github-actions-checkout': 'https://github.com/actions/checkout/releases/tag/v7.0.1',
    'github-actions-setup-python': 'https://github.com/actions/setup-python/releases/tag/v7.0.0',
    'lmstudio-0.4.11-changelog': 'https://lmstudio.ai/changelog/lmstudio-v0.4.11',
    'lmstudio-0.4.20-changelog': 'https://lmstudio.ai/changelog/lmstudio-v0.4.20',
    'lmstudio-system-requirements': 'https://lmstudio.ai/docs/app/system-requirements',
    'turbo-fieldfare-structural-reference': 'https://github.com/drumih/turbo-fieldfare',
}
IMMUTABLE = {
    'github-actions-checkout': '3d3c42e5aac5ba805825da76410c181273ba90b1',
    'github-actions-setup-python': '5fda3b95a4ea91299a34e894583c3862153e4b97',
}


def fail(message: str) -> None:
    print(f'ERROR: {message}', file=sys.stderr)
    raise SystemExit(1)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--live', action='store_true')
    parser.add_argument('--timeout', type=float, default=12.0)
    args = parser.parse_args()
    if args.timeout <= 0:
        parser.error('--timeout must be positive')
    version = (ROOT / 'VERSION').read_text(encoding='utf-8').strip()
    path = ROOT / f'docs/audit/external-evidence-{version}.json'
    record = json.loads(path.read_text(encoding='utf-8'))
    if record.get('repository_version') != version:
        fail('repository version drift')
    if record.get('retrieved_date') != '2026-07-24':
        fail('retrieval date drift')
    raw = record.get('sources', [])
    sources = {str(item.get('id')): item for item in raw}
    if len(sources) != len(raw):
        fail('duplicate or missing source id')
    if len(sources) < 25:
        fail('source inventory is unexpectedly small')
    for source_id, item in sources.items():
        url = item.get('url')
        claims = item.get('claims')
        if not isinstance(url, str) or not url.startswith('https://'):
            fail(f'non-HTTPS source URL: {source_id}')
        if not isinstance(claims, list) or not claims or not all(isinstance(x, str) and x.strip() for x in claims):
            fail(f'empty or invalid claim boundary: {source_id}')
    for source_id, url in EXACT_URLS.items():
        item = sources.get(source_id)
        if item is None or item.get('url') != url:
            fail(f'exact URL drift: {source_id}')
    for source_id, commit in IMMUTABLE.items():
        if sources[source_id].get('immutable_commit') != commit:
            fail(f'immutable commit drift: {source_id}')
    if args.live:
        user_agent = f'GemmaM5-1-FullStack/{version} source-audit'
        for source_id, item in sources.items():
            request = urllib.request.Request(str(item['url']), headers={'User-Agent': user_agent}, method='GET')
            try:
                with urllib.request.urlopen(request, timeout=args.timeout) as response:
                    if response.status >= 400:
                        fail(f'HTTP {response.status}: {source_id}')
            except Exception as exc:
                fail(f'live source failed: {source_id}: {exc}')
        print(f'Live source probes passed: {len(sources)}')
    else:
        print(f'Offline source ledger passed: {len(sources)}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
