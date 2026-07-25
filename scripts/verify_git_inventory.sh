#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "$0")" && pwd)/lib/common.sh"

require_clean=0
while [ "$#" -gt 0 ]; do
  case "$1" in
    --require-clean) require_clean=1 ;;
    -h|--help)
      printf '%s\n' 'Usage: scripts/verify_git_inventory.sh [--require-clean]'
      exit 0
      ;;
    *) fail "Unknown argument: $1" ;;
  esac
  shift
done

require_command git
cd "$PROJECT_ROOT"
git rev-parse --is-inside-work-tree >/dev/null 2>&1 || fail "This directory is not a Git working tree."
git rev-parse --verify HEAD >/dev/null 2>&1 || fail "Git inventory verification requires an existing commit."
[ -f SHA256SUMS ] || fail "SHA256SUMS is missing."

allowed_file="$(mktemp "${TMPDIR:-/tmp}/gemmam5-git-allowed.XXXXXX")"
tracked_file="$(mktemp "${TMPDIR:-/tmp}/gemmam5-git-tracked.XXXXXX")"
cleanup() { rm -f "$allowed_file" "$tracked_file"; }
trap cleanup EXIT

printf '%s\n' 'SHA256SUMS' > "$allowed_file"
python3 "$PROJECT_ROOT/scripts/validate_manifest.py" "$PROJECT_ROOT/SHA256SUMS" \
  --root "$PROJECT_ROOT" --require-files --print-paths >> "$allowed_file"
LC_ALL=C sort -u -o "$allowed_file" "$allowed_file"
git ls-files | LC_ALL=C sort -u > "$tracked_file"

missing="$(comm -23 "$allowed_file" "$tracked_file" || true)"
extra="$(comm -13 "$allowed_file" "$tracked_file" || true)"
if [ -n "$missing" ]; then
  printf 'ERROR: release-manifest paths missing from Git index:\n%s\n' "$missing" >&2
fi
if [ -n "$extra" ]; then
  printf 'ERROR: tracked paths outside the release manifest:\n%s\n' "$extra" >&2
fi
[ -z "$missing" ] && [ -z "$extra" ] || exit 1

if [ "$require_clean" -eq 1 ]; then
  changes="$(git status --porcelain --untracked-files=all)"
  [ -z "$changes" ] || {
    printf 'ERROR: Git working tree is not clean:\n%s\n' "$changes" >&2
    exit 1
  }
fi

log "Git tracked inventory exactly matches SHA256SUMS plus SHA256SUMS itself."
if [ "$require_clean" -eq 1 ]; then
  log "Git working tree is clean."
fi
