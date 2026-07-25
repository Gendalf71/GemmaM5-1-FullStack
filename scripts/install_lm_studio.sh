#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "$0")" && pwd)/lib/common.sh"

upgrade=0
case "${1:-}" in
  "") ;;
  --upgrade) upgrade=1 ;;
  *) fail "Usage: $0 [--upgrade]" ;;
esac

require_macos
require_command brew

if brew list --cask lm-studio >/dev/null 2>&1; then
  if [ "$upgrade" -eq 1 ]; then
    log "Explicitly upgrading the installed LM Studio cask. Re-run the repository gates after the version changes."
    brew upgrade --cask lm-studio
  else
    log "LM Studio is already installed. No implicit upgrade was performed."
    log "Run '$0 --upgrade' only when you deliberately accept a runtime change."
  fi
else
  log "Installing LM Studio through the Homebrew cask."
  brew install --cask lm-studio
fi

log "Launching LM Studio. Complete the first launch before using lms."
open -a "LM Studio"
log "After the application opens, start a new Terminal and run: lms --help"
log "For a legacy CLI bootstrap only, use: ~/.lmstudio/bin/lms bootstrap"
