#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "$0")" && pwd)/lib/common.sh"

require_command git
cd "$PROJECT_ROOT"
[ -d .git ] || fail "Initialize Git first with: git init -b main"
[ -f SHA256SUMS ] || fail "SHA256SUMS is missing."

allowed_file="$(mktemp "${TMPDIR:-/tmp}/gemmam5-stage-allowed.XXXXXX")"
cleanup() { rm -f "$allowed_file"; }
trap cleanup EXIT

printf '%s\n' 'SHA256SUMS' > "$allowed_file"
python3 "$PROJECT_ROOT/scripts/validate_manifest.py" "$PROJECT_ROOT/SHA256SUMS" \
  --root "$PROJECT_ROOT" --require-files --print-paths >> "$allowed_file"
LC_ALL=C sort -u -o "$allowed_file" "$allowed_file"

unexpected=""
while IFS= read -r path; do
  [ -n "$path" ] || continue
  if ! grep -Fqx -- "$path" "$allowed_file"; then
    unexpected="${unexpected}${path}\n"
  fi
done < <(git ls-files --others --exclude-standard)

if [ -n "$unexpected" ]; then
  printf 'ERROR: unexpected untracked files are not part of the release manifest:\n%b' "$unexpected" >&2
  printf 'Move, ignore, review, or add them deliberately to SHA256SUMS before publishing.\n' >&2
  exit 1
fi

while IFS= read -r path; do
  git add -- "$path"
done < "$allowed_file"

git diff --cached --check

invalid=""
while IFS= read -r path; do
  [ -n "$path" ] || continue
  if ! grep -Fqx -- "$path" "$allowed_file"; then
    invalid="${invalid}${path}\n"
  fi
done < <(git diff --cached --name-only --diff-filter=ACMRTUXB)

if [ -n "$invalid" ]; then
  printf 'ERROR: staged paths outside the release manifest:\n%b' "$invalid" >&2
  exit 1
fi

log "Staged only files declared by SHA256SUMS plus SHA256SUMS itself."
git diff --cached --stat
