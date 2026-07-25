#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "$0")" && pwd)/lib/common.sh"

log "GemmaM5-1 FullStack preflight"
log "This script performs read only checks."
log ""

require_macos
require_command python3
require_secure_target_profile_config

arch="$(uname -m)"
macos_version="$(sw_vers -productVersion)"
hardware_json="$(system_profiler SPHardwareDataType -json 2>/dev/null)" || fail "system_profiler could not read hardware data."
hardware_profile="$(printf '%s' "$hardware_json" | python3 "$PROJECT_ROOT/scripts/parse_hardware_profile.py")"
model_name="$(printf '%s' "$hardware_profile" | python3 -c 'import json,sys; print(json.load(sys.stdin)["model_name"])')"
model_identifier="$(printf '%s' "$hardware_profile" | python3 -c 'import json,sys; print(json.load(sys.stdin)["model_identifier"])')"
chip="$(printf '%s' "$hardware_profile" | python3 -c 'import json,sys; print(json.load(sys.stdin)["chip"])')"
mem_bytes="$(sysctl -n hw.memsize)"
mem_gb="$((mem_bytes / 1024 / 1024 / 1024))"
free_kb="$(df -Pk "$HOME" | awk 'NR==2 {print $4}')"
free_gb="$((free_kb / 1024 / 1024))"
min_memory="$(config_value MIN_MEMORY_GB 24)"
min_disk="$(config_value MIN_FREE_DISK_GB 35)"
recommended_disk="$(config_value RECOMMENDED_FREE_DISK_GB 40)"
target_model="$(config_value TARGET_MODEL_NAME 'MacBook Air')"
target_chip="$(config_value TARGET_CHIP_TOKEN M5)"
target_identifiers="$(config_value TARGET_MODEL_IDENTIFIERS 'Mac17,3,Mac17,4')"
min_macos="$(config_value MIN_MACOS_VERSION 26.0)"
status=0

log "Architecture: $arch"
log "Model: $model_name"
log "Model identifier: $model_identifier"
log "Chip: ${chip:-not detected}"
log "macOS: $macos_version"
log "Unified memory reported by macOS: ${mem_gb} GB"
log "Free disk space on the home volume: approximately ${free_gb} GB"
log ""


if [ "$model_name" != "$target_model" ]; then
  warn "Target model must be '$target_model'; detected '$model_name'."
  status=1
fi

case "$chip" in *"$target_chip"*) ;; *) warn "Target chip must contain '$target_chip'; detected '$chip'."; status=1 ;; esac

case ",$target_identifiers," in
  *",$model_identifier,"*) ;;
  *) warn "Target model identifier must be one of '$target_identifiers'; detected '$model_identifier'."; status=1 ;;
esac

if ! version_at_least "$macos_version" "$min_macos"; then
  warn "macOS $min_macos or newer is required; detected $macos_version."
  status=1
fi

if [ "$arch" != "arm64" ]; then
  warn "Apple Silicon arm64 is required."
  status=1
fi

if [ "$mem_gb" -lt "$min_memory" ]; then
  warn "At least ${min_memory} GB of unified memory is required by this repository profile."
  status=1
fi

if [ "$free_gb" -lt "$min_disk" ]; then
  warn "Less than ${min_disk} GB is free. Model download and safe runtime reserve are not available."
  status=1
elif [ "$free_gb" -lt "$recommended_disk" ]; then
  warn "The minimum disk condition is met, but ${recommended_disk} GB or more is recommended."
fi

for command_name in git curl python3; do
  if command_exists "$command_name"; then
    log "$command_name: found"
  else
    warn "$command_name: not found"
    status=1
  fi
done

if command_exists brew; then
  log "Homebrew: $(brew --version | head -n 1)"
else
  warn "Homebrew is not installed. LM Studio can still be installed manually, but the automated installation script will not run."
fi

if "$PROJECT_ROOT/scripts/check_lm_studio_version.sh"; then
  log "LM Studio application compatibility: supported"
else
  warn "LM Studio application version does not satisfy the audited profile."
  status=1
fi

if command_exists lms; then
  log "lms CLI: found"
  if "$PROJECT_ROOT/scripts/verify_lms_cli_contract.sh"; then
    log "lms CLI compatibility contract: supported"
  else
    warn "The installed lms CLI does not satisfy the repository command contract."
    status=1
  fi
elif [ -x "$HOME/.lmstudio/bin/lms" ]; then
  export PATH="$HOME/.lmstudio/bin:$PATH"
  log "lms CLI: found at $HOME/.lmstudio/bin/lms"
  if "$PROJECT_ROOT/scripts/verify_lms_cli_contract.sh"; then
    log "lms CLI compatibility contract: supported"
  else
    warn "The installed lms CLI does not satisfy the repository command contract."
    status=1
  fi
else
  warn "lms CLI: not found. It becomes available after the first LM Studio launch."
fi

if command_exists memory_pressure; then
  log ""
  log "Current memory pressure summary"
  memory_pressure -Q || true
fi

log ""
if [ "$status" -eq 0 ]; then
  log "RESULT: critical hardware and disk checks passed."
else
  log "RESULT: at least one critical preflight condition failed."
fi
exit "$status"
