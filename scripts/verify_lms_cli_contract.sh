#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "$0")" && pwd)/lib/common.sh"

require_macos
require_lms

require_help_flag() {
  local command_label="$1" help_text="$2" flag="$3"
  grep -q -- "$flag" <<<"$help_text" || fail "$command_label does not expose required flag $flag. Update LM Studio."
}

get_help="$(lms get --help 2>&1)"
load_help="$(lms load --help 2>&1)"
ls_help="$(lms ls --help 2>&1)"
ps_help="$(lms ps --help 2>&1)"
start_help="$(lms server start --help 2>&1)"
status_help="$(lms server status --help 2>&1)"

for flag in --gguf --yes; do require_help_flag 'lms get' "$get_help" "$flag"; done
selection_flag="$(lms_get_selection_flag)"
for flag in --context-length --gpu --parallel --identifier --ttl --estimate-only --yes; do
  require_help_flag 'lms load' "$load_help" "$flag"
done
for flag in --variants --json; do require_help_flag 'lms ls' "$ls_help" "$flag"; done
require_help_flag 'lms ps' "$ps_help" --json
for flag in --bind --port; do require_help_flag 'lms server start' "$start_help" "$flag"; done
require_help_flag 'lms server status' "$status_help" --json

log "lms CLI contract verified. Interactive selection flag: $selection_flag"
log "Hidden fail-closed load flags --exact and --local are exercised by estimate/load commands; an incompatible CLI will stop before accepting a model."
