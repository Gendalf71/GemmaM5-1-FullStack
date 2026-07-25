#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "$0")" && pwd)/lib/common.sh"

known_hosts="${1:-$HOME/.ssh/known_hosts}"
host="${2:-github.com}"
expected_fingerprint='SHA256:+DiY3wvvV6TuJJhbpZisF/zLDA0zPMSvHdkr4UvCOqU'

require_command ssh-keygen
[ "$host" = 'github.com' ] || fail "This verifier is intentionally restricted to github.com, got: $host"
[ -f "$known_hosts" ] || fail "Known-hosts file is missing: $known_hosts. Confirm GitHub's published Ed25519 fingerprint during the first interactive connection before automation."

matches="$(ssh-keygen -F "$host" -f "$known_hosts" 2>/dev/null || true)"
[ -n "$matches" ] || fail "No known_hosts entry was found for $host in $known_hosts. Do not populate it from unauthenticated ssh-keyscan output alone."

tmp="$(mktemp "${TMPDIR:-/tmp}/github-known-hosts.XXXXXX")"
cleanup() { rm -f "$tmp"; }
trap cleanup EXIT
printf '%s\n' "$matches" | awk '!/^#/ && NF {print}' > "$tmp"
[ -s "$tmp" ] || fail "ssh-keygen found no usable host-key rows for $host."

fingerprints="$(ssh-keygen -lf "$tmp" -E sha256 2>/dev/null || true)"
printf '%s\n' "$fingerprints"
if ! printf '%s\n' "$fingerprints" | awk -v expected="$expected_fingerprint" '$2 == expected && $NF == "(ED25519)" {found=1} END {exit(found ? 0 : 1)}'; then
  fail "The persisted github.com Ed25519 key does not match GitHub's published fingerprint $expected_fingerprint. Stop and inspect ~/.ssh/known_hosts; do not bypass this failure."
fi
log "GitHub known_hosts Ed25519 fingerprint verified: $expected_fingerprint"
