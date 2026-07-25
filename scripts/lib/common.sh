#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
DEFAULT_CONFIG="$PROJECT_ROOT/config/defaults.conf"
LOCAL_CONFIG="$PROJECT_ROOT/config/local.conf"

log() { printf '%s\n' "$*"; }
fail() { printf 'ERROR: %s\n' "$*" >&2; exit 1; }
warn() { printf 'WARNING: %s\n' "$*" >&2; }
command_exists() { command -v "$1" >/dev/null 2>&1; }

read_config_key() {
  local key="$1" file="$2"
  awk -F= -v wanted="$key" '
    /^[[:space:]]*#/ { next }
    NF >= 2 {
      left=$1
      gsub(/^[[:space:]]+|[[:space:]]+$/, "", left)
      if (left == wanted) {
        sub(/^[^=]*=/, "")
        gsub(/^[[:space:]]+|[[:space:]]+$/, "")
        print
        exit
      }
    }
  ' "$file"
}

validate_config_files() {
  require_command python3
  python3 - "$DEFAULT_CONFIG" "$LOCAL_CONFIG" <<'PY_CONFIG'
from __future__ import annotations
import os
from pathlib import Path
import re
import stat
import sys

ALLOWED = {
    "MODEL_CATALOG_ID", "MODEL_QUANTIZATION", "MODEL_IDENTIFIER", "CONTEXT_LENGTH",
    "GPU_OFFLOAD", "MAX_CONCURRENT_PREDICTIONS", "TTL_SECONDS", "SERVER_HOST",
    "SERVER_PORT", "MIN_MEMORY_GB", "MIN_FREE_DISK_GB", "RECOMMENDED_FREE_DISK_GB",
    "REQUIRE_API_AUTH", "TARGET_MODEL_NAME", "TARGET_CHIP_TOKEN",
    "TARGET_MODEL_IDENTIFIERS", "MIN_MACOS_VERSION", "MIN_LM_STUDIO_VERSION",
    "RECOMMENDED_LM_STUDIO_VERSION",
}
LINE = re.compile(r"([A-Z][A-Z0-9_]*)=([^\n]*)")

def fail(message: str) -> None:
    raise SystemExit(f"ERROR: {message}")

def parse(path: Path, required: bool) -> set[str]:
    if not path.exists():
        if required: fail(f"configuration file is missing: {path}")
        return set()
    if path.is_symlink() or not path.is_file():
        fail(f"configuration path must be a regular non-symlink file: {path}")
    mode = stat.S_IMODE(path.stat().st_mode)
    if mode & 0o022:
        fail(f"configuration file must not be group/world-writable: {path} ({mode:04o})")
    data = path.read_bytes()
    if b"\r" in data:
        fail(f"configuration file must use LF line endings: {path}")
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        fail(f"configuration file is not valid UTF-8: {path}: {exc}")
    seen: set[str] = set()
    for number, raw in enumerate(text.splitlines(), 1):
        if not raw or raw.startswith("#"):
            continue
        if any(ord(ch) < 32 for ch in raw):
            fail(f"control character in {path}:{number}")
        match = LINE.fullmatch(raw)
        if not match:
            fail(f"non-canonical KEY=VALUE line in {path}:{number}")
        key, value = match.groups()
        if key not in ALLOWED:
            fail(f"unsupported configuration key in {path}:{number}: {key}")
        if key in seen:
            fail(f"duplicate configuration key in {path}:{number}: {key}")
        if value == "" or value != value.strip():
            fail(f"configuration value must be non-empty and unpadded in {path}:{number}: {key}")
        seen.add(key)
    return seen

defaults = parse(Path(sys.argv[1]), True)
missing = sorted(ALLOWED - defaults)
if missing:
    fail("defaults.conf is missing keys: " + ", ".join(missing))
parse(Path(sys.argv[2]), False)
PY_CONFIG
}

config_value() {
  local key="$1" default_value="${2:-}" value=""
  case "$key" in
    MODEL_CATALOG_ID|MODEL_QUANTIZATION|MODEL_IDENTIFIER|CONTEXT_LENGTH|GPU_OFFLOAD|MAX_CONCURRENT_PREDICTIONS|TTL_SECONDS|SERVER_HOST|SERVER_PORT|MIN_MEMORY_GB|MIN_FREE_DISK_GB|RECOMMENDED_FREE_DISK_GB|REQUIRE_API_AUTH|TARGET_MODEL_NAME|TARGET_CHIP_TOKEN|TARGET_MODEL_IDENTIFIERS|MIN_MACOS_VERSION|MIN_LM_STUDIO_VERSION|RECOMMENDED_LM_STUDIO_VERSION) ;;
    *) fail "Unsupported configuration key: $key" ;;
  esac
  if [ -f "$LOCAL_CONFIG" ]; then value="$(read_config_key "$key" "$LOCAL_CONFIG")"; fi
  if [ -z "$value" ] && [ -f "$DEFAULT_CONFIG" ]; then value="$(read_config_key "$key" "$DEFAULT_CONFIG")"; fi
  if [ -z "$value" ]; then value="$default_value"; fi
  printf '%s' "$value"
}

require_command() { command_exists "$1" || fail "Required command not found: $1"; }
require_macos() { [ "$(uname -s)" = "Darwin" ] || fail "This command is intended for macOS."; }

require_lms() {
  if command_exists lms; then return 0; fi
  if [ -x "$HOME/.lmstudio/bin/lms" ]; then
    export PATH="$HOME/.lmstudio/bin:$PATH"
    return 0
  fi
  fail "The lms command is unavailable. Launch LM Studio once, reopen Terminal and run lms --help. Legacy installations may use ~/.lmstudio/bin/lms bootstrap."
}


lms_supports_parallel_flag() {
  lms load --help 2>&1 | grep -q -- '--parallel'
}

require_lms_parallel_support() {
  lms_supports_parallel_flag || fail "The installed lms CLI does not expose lms load --parallel. Update LM Studio, launch it once, reopen Terminal and retry."
}

require_gpu_offload() {
  local value="$1"
  case "$value" in
    max|off) return 0 ;;
  esac
  if ! python3 - "$value" <<'PY_GPU'
import re
import sys

value = sys.argv[1]
if not re.fullmatch(r'(?:0(?:\.[0-9]+)?|1(?:\.0+)?)', value):
    raise SystemExit(1)
number = float(value)
raise SystemExit(0 if 0.0 <= number <= 1.0 else 1)
PY_GPU
  then
    fail "GPU_OFFLOAD must be 'off', 'max', or a canonical number from 0 to 1: $value"
  fi
}

lms_get_selection_flag() {
  local help
  help="$(lms get --help 2>&1)" || fail "Unable to inspect lms get --help."
  if grep -q -- '--select' <<<"$help"; then
    printf '%s' '--select'
  elif grep -q -- '--always-show-download-options' <<<"$help"; then
    printf '%s' '--always-show-download-options'
  else
    fail "The installed lms CLI exposes neither --select nor the legacy --always-show-download-options flag. Update LM Studio."
  fi
}

require_positive_integer() {
  local label="$1" value="$2"
  case "$value" in ''|*[!0-9]*) fail "$label must be a positive integer." ;; esac
  [ "$value" -gt 0 ] || fail "$label must be greater than zero."
}

require_port() {
  local value="$1"
  require_positive_integer "SERVER_PORT" "$value"
  [ "$value" -le 65535 ] || fail "SERVER_PORT must not exceed 65535."
}

version_at_least() {
  local actual="$1" required="$2"
  awk -v actual="$actual" -v required="$required" 'BEGIN {
    na=split(actual,a,"."); nr=split(required,r,"."); n=(na>nr?na:nr);
    for(i=1;i<=n;i++){av=(i<=na?a[i]+0:0); rv=(i<=nr?r[i]+0:0); if(av>rv)exit 0; if(av<rv)exit 1}
    exit 0
  }'
}

read_release_version() {
  local version
  version="$(cat "$PROJECT_ROOT/VERSION")"
  [[ "$version" =~ ^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$ ]] || \
    fail "VERSION must be a canonical three-component release version (X.Y.Z): $version"
  printf '%s' "$version"
}

assert_loopback_listener() {
  local port="$1" attempts="${2:-10}" endpoints="" current=1
  require_command lsof
  require_command python3
  require_positive_integer "Listener verification attempts" "$attempts"
  while [ "$current" -le "$attempts" ]; do
    endpoints="$(lsof -nP -F n -iTCP:"$port" -sTCP:LISTEN 2>/dev/null | sed -n 's/^n//p' || true)"
    if [ -n "$endpoints" ]; then break; fi
    sleep 1
    current=$((current + 1))
  done
  [ -n "$endpoints" ] || fail "No TCP listener was found on port $port after $attempts checks."
  LISTENER_ENDPOINTS="$endpoints" python3 - "$port" <<'PY_LISTENERS'
import ipaddress
import os
import sys

expected_port = int(sys.argv[1])
endpoints = [line.strip() for line in os.environ.get('LISTENER_ENDPOINTS', '').splitlines() if line.strip()]
if not endpoints:
    raise SystemExit('ERROR: no listener endpoints were supplied for verification')
for endpoint in endpoints:
    if endpoint.startswith('['):
        closing = endpoint.find(']')
        if closing < 0 or closing + 1 >= len(endpoint) or endpoint[closing + 1] != ':':
            raise SystemExit(f'ERROR: cannot parse listener endpoint: {endpoint}')
        host = endpoint[1:closing]
        port_text = endpoint[closing + 2:]
    else:
        try:
            host, port_text = endpoint.rsplit(':', 1)
        except ValueError as exc:
            raise SystemExit(f'ERROR: cannot parse listener endpoint: {endpoint}') from exc
    try:
        port = int(port_text)
    except ValueError as exc:
        raise SystemExit(f'ERROR: invalid listener port in endpoint: {endpoint}') from exc
    if port != expected_port:
        raise SystemExit(f'ERROR: listener endpoint uses port {port}; expected {expected_port}')
    try:
        address = ipaddress.ip_address(host)
    except ValueError as exc:
        raise SystemExit(f'ERROR: listener address is not a numeric IP address: {endpoint}') from exc
    if not address.is_loopback:
        raise SystemExit(f'ERROR: non-loopback listener detected: {endpoint}')
print('Verified loopback-only listener endpoint(s):')
for endpoint in endpoints:
    print(endpoint)
PY_LISTENERS
}

assert_no_tcp_listener() {
  local port="$1" attempts="${2:-10}" endpoints="" current=1
  require_command lsof
  require_positive_integer "Listener shutdown verification attempts" "$attempts"
  while [ "$current" -le "$attempts" ]; do
    endpoints="$(lsof -nP -F n -iTCP:"$port" -sTCP:LISTEN 2>/dev/null | sed -n 's/^n//p' || true)"
    if [ -z "$endpoints" ]; then
      log "No TCP listener remains on port $port."
      return 0
    fi
    sleep 1
    current=$((current + 1))
  done
  printf 'ERROR: TCP listener(s) remain on port %s after %s checks:\n%s\n' "$port" "$attempts" "$endpoints" >&2
  return 1
}

assert_lms_server_status() {
  local expected_port="$1" status_json
  require_command python3
  require_port "$expected_port"
  status_json="$(lms server status --json --quiet 2>/dev/null)" ||     fail "LM Studio did not return machine-readable server status. Update LM Studio and retry."
  LMS_STATUS_JSON="$status_json" python3 - "$expected_port" <<'PY_STATUS'
import json
import os
import sys

expected_port = int(sys.argv[1])
try:
    status = json.loads(os.environ['LMS_STATUS_JSON'])
except (KeyError, json.JSONDecodeError) as exc:
    raise SystemExit(f'ERROR: invalid LM Studio server status JSON: {exc}')
if not isinstance(status, dict):
    raise SystemExit('ERROR: LM Studio server status must be a JSON object')
if status.get('running') is not True:
    raise SystemExit('ERROR: LM Studio reports that the server is not running')
if status.get('port') != expected_port:
    raise SystemExit(
        f"ERROR: LM Studio reports port {status.get('port')!r}; expected {expected_port}"
    )
print(f'LM Studio server status confirms running=true on port {expected_port}.')
PY_STATUS
}

assert_lms_server_stopped() {
  local attempts="${1:-10}" status_json="" current=1
  require_command python3
  require_positive_integer "Server shutdown verification attempts" "$attempts"
  while [ "$current" -le "$attempts" ]; do
    status_json="$(lms server status --json --quiet 2>/dev/null || true)"
    if LMS_STATUS_JSON="$status_json" python3 - <<'PY_STATUS_STOPPED'
import json
import os
try:
    status = json.loads(os.environ.get('LMS_STATUS_JSON', ''))
except json.JSONDecodeError:
    raise SystemExit(1)
raise SystemExit(0 if isinstance(status, dict) and status.get('running') is False else 1)
PY_STATUS_STOPPED
    then
      log "LM Studio server status confirms running=false."
      return 0
    fi
    sleep 1
    current=$((current + 1))
  done
  fail "LM Studio did not confirm running=false after $attempts checks."
}

require_target_model_profile() {
  local catalog_id="$1" quantization="$2"
  [ "$catalog_id" = "google/gemma-4-26b-a4b-qat" ] || \
    fail "MODEL_CATALOG_ID must remain google/gemma-4-26b-a4b-qat for this 24 GB profile."
  [ "$(printf '%s' "$quantization" | tr '[:upper:]' '[:lower:]')" = "q4_0" ] || \
    fail "MODEL_QUANTIZATION must remain q4_0 for this 24 GB profile."
}


require_secure_target_profile_config() {
  validate_config_files
  local catalog_id quantization host auth parallel min_memory min_disk recommended_disk target_model target_chip target_identifiers min_macos min_lm_studio recommended_lm_studio
  catalog_id="$(config_value MODEL_CATALOG_ID)"
  quantization="$(config_value MODEL_QUANTIZATION q4_0)"
  require_target_model_profile "$catalog_id" "$quantization"

  host="$(config_value SERVER_HOST 127.0.0.1)"
  auth="$(config_value REQUIRE_API_AUTH 1)"
  parallel="$(config_value MAX_CONCURRENT_PREDICTIONS 1)"
  min_memory="$(config_value MIN_MEMORY_GB 24)"
  min_disk="$(config_value MIN_FREE_DISK_GB 35)"
  recommended_disk="$(config_value RECOMMENDED_FREE_DISK_GB 40)"
  target_model="$(config_value TARGET_MODEL_NAME 'MacBook Air')"
  target_chip="$(config_value TARGET_CHIP_TOKEN M5)"
  target_identifiers="$(config_value TARGET_MODEL_IDENTIFIERS 'Mac17,3,Mac17,4')"
  min_macos="$(config_value MIN_MACOS_VERSION 26.0)"
  min_lm_studio="$(config_value MIN_LM_STUDIO_VERSION 0.4.11)"
  recommended_lm_studio="$(config_value RECOMMENDED_LM_STUDIO_VERSION 0.4.20)"

  [ "$host" = "127.0.0.1" ] || fail "SERVER_HOST must remain 127.0.0.1 for the secure target profile."
  [ "$auth" = "1" ] || fail "REQUIRE_API_AUTH must remain 1 for the secure target profile."
  require_positive_integer "MAX_CONCURRENT_PREDICTIONS" "$parallel"
  [ "$parallel" -eq 1 ] || fail "MAX_CONCURRENT_PREDICTIONS must remain 1 for the 24 GB target profile."
  require_positive_integer "MIN_MEMORY_GB" "$min_memory"
  require_positive_integer "MIN_FREE_DISK_GB" "$min_disk"
  require_positive_integer "RECOMMENDED_FREE_DISK_GB" "$recommended_disk"
  [ "$min_memory" -ge 24 ] || fail "MIN_MEMORY_GB must not be lower than 24."
  [ "$min_disk" -ge 35 ] || fail "MIN_FREE_DISK_GB must not be lower than 35."
  [ "$recommended_disk" -ge "$min_disk" ] || fail "RECOMMENDED_FREE_DISK_GB must be at least MIN_FREE_DISK_GB."
  [ "$target_model" = "MacBook Air" ] || fail "TARGET_MODEL_NAME must remain MacBook Air."
  [ "$target_chip" = "M5" ] || fail "TARGET_CHIP_TOKEN must remain M5."
  [ "$target_identifiers" = "Mac17,3,Mac17,4" ] || \
    fail "TARGET_MODEL_IDENTIFIERS must remain Mac17,3,Mac17,4."
  [[ "$min_macos" =~ ^(0|[1-9][0-9]*)(\.(0|[1-9][0-9]*)){1,2}$ ]] || \
    fail "MIN_MACOS_VERSION must be a canonical two- or three-component numeric version."
  version_at_least "$min_macos" "26.0" || fail "MIN_MACOS_VERSION must not be lower than 26.0."
  [[ "$min_lm_studio" =~ ^(0|[1-9][0-9]*)(\.(0|[1-9][0-9]*)){2}$ ]] || \
    fail "MIN_LM_STUDIO_VERSION must be a canonical three-component numeric version."
  [[ "$recommended_lm_studio" =~ ^(0|[1-9][0-9]*)(\.(0|[1-9][0-9]*)){2}$ ]] || \
    fail "RECOMMENDED_LM_STUDIO_VERSION must be a canonical three-component numeric version."
  version_at_least "$min_lm_studio" "0.4.11" || \
    fail "MIN_LM_STUDIO_VERSION must not be lower than 0.4.11."
  version_at_least "$recommended_lm_studio" "$min_lm_studio" || \
    fail "RECOMMENDED_LM_STUDIO_VERSION must be at least MIN_LM_STUDIO_VERSION."
}

resolve_exact_model_identity() {
  require_command python3
  if [ -n "${MODEL_KEY:-}" ]; then
    python3 "$PROJECT_ROOT/scripts/resolve_model_identity.py" \
      --verify-model-key "$MODEL_KEY" --format tsv
  else
    python3 "$PROJECT_ROOT/scripts/resolve_model_identity.py" --format tsv
  fi
}

resolve_exact_model_path() {
  require_command python3
  if [ -n "${MODEL_KEY:-}" ]; then
    python3 "$PROJECT_ROOT/scripts/resolve_model_identity.py" \
      --verify-model-key "$MODEL_KEY" --format path
  else
    python3 "$PROJECT_ROOT/scripts/resolve_model_identity.py" --format path
  fi
}

resolve_exact_model_key() {
  require_command python3
  if [ -n "${MODEL_KEY:-}" ]; then
    python3 "$PROJECT_ROOT/scripts/resolve_model_identity.py" \
      --verify-model-key "$MODEL_KEY" --format model-key
  else
    python3 "$PROJECT_ROOT/scripts/resolve_model_identity.py" --format model-key
  fi
}

confirm_exact() {
  local expected="$1" prompt="$2" answer
  [ -t 0 ] || fail "Interactive confirmation is required. Re-run in a Terminal or use the documented --yes flag."
  printf '%s\nType %s to continue: ' "$prompt" "$expected"
  IFS= read -r answer
  [ "$answer" = "$expected" ] || fail "Confirmation did not match; no destructive action was performed."
}

create_curl_auth_header_file() {
  local destination="$1" token="${LM_API_TOKEN:-}"
  umask 077
  : > "$destination"
  [ -n "$token" ] || return 0
  case "$token" in *$'\n'*|*$'\r'*) fail "LM_API_TOKEN must not contain newline characters." ;; esac
  printf 'Authorization: Bearer %s\n' "$token" > "$destination"
}

require_api_token() {
  [ -n "${LM_API_TOKEN:-}" ] || fail "LM_API_TOKEN is required by the secure target profile. Enable authentication in LM Studio, create a token and export it in the current shell."
}
