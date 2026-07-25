#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "$0")" && pwd)/lib/common.sh"

require_macos
require_lms
require_command python3
require_secure_target_profile_config
"$PROJECT_ROOT/scripts/check_lm_studio_version.sh"

context="${1:-$(config_value CONTEXT_LENGTH 8192)}"
gpu="$(config_value GPU_OFFLOAD max)"
identity="$(resolve_exact_model_identity)"
IFS=$'\t' read -r model_path model_key <<< "$identity"
[ -n "$model_path" ] && [ -n "$model_key" ] || fail "The exact model resolver returned an incomplete identity."
require_positive_integer "Context length" "$context"
require_gpu_offload "$gpu"

log "Model path used by lms load --exact: $model_path"
log "Expected modelKey postcondition: $model_key"
log "Context length: $context"
log "GPU offload: $gpu"
log ""

lms load "$model_path" \
  --estimate-only \
  --exact \
  --local \
  --yes \
  --context-length "$context" \
  --gpu "$gpu"

log ""
log "Do not load the model if the estimate leaves no practical reserve for macOS and required applications."
