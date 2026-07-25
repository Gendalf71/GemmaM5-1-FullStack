#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "$0")" && pwd)/lib/common.sh"

require_macos
require_command curl
require_secure_target_profile_config
require_api_token
host="$(config_value SERVER_HOST 127.0.0.1)"
port="$(config_value SERVER_PORT 1234)"
require_port "$port"
[ "$host" = "127.0.0.1" ] || fail "API authentication verification is restricted to SERVER_HOST=127.0.0.1."

header_file="$(mktemp "${TMPDIR:-/tmp}/gemmam5-auth-header.XXXXXX")"
cleanup() { rm -f -- "$header_file"; }
trap cleanup EXIT HUP INT TERM
create_curl_auth_header_file "$header_file"

endpoint="http://$host:$port/v1/models"
unauthenticated_code="$(curl --silent --show-error --output /dev/null --write-out '%{http_code}' --connect-timeout 5 --max-time 30 "$endpoint" || true)"
case "$unauthenticated_code" in
  401|403) ;;
  *) fail "LM Studio authentication is not enforced: unauthenticated $endpoint returned HTTP ${unauthenticated_code:-no-response}. Enable Require Authentication in Developer > Server Settings." ;;
esac

authenticated_code="$(curl --silent --show-error --output /dev/null --write-out '%{http_code}' --connect-timeout 5 --max-time 30 --header "@$header_file" "$endpoint" || true)"
[ "$authenticated_code" = "200" ] || fail "Authenticated API verification failed with HTTP ${authenticated_code:-no-response}. Check LM_API_TOKEN and its permissions."
log "LM Studio API authentication verified: unauthenticated access rejected, token-authenticated access accepted."
