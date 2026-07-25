#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "$0")" && pwd)/lib/common.sh"

require_macos
require_lms
require_command curl
require_secure_target_profile_config
host="$(config_value SERVER_HOST 127.0.0.1)"
port="$(config_value SERVER_PORT 1234)"
require_port "$port"
[ "$host" = "127.0.0.1" ] || fail "This repository permits only SERVER_HOST=127.0.0.1."

log "Server status"
assert_lms_server_status "$port"
log ""
log "Loaded models"
lms ps || true
log ""

if command_exists memory_pressure; then
  log "Memory pressure"
  memory_pressure -Q || true
  log ""
fi

log "Listening socket"
assert_loopback_listener "$port"
log ""
log "API model list"
require_api_token
header_file="$(mktemp "${TMPDIR:-/tmp}/gemmam5-status-header.XXXXXX")"
cleanup() { rm -f -- "$header_file"; }
trap cleanup EXIT HUP INT TERM
create_curl_auth_header_file "$header_file"
headers=()
if [ -s "$header_file" ]; then headers=(--header "@$header_file"); fi
curl --fail --silent --show-error \
  --connect-timeout 5 \
  --max-time 30 \
  "http://$host:$port/v1/models" \
  "${headers[@]}"
printf '\n'
