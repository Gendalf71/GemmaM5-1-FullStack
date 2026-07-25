#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "$0")" && pwd)/lib/common.sh"

require_macos
require_lms
require_command python3
require_command mktemp
require_secure_target_profile_config

output="${1:-$PROJECT_ROOT/artifacts/model-provenance.json}"
catalog_id="$(config_value MODEL_CATALOG_ID)"
quantization="$(config_value MODEL_QUANTIZATION)"
require_target_model_profile "$catalog_id" "$quantization"
identity="$(resolve_exact_model_identity)"
IFS=$'\t' read -r model_path model_key <<< "$identity"
[ -n "$model_path" ] && [ -n "$model_key" ] || fail "The exact model resolver returned an incomplete identity."
version="$(read_release_version)"
collected_utc="$(date -u '+%Y-%m-%dT%H:%M:%SZ')"

umask 077
inventory="$(mktemp "${TMPDIR:-/tmp}/gemmam5-model-inventory.XXXXXX")"
temporary_output="$(mktemp "${TMPDIR:-/tmp}/gemmam5-model-provenance.XXXXXX")"
cleanup() { rm -f "$inventory" "$temporary_output"; }
trap cleanup EXIT

lms ls --json > "$inventory" || fail "LM Studio did not return the machine-readable local inventory."
python3 "$PROJECT_ROOT/scripts/write_model_provenance.py" \
  --inventory "$inventory" \
  --output "$temporary_output" \
  --repository-version "$version" \
  --catalog-id "$catalog_id" \
  --required-quantization "$quantization" \
  --resolved-model-key "$model_key" \
  --resolved-model-path "$model_path" \
  --collected-utc "$collected_utc"
mkdir -p "$(dirname "$output")"
mv "$temporary_output" "$output"
log "Privacy-filtered model provenance written to: $output"
