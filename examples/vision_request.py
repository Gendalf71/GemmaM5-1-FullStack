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
from image_policy import image_data_url  # noqa: E402



def main() -> int:
    parser = argparse.ArgumentParser(description='Vision request to the local LM Studio API')
    parser.add_argument('--base-url', default='http://127.0.0.1:1234/v1')
    parser.add_argument('--model', default='gemma4-local')
    parser.add_argument('--image', type=Path, default=PROJECT_ROOT / 'tests' / 'fixtures' / 'vision_test.png')
    parser.add_argument('--allow-remote-base-url', action='store_true', help='Explicitly allow sending the image and LM_API_TOKEN to a non-loopback endpoint.')
    args = parser.parse_args()
    if not args.image.is_file():
        raise SystemExit(f'Image not found: {args.image}')
    try:
        base_url = validate_api_base_url(args.base_url, allow_remote=args.allow_remote_base_url)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    if args.allow_remote_base_url:
        print('WARNING: the selected image and LM_API_TOKEN, if set, may be sent to a remote endpoint.', file=sys.stderr)
    body = {
        'model': args.model,
        'messages': [{'role': 'user', 'content': [
            {'type': 'image_url', 'image_url': {'url': image_data_url(args.image)}},
            {'type': 'text', 'text': 'Read the image. Report the large number, the three labels and the geometric objects. Do not invent missing details.'},
        ]}],
        'temperature': 0.2,
        'max_tokens': 512,
    }
    headers = {'Content-Type': 'application/json'}
    token = require_api_token()
    headers['Authorization'] = f'Bearer {token}'
    request = urllib.request.Request(f'{base_url}/chat/completions', data=json.dumps(body).encode('utf-8'), headers=headers, method='POST')
    with urllib.request.urlopen(request, timeout=240) as response:
        result = json.loads(response.read().decode('utf-8'))
    print(result['choices'][0]['message']['content'])
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
