#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys
import urllib.request

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / 'scripts'))
from api_url_policy import require_api_token, validate_api_base_url  # noqa: E402


def post_json(url: str, payload: dict) -> dict:
    headers = {'Content-Type': 'application/json'}
    token = require_api_token()
    headers['Authorization'] = f'Bearer {token}'
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode('utf-8'),
        headers=headers,
        method='POST',
    )
    with urllib.request.urlopen(request, timeout=180) as response:
        return json.loads(response.read().decode('utf-8'))


def main() -> int:
    parser = argparse.ArgumentParser(description='Text request to the local LM Studio API')
    parser.add_argument('--base-url', default='http://127.0.0.1:1234/v1')
    parser.add_argument('--model', default='gemma4-local')
    parser.add_argument('--prompt', default='Explain the operational meaning of unified memory on Apple Silicon in five precise sentences.')
    parser.add_argument('--allow-remote-base-url', action='store_true', help='Explicitly allow sending the prompt and LM_API_TOKEN to a non-loopback endpoint.')
    args = parser.parse_args()
    try:
        base_url = validate_api_base_url(args.base_url, allow_remote=args.allow_remote_base_url)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    if args.allow_remote_base_url:
        print('WARNING: the prompt and LM_API_TOKEN, if set, may be sent to a remote endpoint.', file=sys.stderr)
    payload = {
        'model': args.model,
        'messages': [
            {'role': 'system', 'content': 'Answer accurately. State uncertainty explicitly.'},
            {'role': 'user', 'content': args.prompt},
        ],
        'temperature': 1.0,
        'top_p': 0.95,
        'max_tokens': 512,
    }
    result = post_json(f'{base_url}/chat/completions', payload)
    print(result['choices'][0]['message']['content'])
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
