#!/usr/bin/env python3
"""Validate repository-local Git author identity without guessing user data."""
from __future__ import annotations

import argparse
import re
import sys

EMAIL_RE = re.compile(r"^[^@\s<>]+@[^@\s<>]+$")
PLACEHOLDER_TOKENS = ("your_", "example.com", "localhost", ".invalid", "changeme", "placeholder")


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--name", required=True)
    parser.add_argument("--email", required=True)
    args = parser.parse_args()

    name = args.name
    email = args.email
    if name != name.strip() or not name or len(name) > 200 or any(ord(ch) < 32 or ord(ch) == 127 for ch in name):
        fail("Git user.name is empty, padded, too long or contains control characters")
    if email != email.strip() or not EMAIL_RE.fullmatch(email) or len(email) > 254:
        fail("Git user.email is not a canonical single email address")
    lowered = f"{name}\n{email}".lower()
    if any(token in lowered for token in PLACEHOLDER_TOKENS):
        fail("Git identity still contains a placeholder or non-publishable address")
    print(f"Repository-local Git identity verified: {name} <{email}>")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
