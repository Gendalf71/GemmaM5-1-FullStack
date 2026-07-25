#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "$0")" && pwd)/lib/common.sh"

require_macos
require_command plutil
require_secure_target_profile_config

min_version="$(config_value MIN_LM_STUDIO_VERSION 0.4.11)"
recommended_version="$(config_value RECOMMENDED_LM_STUDIO_VERSION 0.4.20)"
repository_version="$(read_release_version)"

find_app() {
  local candidate
  if [ -n "${LM_STUDIO_APP_PATH:-}" ]; then
    [ -d "$LM_STUDIO_APP_PATH" ] || fail "LM_STUDIO_APP_PATH is not an application directory: $LM_STUDIO_APP_PATH"
    printf '%s' "$LM_STUDIO_APP_PATH"
    return 0
  fi
  for candidate in "/Applications/LM Studio.app" "$HOME/Applications/LM Studio.app"; do
    if [ -d "$candidate" ]; then
      printf '%s' "$candidate"
      return 0
    fi
  done
  return 1
}

app_path="$(find_app)" || fail "LM Studio.app was not found in /Applications or ~/Applications. Install LM Studio $min_version or newer."
plist="$app_path/Contents/Info.plist"
[ -f "$plist" ] || fail "LM Studio Info.plist was not found: $plist"
version="$(plutil -extract CFBundleShortVersionString raw -o - "$plist" 2>/dev/null || true)"
[[ "$version" =~ ^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$ ]] || \
  fail "LM Studio reported a non-canonical application version: ${version:-empty}"
version_at_least "$version" "$min_version" || \
  fail "LM Studio $min_version or newer is required for the updated Gemma 4 chat template; detected $version."

log "LM Studio application version: $version (minimum $min_version)"
if version_at_least "$version" "$recommended_version"; then
  log "LM Studio recommendation: satisfied ($recommended_version or newer)."
else
  warn "LM Studio $version meets the minimum, but $recommended_version or newer is recommended for the audited $repository_version profile."
fi
