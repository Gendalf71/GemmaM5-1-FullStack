#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "$0")" && pwd)/lib/common.sh"

unload_all=0
while [ "$#" -gt 0 ]; do
  case "$1" in
    --unload-all) unload_all=1 ;;
    -h|--help) printf '%s\n' 'Usage: scripts/stop_server.sh [--unload-all]'; exit 0 ;;
    *) fail "Unknown argument: $1" ;;
  esac
  shift
done

require_macos
require_lms
require_command python3
require_command lsof
require_secure_target_profile_config
port="$(config_value SERVER_PORT 1234)"
require_port "$port"
if ! lms server stop; then
  warn "LM Studio server stop returned a non-zero status; verifying the final state instead of assuming success."
fi
assert_lms_server_stopped 10
assert_no_tcp_listener "$port" 10
log "LM Studio server is stopped and no listener remains on port $port."
if [ "$unload_all" -eq 1 ]; then
  log "Explicit unload of all models requested."
  lms unload --all
else
  log "Loaded models were retained. Use --unload-all only when you intend to remove every loaded model from memory."
fi
