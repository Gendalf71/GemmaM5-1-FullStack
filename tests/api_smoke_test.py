#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys
import urllib.error
import urllib.request

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / 'scripts'))
from api_url_policy import require_api_token, validate_api_base_url  # noqa: E402
from image_policy import image_data_url  # noqa: E402


def request_json(url: str, payload: dict | None = None, timeout: int = 180) -> dict:
    headers = {'Content-Type': 'application/json'}
    token = require_api_token()
    headers['Authorization'] = f'Bearer {token}'
    data = None if payload is None else json.dumps(payload).encode('utf-8')
    request = urllib.request.Request(url, data=data, headers=headers, method='GET' if data is None else 'POST')
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode('utf-8'))


def check_text(base_url: str, model: str) -> None:
    result = request_json(f'{base_url}/chat/completions', {'model': model, 'messages': [{'role': 'user', 'content': 'Reply with exactly: TEXT_OK'}], 'temperature': 0, 'max_tokens': 32})
    content = result['choices'][0]['message'].get('content', '')
    if 'TEXT_OK' not in content:
        raise AssertionError(f'Unexpected text response: {content!r}')
    print('PASS text generation')


def check_vision(base_url: str, model: str, image_path: Path) -> None:
    encoded_url = image_data_url(image_path)
    result = request_json(f'{base_url}/chat/completions', {
        'model': model,
        'messages': [{'role': 'user', 'content': [
            {'type': 'image_url', 'image_url': {'url': encoded_url}},
            {'type': 'text', 'text': 'Return only the large number shown in the image.'},
        ]}],
        'temperature': 0,
        'max_tokens': 32,
    }, timeout=240)
    content = result['choices'][0]['message'].get('content', '')
    if '417' not in content:
        raise AssertionError(f'Vision response did not contain 417: {content!r}')
    print('PASS image understanding')


def check_tool_schema(base_url: str, model: str) -> None:
    result = request_json(f'{base_url}/chat/completions', {
        'model': model,
        'messages': [{'role': 'user', 'content': 'Use the function to obtain the current memory pressure.'}],
        'tools': [{'type': 'function', 'function': {'name': 'read_memory_pressure', 'description': 'Read current memory pressure.', 'parameters': {'type': 'object', 'properties': {}, 'additionalProperties': False}}}],
        'tool_choice': {'type': 'function', 'function': {'name': 'read_memory_pressure'}},
        'max_tokens': 128,
    })
    message = result['choices'][0]['message']
    calls = message.get('tool_calls') or []
    if not calls or calls[0].get('function', {}).get('name') != 'read_memory_pressure':
        raise AssertionError(f'Expected tool call was not formed: {message!r}')
    print('PASS tool call formation without execution')


def main() -> int:
    parser = argparse.ArgumentParser(description='Acceptance smoke tests for a running local model')
    parser.add_argument('--base-url', default='http://127.0.0.1:1234/v1')
    parser.add_argument('--model', default='gemma4-local')
    parser.add_argument('--skip-vision', action='store_true')
    parser.add_argument('--allow-remote-base-url', action='store_true', help='Explicitly allow sending prompts, the fixture image and LM_API_TOKEN to a non-loopback endpoint.')
    args = parser.parse_args()
    try:
        base_url = validate_api_base_url(args.base_url, allow_remote=args.allow_remote_base_url)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    if args.allow_remote_base_url:
        print('WARNING: prompts, the fixture image and LM_API_TOKEN, if set, may be sent to a remote endpoint.', file=sys.stderr)
    try:
        models = request_json(f'{base_url}/models', timeout=30)
        print(f"PASS API model list: {len(models.get('data', []))} entries")
        check_text(base_url, args.model)
        if not args.skip_vision:
            check_vision(base_url, args.model, Path(__file__).resolve().parent / 'fixtures' / 'vision_test.png')
        check_tool_schema(base_url, args.model)
    except urllib.error.URLError as exc:
        raise SystemExit(f'API connection failed: {exc}') from exc
    print('All requested runtime smoke tests passed.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
