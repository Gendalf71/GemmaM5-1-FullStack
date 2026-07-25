#!/usr/bin/env python3
"""Compatibility entry point: print the exact verified LM Studio modelKey."""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify-key", metavar="MODEL_KEY")
    args = parser.parse_args()
    command = [
        sys.executable,
        str(Path(__file__).with_name("resolve_model_identity.py")),
        "--format",
        "model-key",
    ]
    if args.verify_key:
        command.extend(["--verify-model-key", args.verify_key])
    return subprocess.run(command, check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())
