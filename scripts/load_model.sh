#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "$0")" && pwd)/lib/common.sh"

execute=0
unload_others=0
assume_yes=0
context="$(config_value CONTEXT_LENGTH 8192)"

while [ "$#" -gt 0 ]; do
  case "$1" in
    --execute) execute=1 ;;
    --unload-others) unload_others=1 ;;
    --yes) assume_yes=1 ;;
    --context)
      shift
      [ "$#" -gt 0 ] || fail "--context requires a value"
      context="$1"
      ;;
    -h|--help)
      cat <<'EOF'
Usage: scripts/load_model.sh [--execute] [--context N] [--unload-others] [--yes]

Without --execute, the script performs the mandatory estimate and exits.
--unload-others requests an explicit lms unload --all before loading.
--yes skips the typed UNLOAD confirmation and is intended only for reviewed automation.
EOF
      exit 0
      ;;
    *) fail "Unknown argument: $1" ;;
  esac
  shift
done

require_macos
require_lms
require_lms_parallel_support
require_command python3
require_secure_target_profile_config
"$PROJECT_ROOT/scripts/check_lm_studio_version.sh"
require_positive_integer "Context length" "$context"

identity="$(resolve_exact_model_identity)"
IFS=$'\t' read -r model_path model_key <<< "$identity"
[ -n "$model_path" ] && [ -n "$model_key" ] || fail "The exact model resolver returned an incomplete identity."
identifier="$(config_value MODEL_IDENTIFIER gemma4-local)"
gpu="$(config_value GPU_OFFLOAD max)"
parallel="$(config_value MAX_CONCURRENT_PREDICTIONS 1)"
ttl="$(config_value TTL_SECONDS 3600)"
require_positive_integer "MAX_CONCURRENT_PREDICTIONS" "$parallel"
[ "$parallel" -eq 1 ] || fail "MAX_CONCURRENT_PREDICTIONS must remain 1 for this 24 GB profile."
require_positive_integer "TTL_SECONDS" "$ttl"

case "$identifier" in ''|*[!A-Za-z0-9._-]*) fail "MODEL_IDENTIFIER contains unsupported characters: $identifier" ;; esac
require_gpu_offload "$gpu"

log "The mandatory resource estimate follows."
"$PROJECT_ROOT/scripts/estimate_model.sh" "$context"
log ""

if [ "$execute" -ne 1 ]; then
  log "Dry run completed. No model was loaded and no model was unloaded."
  log "Review the estimate, close memory-heavy applications, then run:"
  log "./scripts/load_model.sh --execute --context $context"
  exit 0
fi

if command_exists memory_pressure; then
  log "Current memory pressure before load"
  memory_pressure -Q || true
fi

log "Currently loaded models"
lms ps || true
log ""

loaded_json="$(lms ps --json --quiet)" || fail "LM Studio did not return the loaded-model inventory."
pre_state="$(printf '%s' "$loaded_json" | python3 "$PROJECT_ROOT/scripts/verify_loaded_model.py" \
  --phase pre \
  --expected-model-path "$model_path" \
  --expected-model-key "$model_key" \
  --expected-identifier "$identifier" \
  --expected-parallel "$parallel")"

if [ "$pre_state" = "already-loaded" ] && [ "$unload_others" -ne 1 ]; then
  log "The unique exact model instance is already loaded with the required path, modelKey, identifier and concurrency."
  exit 0
fi
[ "$pre_state" = "ready" ] || [ "$pre_state" = "already-loaded" ] || fail "Unexpected loaded-model precondition state: $pre_state"

if [ "$unload_others" -eq 1 ]; then
  log "You explicitly requested removal of every currently loaded model."
  if [ "$assume_yes" -ne 1 ]; then
    confirm_exact "UNLOAD" "This will run: lms unload --all"
  fi
  lms unload --all
else
  log "No unrelated model will be unloaded. Use --unload-others only after reviewing the list above."
fi

load_attempted=0
cleanup_failed_load() {
  local rc=$?
  if [ "$rc" -ne 0 ] && [ "$load_attempted" -eq 1 ]; then
    warn "Load or postcondition verification failed; rolling back the exact managed identifier '$identifier'."
    lms unload "$identifier" >/dev/null 2>&1 || \
      warn "Automatic rollback could not unload '$identifier'; inspect lms ps and unload that identifier manually."
  fi
  trap - EXIT
  exit "$rc"
}
trap cleanup_failed_load EXIT

log "Loading exact local path $model_path"
log "Expected loaded modelKey: $model_key"
log "Managed API identifier: $identifier"
load_attempted=1
lms load "$model_path" \
  --exact \
  --local \
  --yes \
  --context-length "$context" \
  --gpu "$gpu" \
  --parallel "$parallel" \
  --identifier "$identifier" \
  --ttl "$ttl"

lms ps --json --quiet | python3 "$PROJECT_ROOT/scripts/verify_loaded_model.py" \
  --phase post \
  --expected-model-path "$model_path" \
  --expected-model-key "$model_key" \
  --expected-identifier "$identifier" \
  --expected-parallel "$parallel"

trap - EXIT
log "Model loaded and its exact path, modelKey, identifier and concurrency postconditions were verified."
