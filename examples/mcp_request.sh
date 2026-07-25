#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
project_root="$(cd -- "$script_dir/.." && pwd)"
source "$project_root/scripts/lib/common.sh"

base_url="${LM_NATIVE_BASE_URL:-http://127.0.0.1:1234/api/v1}"
model="${MODEL_IDENTIFIER:-gemma4-local}"
request_file=""
allow_remote=0

while [ "$#" -gt 0 ]; do
  case "$1" in
    --allow-remote-base-url) allow_remote=1 ;;
    --request-file)
      shift
      [ "$#" -gt 0 ] || { printf '%s\n' 'ERROR: --request-file requires a path.' >&2; exit 1; }
      request_file="$1"
      ;;
    -h|--help)
      cat <<'HELP'
Usage: examples/mcp_request.sh [--request-file PATH] [--allow-remote-base-url] [PATH]

The default endpoint is the local LM Studio native API at 127.0.0.1.
A non-loopback endpoint is rejected unless --allow-remote-base-url is supplied.
The optional positional PATH is retained for compatibility with earlier releases.
HELP
      exit 0
      ;;
    --*) printf 'ERROR: unknown argument: %s\n' "$1" >&2; exit 1 ;;
    *)
      [ -z "$request_file" ] || { printf '%s\n' 'ERROR: more than one request file was supplied.' >&2; exit 1; }
      request_file="$1"
      ;;
  esac
  shift
done

request_file="${request_file:-$project_root/config/mcp_request.example.json}"

command -v python3 >/dev/null 2>&1 || { printf 'Required command not found: python3\n' >&2; exit 1; }
command -v curl >/dev/null 2>&1 || { printf 'Required command not found: curl\n' >&2; exit 1; }
[ -f "$request_file" ] || { printf 'Request file not found: %s\n' "$request_file" >&2; exit 1; }

if [ "$allow_remote" -eq 1 ]; then
  base_url="$(python3 "$project_root/scripts/api_url_policy.py" --kind native --allow-remote-base-url "$base_url")"
else
  base_url="$(python3 "$project_root/scripts/api_url_policy.py" --kind native "$base_url")"
fi

umask 077
if [ "$allow_remote" -eq 0 ]; then require_api_token; fi

payload_file="$(mktemp "${TMPDIR:-/tmp}/gemmam5-mcp-request.XXXXXX.json")"
header_file="$(mktemp "${TMPDIR:-/tmp}/gemmam5-mcp-header.XXXXXX")"
cleanup() {
  rm -f -- "$payload_file" "$header_file"
}
trap cleanup EXIT HUP INT TERM

python3 - "$request_file" "$model" "$payload_file" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

source = Path(sys.argv[1])
model = sys.argv[2].strip()
destination = Path(sys.argv[3])

if not model:
    raise SystemExit('MODEL_IDENTIFIER must not be empty')

try:
    payload = json.loads(source.read_text(encoding='utf-8'))
except (OSError, UnicodeError, json.JSONDecodeError) as exc:
    raise SystemExit(f'Cannot read valid JSON request template {source}: {exc}') from exc

if not isinstance(payload, dict):
    raise SystemExit('MCP request template must contain a JSON object')

integrations = payload.get('integrations')
if not isinstance(integrations, list) or not integrations:
    raise SystemExit('MCP request template must contain a non-empty integrations list')

mcp_count = 0
for index, integration in enumerate(integrations):
    if not isinstance(integration, dict):
        raise SystemExit(f'integrations[{index}] must be a JSON object')
    if integration.get('type') != 'ephemeral_mcp':
        continue
    mcp_count += 1
    allowed_tools = integration.get('allowed_tools')
    if (
        not isinstance(allowed_tools, list)
        or not allowed_tools
        or any(not isinstance(tool, str) or not tool.strip() for tool in allowed_tools)
    ):
        raise SystemExit(
            f'integrations[{index}].allowed_tools must be a non-empty list of tool names'
        )

if mcp_count == 0:
    raise SystemExit('MCP request template contains no ephemeral_mcp integration')

payload['model'] = model
destination.write_text(
    json.dumps(payload, ensure_ascii=False, indent=2) + '\n',
    encoding='utf-8',
)
PY

create_curl_auth_header_file "$header_file"
headers=(-H 'Content-Type: application/json')
if [ -s "$header_file" ]; then
  headers+=(--header "@$header_file")
fi

if [ "$allow_remote" -eq 1 ]; then
  printf '%s\n' 'WARNING: the MCP request and LM_API_TOKEN, if set, may be sent to a remote endpoint.' >&2
fi
printf 'MCP is disabled by default. Review the server, allowed tools and arguments in %s before sending.\n' "$request_file" >&2
printf 'Target endpoint: %s\n' "$base_url" >&2
printf 'Target model: %s\n' "$model" >&2
curl --fail --silent --show-error \
  --connect-timeout 10 \
  --max-time 180 \
  "${headers[@]}" \
  --data-binary "@$payload_file" \
  "$base_url/chat"
printf '\n'
