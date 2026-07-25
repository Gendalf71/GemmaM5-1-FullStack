#!/usr/bin/env python3
"""A deliberately narrow demonstration of tool calling.

The model may request the fixed tool ``read_memory_pressure``. The host program,
not the model, decides whether the request is valid and executes only the fixed
command ``/usr/bin/memory_pressure -Q``. Arbitrary shell strings are never
accepted. The endpoint is loopback-only unless a separate explicit remote opt-in
is supplied, because the tool result contains current host information.
"""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import urllib.request


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / 'scripts'))
from api_url_policy import require_api_token, validate_api_base_url  # noqa: E402


def validate_memory_pressure_call(calls: object) -> tuple[str, dict]:
    if not isinstance(calls, list) or len(calls) != 1:
        raise ValueError('Expected exactly one tool call.')
    call = calls[0]
    if not isinstance(call, dict):
        raise ValueError('Tool call must be a JSON object.')
    call_id = call.get('id')
    if not isinstance(call_id, str) or not call_id.strip():
        raise ValueError('Tool call ID must be a non-empty string.')
    function = call.get('function')
    if not isinstance(function, dict) or function.get('name') != 'read_memory_pressure':
        name = function.get('name') if isinstance(function, dict) else None
        raise ValueError(f'Rejected unapproved tool: {name}')
    raw_arguments = function.get('arguments', '{}')
    if not isinstance(raw_arguments, str):
        raise ValueError('Tool arguments must be a JSON-encoded object string.')
    try:
        arguments = json.loads(raw_arguments)
    except json.JSONDecodeError as exc:
        raise ValueError(f'Tool arguments are not valid JSON: {exc}') from exc
    if not isinstance(arguments, dict):
        raise ValueError('Tool arguments must decode to a JSON object.')
    if arguments:
        raise ValueError('Rejected unexpected tool arguments.')
    return call_id, arguments


def api_call(base_url: str, payload: dict) -> dict:
    headers = {'Content-Type': 'application/json'}
    token = require_api_token()
    headers['Authorization'] = f'Bearer {token}'
    request = urllib.request.Request(
        f'{base_url}/chat/completions',
        data=json.dumps(payload).encode('utf-8'),
        headers=headers,
        method='POST',
    )
    with urllib.request.urlopen(request, timeout=180) as response:
        return json.loads(response.read().decode('utf-8'))


def fixed_memory_pressure() -> str:
    completed = subprocess.run(
        ['/usr/bin/memory_pressure', '-Q'],
        check=False,
        capture_output=True,
        text=True,
        timeout=20,
    )
    return (completed.stdout + completed.stderr).strip()[:12000]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--base-url', default='http://127.0.0.1:1234/v1')
    parser.add_argument('--model', default='gemma4-local')
    parser.add_argument(
        '--allow-remote-base-url', action='store_true',
        help='Explicitly allow sending the local tool result to a non-loopback endpoint.',
    )
    args = parser.parse_args()

    try:
        base_url = validate_api_base_url(args.base_url, allow_remote=args.allow_remote_base_url)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    if args.allow_remote_base_url:
        print(
            'WARNING: the memory-pressure result may be sent to a remote endpoint.',
            file=sys.stderr,
        )

    tools = [{
        'type': 'function',
        'function': {
            'name': 'read_memory_pressure',
            'description': 'Read the current macOS memory pressure summary without changing the system.',
            'parameters': {'type': 'object', 'properties': {}, 'additionalProperties': False},
        },
    }]
    messages = [
        {'role': 'system', 'content': 'Use the supplied read-only tool when current memory pressure is needed.'},
        {'role': 'user', 'content': 'Check current memory pressure and explain whether loading a large local model is prudent.'},
    ]
    first = api_call(base_url, {'model': args.model, 'messages': messages, 'tools': tools, 'tool_choice': 'auto'})
    assistant_message = first['choices'][0]['message']
    calls = assistant_message.get('tool_calls') or []
    if not calls:
        print(assistant_message.get('content', 'No tool call and no text returned.'))
        return 0

    try:
        call_id, _arguments = validate_memory_pressure_call(calls)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc

    messages.append(assistant_message)
    messages.append({
        'role': 'tool',
        'tool_call_id': call_id,
        'content': fixed_memory_pressure(),
    })

    final = api_call(base_url, {'model': args.model, 'messages': messages})
    print(final['choices'][0]['message']['content'])
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
