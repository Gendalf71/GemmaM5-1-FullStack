#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "$0")" && pwd)/lib/common.sh"

output_dir="$PROJECT_ROOT/artifacts"
while [ "$#" -gt 0 ]; do
  case "$1" in
    --output-dir)
      shift
      [ "$#" -gt 0 ] || fail "--output-dir requires a path"
      output_dir="$1"
      ;;
    -h|--help)
      printf '%s\n' 'Usage: scripts/capture_hardware_report.sh [--output-dir PATH]'
      exit 0
      ;;
    *) fail "Unknown argument: $1" ;;
  esac
  shift
done

require_macos
umask 077
mkdir -p "$output_dir"
output_dir="$(cd "$output_dir" && pwd)"
timestamp="$(date -u '+%Y%m%dT%H%M%SZ')"
report="$output_dir/hardware-report-$timestamp.txt"
[ ! -e "$report" ] || fail "Refusing to overwrite existing report: $report"
{
  printf 'GemmaM5-1 FullStack owner hardware report\n'
  printf 'Evidence status: local capture; review and redact before publication\n\n'
  "$PROJECT_ROOT/scripts/collect_environment.sh"
  printf '\nRequired next steps\n'
  printf '%s\n' '- Run the 4K, 8K and optional 32K protocol in docs/BENCHMARK_PROTOCOL.md.'
  printf '%s\n' '- Populate benchmark JSON only with directly measured values.'
  printf '%s\n' '- Do not publish this raw file before checking it for local identifiers.'
} > "$report"
chmod 600 "$report"
printf 'Hardware report written with owner-only permissions: %s\n' "$report"
