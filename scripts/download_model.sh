#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "$0")" && pwd)/lib/common.sh"

interactive_fallback=0
while [ "$#" -gt 0 ]; do
  case "$1" in
    --interactive-fallback) interactive_fallback=1 ;;
    -h|--help)
      cat <<'EOF'
Usage: scripts/download_model.sh [--interactive-fallback]

The default path downloads the exact catalog entry and quantization only.
--interactive-fallback permits manual selection if the exact reference is not
accepted; the script feature-detects the current or legacy lms selection flag
and still verifies the selected local model afterwards.
EOF
      exit 0
      ;;
    *) fail "Unknown argument: $1" ;;
  esac
  shift
done

require_macos
require_lms
require_command python3
require_secure_target_profile_config
"$PROJECT_ROOT/scripts/check_lm_studio_version.sh"

catalog_id="$(config_value MODEL_CATALOG_ID)"
quantization="$(config_value MODEL_QUANTIZATION q4_0)"
exact_ref="${catalog_id}@${quantization}"
require_target_model_profile "$catalog_id" "$quantization"

log "Requested catalog model: $catalog_id"
log "Requested format: GGUF"
log "Requested quantization: $quantization"
log "Exact catalog reference: $exact_ref"
log "The LM Studio catalog lists Q4_0 at 15.60 GB (about 14.53 GiB); the exact package may differ by revision."
log ""

if lms get "$exact_ref" --gguf --yes; then
  log "Exact model download command completed."
elif [ "$interactive_fallback" -eq 1 ]; then
  warn "The exact catalog reference was not accepted by the installed lms version."
  warn "Interactive fallback was explicitly requested. Select GGUF and Q4_0 only."
  selection_flag="$(lms_get_selection_flag)"
  lms get "$catalog_id" --gguf "$selection_flag"
else
  fail "Exact catalog download failed. Review network/runtime errors and retry. Use --interactive-fallback only for a deliberate manual selection."
fi

identity="$(resolve_exact_model_identity)"
IFS=$'\t' read -r model_path model_key <<< "$identity"
[ -n "$model_path" ] && [ -n "$model_key" ] || fail "The exact model resolver returned an incomplete identity."
log "Verified local model path: $model_path"
log "Verified local modelKey: $model_key"
log ""
log "Downloaded models"
lms ls --variants || lms ls
