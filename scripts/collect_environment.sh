#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "$0")" && pwd)/lib/common.sh"

require_macos
printf 'GemmaM5-1 FullStack hardware environment\n'
printf 'Collected UTC: %s\n' "$(date -u '+%Y-%m-%dT%H:%M:%SZ')"
printf 'Repository version: %s\n' "$(cat "$PROJECT_ROOT/VERSION")"
printf 'Architecture: %s\n' "$(uname -m)"
printf 'Chip: %s\n' "$(system_profiler SPHardwareDataType 2>/dev/null | awk -F': ' '/Chip:/{print $2; exit}')"
printf 'Unified memory bytes: %s\n' "$(sysctl -n hw.memsize)"
printf 'macOS: %s\n' "$(sw_vers -productVersion)"
printf 'Build: %s\n' "$(sw_vers -buildVersion)"
if command_exists lms; then
  printf '\nLM Studio CLI\n'
  lms --version 2>/dev/null || lms --help | head -n 2 || true
  printf '\nDownloaded candidate\n'
  lms ls --json --variants 2>/dev/null | python3 "$PROJECT_ROOT/scripts/summarize_lms_models.py" || true
  printf '\nLoaded models\n'
  lms ps --json 2>/dev/null | python3 "$PROJECT_ROOT/scripts/summarize_lms_models.py" || true
  printf '\nServer status\n'
  lms server status --json --quiet 2>/dev/null || lms server status || true
else
  printf 'lms: not found\n'
fi
if command_exists memory_pressure; then
  printf '\nMemory pressure\n'
  memory_pressure -Q || true
fi
printf '\nSwap usage\n'
sysctl vm.swapusage || true
