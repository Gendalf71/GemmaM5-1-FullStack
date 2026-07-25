#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "$0")" && pwd)/lib/common.sh"

require_macos
require_lms
require_command python3
require_secure_target_profile_config
host="$(config_value SERVER_HOST 127.0.0.1)"
port="$(config_value SERVER_PORT 1234)"
require_port "$port"
[ "$host" = "127.0.0.1" ] || fail "This repository permits only SERVER_HOST=127.0.0.1."

help_text="$(lms server start --help 2>&1 || true)"
printf '%s' "$help_text" | grep -q -- '--bind' || \
  fail "The installed lms CLI does not advertise --bind. Update LM Studio and keep Serve on Local Network disabled."

log "Confirming that no LM Studio server is already running."
assert_lms_server_stopped 1
server_started=0
cleanup_failed_start() {
  local rc=$?
  if [ "$rc" -ne 0 ] && [ "$server_started" -eq 1 ]; then
    warn "Server startup postconditions failed; stopping the server started by this script."
    lms server stop >/dev/null 2>&1 || warn "Automatic rollback could not stop LM Studio; run scripts/stop_server.sh and inspect the listener."
  fi
  trap - EXIT
  exit "$rc"
}
trap cleanup_failed_start EXIT

log "Starting the LM Studio server on $host:$port."
log "CORS and local-network serving are not enabled by this script."
lms server start --bind "$host" --port "$port"
server_started=1
log "Verifying LM Studio server state"
assert_lms_server_status "$port"
log "Verifying the listening address"
assert_loopback_listener "$port"
auth_required="$(config_value REQUIRE_API_AUTH 1)"
[ "$auth_required" = "1" ] || fail "REQUIRE_API_AUTH must remain 1 for the secure target profile."
"$PROJECT_ROOT/scripts/verify_api_auth.sh"
log "OpenAI-compatible base URL: http://$host:$port/v1"
log "Native API base URL: http://$host:$port/api/v1"

trap - EXIT
