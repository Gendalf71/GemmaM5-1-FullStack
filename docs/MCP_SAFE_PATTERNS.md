# Safe MCP patterns

MCP expands the trust boundary beyond the model and LM Studio. Start with the smallest useful capability.

## Recommended first test

Use a public, read-only remote search server with exactly one allowed tool, as shown in `config/mcp_request.example.json`. Do not include credentials in the JSON file.

## Permission classes

| Class | Default | Review requirement |
| --- | --- | --- |
| Public read-only search | Disabled | Verify server identity, URL and tool schema |
| Single project directory read | Disabled | Pin one directory; reject `..` and symlinks outside it |
| Browser navigation | Disabled | Separate profile; no saved passwords; explicit domain policy |
| Email, calendar or cloud storage | Disabled | Authentication, least privilege and confirmation for writes |
| Shell or process execution | Prohibited by this repository | Requires a separate sandboxed design |

For every MCP request, specify `allowed_tools`. If the field is omitted, the model may receive every tool exposed by that server.
## Executable example

With the local server running, review the tracked template and send it with:

```bash
MODEL_IDENTIFIER=gemma4-local ./examples/mcp_request.sh
```

The executable request is local-only by default. `LM_NATIVE_BASE_URL` must resolve to a numeric loopback address unless `--allow-remote-base-url` is supplied explicitly. Remote opt-in means the request body and `LM_API_TOKEN`, if configured, leave the Mac; review that endpoint as a separate security boundary.

```bash
LM_NATIVE_BASE_URL=https://203.0.113.1/api/v1 \
  ./examples/mcp_request.sh --allow-remote-base-url
```

The script resolves the default template relative to the repository, requires at least one `ephemeral_mcp` integration, rejects an empty `allowed_tools` list and writes the selected model identifier only into a temporary request payload. The tracked JSON template is not modified. An explicit alternative template path may be passed as the first argument.
