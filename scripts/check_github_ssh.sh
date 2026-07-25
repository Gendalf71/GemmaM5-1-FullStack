#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "$0")" && pwd)/lib/common.sh"

host_alias="${1:-github-gendalf71}"
expected_login="${2:-Gendalf71}"
expected_identity="${3:-$HOME/.ssh/id_ed25519_github_gendalf71_m5}"
require_command ssh
require_command python3
[ -f "$expected_identity" ] || fail "Expected SSH private key is missing: $expected_identity"

log "Inspecting effective SSH configuration for host alias: $host_alias"
effective="$(ssh -G "$host_alias" 2>/dev/null)" || fail "ssh -G could not resolve the host alias '$host_alias'."
SSH_EFFECTIVE="$effective" python3 - "$expected_identity" <<'PY'
from __future__ import annotations
import os
from pathlib import Path
import sys

expected = str(Path(sys.argv[1]).expanduser().resolve(strict=False))
rows: dict[str, list[str]] = {}
for line in os.environ.get('SSH_EFFECTIVE', '').splitlines():
    key, _, value = line.partition(' ')
    if key and value:
        rows.setdefault(key.lower(), []).append(value.strip())

def first(name: str) -> str:
    values = rows.get(name, [])
    return values[0] if values else ''

if first('hostname').lower() != 'github.com':
    raise SystemExit(f"ERROR: effective SSH HostName must be github.com, got {first('hostname')!r}")
if first('user') != 'git':
    raise SystemExit(f"ERROR: effective SSH User must be git, got {first('user')!r}")
if first('identitiesonly').lower() != 'yes':
    raise SystemExit('ERROR: effective SSH IdentitiesOnly must be yes')
for setting in ('proxycommand', 'proxyjump'):
    value = first(setting)
    if value and value.lower() != 'none':
        raise SystemExit(f'ERROR: effective SSH {setting} must be none, got {value!r}')
identities = {
    str(Path(value.replace('~', str(Path.home()), 1)).expanduser().resolve(strict=False))
    for value in rows.get('identityfile', [])
}
if expected not in identities:
    raise SystemExit(f'ERROR: expected SSH IdentityFile is not effective: {expected}')
print('Effective SSH configuration verified: github.com, user git, exact identity, IdentitiesOnly yes, no proxy.')
PY

"$PROJECT_ROOT/scripts/verify_github_known_hosts.sh" "$HOME/.ssh/known_hosts" github.com

log "Testing GitHub SSH authentication through host alias: $host_alias"
log "Expected GitHub login: $expected_login"
set +e
output="$(ssh -T -o BatchMode=yes -o StrictHostKeyChecking=yes -o ConnectTimeout=15 "git@$host_alias" 2>&1)"
code=$?
set -e
printf '%s\n' "$output"

if ! printf '%s' "$output" | grep -q "successfully authenticated"; then
  warn "SSH authentication was not confirmed. Original ssh exit code: $code"
  exit 1
fi
if ! printf '%s' "$output" | grep -Fq "Hi ${expected_login}!"; then
  warn "SSH authenticated a different GitHub account. Expected: $expected_login"
  exit 1
fi
log "RESULT: SSH authentication succeeded for $expected_login. GitHub normally returns exit code 1 because it does not provide shell access."
