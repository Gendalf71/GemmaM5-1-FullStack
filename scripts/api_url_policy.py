#!/usr/bin/env python3
"""Shared fail-closed URL policy for LM Studio example clients."""
from __future__ import annotations

import argparse
import ipaddress
import os
from urllib.parse import urlsplit



def require_api_token(value: str | None = None) -> str:
    """Require a canonical token because the audited profile enables API auth."""
    token = os.getenv('LM_API_TOKEN') if value is None else value
    if token is None or not token:
        raise ValueError('LM_API_TOKEN is required by the audited authenticated API profile.')
    if token != token.strip():
        raise ValueError('LM_API_TOKEN must not contain leading or trailing whitespace.')
    if any(ord(ch) < 33 or ord(ch) == 127 for ch in token):
        raise ValueError('LM_API_TOKEN contains whitespace or control characters.')
    if len(token.encode('utf-8')) > 4096:
        raise ValueError('LM_API_TOKEN is unexpectedly large.')
    return token


def validate_http_api_base_url(
    value: str,
    *,
    required_suffix: str,
    allow_remote: bool = False,
) -> str:
    normalized = value.strip().rstrip('/')
    if not normalized:
        raise ValueError('Base URL must not be empty.')
    if any(ord(ch) < 32 or ord(ch) == 127 for ch in normalized):
        raise ValueError('Base URL must not contain control characters.')
    parsed = urlsplit(normalized)
    if parsed.scheme not in {'http', 'https'} or not parsed.hostname:
        raise ValueError('Base URL must be an absolute HTTP or HTTPS URL.')
    if parsed.username is not None or parsed.password is not None:
        raise ValueError('Base URL must not contain embedded credentials.')
    if parsed.query or parsed.fragment:
        raise ValueError('Base URL must not contain a query string or fragment.')
    try:
        port = parsed.port
    except ValueError as exc:
        raise ValueError(f'Base URL contains an invalid port: {exc}') from exc
    if port is not None and not 1 <= port <= 65535:
        raise ValueError('Base URL port must be between 1 and 65535.')
    if parsed.path != required_suffix:
        raise ValueError(f'Base URL path must be exactly {required_suffix}.')
    if allow_remote and parsed.scheme != 'https':
        raise ValueError(
            'A deliberately remote endpoint must use HTTPS so prompts, images and '
            'LM_API_TOKEN are not sent in clear text.'
        )
    if not allow_remote:
        try:
            address = ipaddress.ip_address(parsed.hostname)
        except ValueError as exc:
            raise ValueError(
                'This client accepts a numeric loopback endpoint only by default. '
                'Use 127.0.0.1 or pass --allow-remote-base-url only after reviewing '
                'request-data and token disclosure.'
            ) from exc
        if not address.is_loopback:
            raise ValueError(
                'Refusing to send request data or LM_API_TOKEN to a non-loopback endpoint. '
                'Pass --allow-remote-base-url only for a deliberately reviewed remote host.'
            )
    return normalized


def validate_api_base_url(value: str, *, allow_remote: bool = False) -> str:
    return validate_http_api_base_url(
        value,
        required_suffix='/v1',
        allow_remote=allow_remote,
    )


def validate_native_api_base_url(value: str, *, allow_remote: bool = False) -> str:
    return validate_http_api_base_url(
        value,
        required_suffix='/api/v1',
        allow_remote=allow_remote,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description='Validate an LM Studio API base URL')
    parser.add_argument('value')
    parser.add_argument('--kind', choices=('openai', 'native'), default='openai')
    parser.add_argument('--allow-remote-base-url', action='store_true')
    args = parser.parse_args()
    validator = validate_api_base_url if args.kind == 'openai' else validate_native_api_base_url
    try:
        print(validator(args.value, allow_remote=args.allow_remote_base_url))
    except ValueError as exc:
        parser.exit(1, f'ERROR: {exc}\n')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
