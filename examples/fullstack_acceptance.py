#!/usr/bin/env python3
"""Bounded full-stack acceptance example for document, vision and one fixed tool.

This is not a general RAG engine. It sends a reviewed local UTF-8 excerpt and one
image to the OpenAI-compatible localhost endpoint, then demonstrates the same
fixed, host-validated ``read_memory_pressure`` tool used by ``safe_tool_call.py``.
No model-provided shell string is executed.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys
import urllib.request

PROJECT_ROOT = Path(__file__).resolve().parents[1]
EXAMPLES_DIR = Path(__file__).resolve().parent
DEFAULT_DOCUMENT = PROJECT_ROOT / 'tests' / 'fixtures' / 'document_test.md'
DEFAULT_IMAGE = PROJECT_ROOT / 'tests' / 'fixtures' / 'vision_test.png'
MAX_DOCUMENT_BYTES = 131_072
MAX_IMAGE_BYTES = 12 * 1024 * 1024
MAX_DOCUMENT_CHARACTERS = 24_000

sys.path.insert(0, str(PROJECT_ROOT / 'scripts'))
sys.path.insert(0, str(EXAMPLES_DIR))
from api_url_policy import require_api_token, validate_api_base_url  # noqa: E402
from image_policy import image_data_url as validated_image_data_url  # noqa: E402
from safe_tool_call import (  # noqa: E402
    api_call,
    fixed_memory_pressure,
    validate_memory_pressure_call,
)


def read_bounded_text(path: Path) -> str:
    if not path.is_file():
        raise SystemExit(f'Document not found: {path}')
    size = path.stat().st_size
    if size > MAX_DOCUMENT_BYTES:
        raise SystemExit(f'Document exceeds {MAX_DOCUMENT_BYTES} bytes: {path}')
    try:
        text = path.read_text(encoding='utf-8')
    except UnicodeError as exc:
        raise SystemExit(f'Document must be UTF-8 text: {path}: {exc}') from exc
    return text[:MAX_DOCUMENT_CHARACTERS]


def image_data_url(path: Path) -> str:
    try:
        return validated_image_data_url(path, max_bytes=MAX_IMAGE_BYTES)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc


def post_json(base_url: str, payload: dict) -> dict:
    headers = {'Content-Type': 'application/json'}
    token = require_api_token()
    headers['Authorization'] = f'Bearer {token}'
    request = urllib.request.Request(
        f'{base_url}/chat/completions',
        data=json.dumps(payload).encode('utf-8'),
        headers=headers,
        method='POST',
    )
    with urllib.request.urlopen(request, timeout=300) as response:
        return json.loads(response.read().decode('utf-8'))


def run_tool_phase(base_url: str, model: str) -> str:
    tools = [{
        'type': 'function',
        'function': {
            'name': 'read_memory_pressure',
            'description': 'Read the current macOS memory pressure summary without changing the system.',
            'parameters': {'type': 'object', 'properties': {}, 'additionalProperties': False},
        },
    }]
    messages = [
        {'role': 'system', 'content': 'Use only the supplied read-only tool when current memory pressure is needed.'},
        {'role': 'user', 'content': 'Read current memory pressure and state whether another large local workload should start.'},
    ]
    first = api_call(base_url, {'model': model, 'messages': messages, 'tools': tools, 'tool_choice': 'auto'})
    assistant_message = first['choices'][0]['message']
    calls = assistant_message.get('tool_calls') or []
    if not calls:
        return assistant_message.get('content', 'No tool call and no text returned.')
    call_id, _arguments = validate_memory_pressure_call(calls)
    messages.append(assistant_message)
    messages.append({'role': 'tool', 'tool_call_id': call_id, 'content': fixed_memory_pressure()})
    final = api_call(base_url, {'model': model, 'messages': messages})
    return final['choices'][0]['message']['content']


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-url', default='http://127.0.0.1:1234/v1')
    parser.add_argument('--model', default='gemma4-local')
    parser.add_argument('--document', type=Path, default=DEFAULT_DOCUMENT)
    parser.add_argument('--image', type=Path, default=DEFAULT_IMAGE)
    parser.add_argument('--skip-tool', action='store_true')
    parser.add_argument(
        '--allow-remote-base-url', action='store_true',
        help='Explicitly allow sending the selected document, image, tool result and token to a remote endpoint.',
    )
    args = parser.parse_args()
    try:
        base_url = validate_api_base_url(args.base_url, allow_remote=args.allow_remote_base_url)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    if args.allow_remote_base_url:
        print('WARNING: selected local evidence and LM_API_TOKEN may leave this Mac.', file=sys.stderr)

    document = read_bounded_text(args.document)
    payload = {
        'model': args.model,
        'messages': [{
            'role': 'user',
            'content': [
                {'type': 'image_url', 'image_url': {'url': image_data_url(args.image)}},
                {'type': 'text', 'text': (
                    'Cross-check the image against the following reviewed local document excerpt. '
                    'Report the large number in the image, the release target in the document, and any contradiction. '
                    'Do not infer facts that are absent.\n\n'
                    f'DOCUMENT {args.document.name}:\n{document}'
                )},
            ],
        }],
        'temperature': 0.2,
        'max_tokens': 700,
    }
    result = post_json(base_url, payload)
    print('DOCUMENT + VISION')
    print(result['choices'][0]['message']['content'])
    if not args.skip_tool:
        print('\nCONTROLLED TOOL')
        print(run_tool_phase(base_url, args.model))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
