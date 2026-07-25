# Security model

## Local server

Project scripts bind explicitly to `127.0.0.1` and do not enable CORS. Do not replace this address with `0.0.0.0` without API authentication, firewall rules and an explicit client-access decision.

## Tokens

When LM Studio authentication is enabled, pass the token through `LM_API_TOKEN`. Do not store it in tracked configuration, screenshots or shell scripts.

## Tool calling

A model request is not authority to execute. The host must validate the function name, JSON schema, additional fields, time limit, output size and working directory. Never pass a model-supplied string to a shell. The memory-pressure example also restricts its API endpoint to a numeric loopback address unless the operator supplies a separate explicit remote opt-in, and it accepts exactly one call whose arguments decode to an empty JSON object.

## MCP

MCP is off by default. Enable only the server class required for the current test, restrict `allowed_tools`, avoid broad filesystem roots and do not expose SSH keys, browser profiles, password stores, cloud credentials or private documents. The executable MCP request accepts only a numeric loopback native-API endpoint by default; a remote endpoint requires a separate opt-in because request content and the optional `LM_API_TOKEN` leave the machine.

## GitHub SSH

The dedicated alias uses `IdentitiesOnly yes`. The verification script checks both the authentication message and the exact account name `Gendalf71`.

The startup path checks that the installed CLI exposes `--bind`, starts on `127.0.0.1`, and uses `lsof` to reject wildcard listeners such as `0.0.0.0`, `*` or `[::]`.

## Continuous integration

GitHub Actions are pinned to immutable release commit SHAs rather than mutable major tags. Checkout does not persist the workflow token, the job has a finite timeout and Dependabot is configured to propose reviewed action updates.

## Git publication inventory

A clean working tree does not prove that a previous commit contains only release files. `verify_git_inventory.sh` compares the complete Git index with `SHA256SUMS` and is mandatory before an automated push. Publication automation requires repository-local author identity from `.git/config`; inherited global values are not accepted, so this project neither changes nor silently depends on unrelated repository settings.

- Every `SHA256SUMS` path is validated before verification, staging or release copying; path traversal and absolute paths are rejected.

## GitHub publication boundaries

Publication refuses to rewrite an unexpected existing `origin`, rejects archived repositories and rejects a visibility mismatch instead of silently changing repository state. Review any corrective `git remote set-url` or visibility change manually before rerunning automation.

## API client endpoint boundary

The text, vision, constrained-tool and runtime smoke-test clients use fail-closed URL validation. By default they accept only numeric loopback HTTP(S) endpoints whose path ends in `/v1`; embedded credentials, query strings, fragments and non-loopback hosts are rejected before prompts, images, tool results or `LM_API_TOKEN` can be transmitted.

## Listener, shutdown and Release provenance

Every endpoint on the configured port must be loopback-only; one safe listener cannot mask a second LAN listener. Shutdown requires `running=false` and no remaining listener. A GitHub Release must be created from the exact clean commit already present at `origin/main`, with successful CI for that SHA and matching local/remote tag targets.

## Mandatory local API authentication

In LM Studio open **Developer > Server Settings**, enable **Require Authentication**, and create a least-privilege API token. Load it into the current Terminal without adding it to shell history:

```bash
read -s LM_API_TOKEN
export LM_API_TOKEN
printf '\n'
```

`start_server.sh` enforces `REQUIRE_API_AUTH=1`, proves that an unauthenticated request is rejected and that the token-authenticated request succeeds. Shell clients use an owner-only temporary header file so the token is not placed in `curl` command-line arguments.

## Non-weakenable target profile

`config/local.conf` may carry reviewed local tuning or stricter thresholds. Operational scripts reject attempts to disable API authentication, lower the 24 GB memory, 35 GB free-space or macOS 26.0 floors, change the MacBook Air M5/Q4_0 target, expose the bind address or raise concurrent predictions above one.

Server startup refuses a pre-existing LM Studio server. If a post-start listener or authentication check fails, the startup script attempts to roll back the server it started and reports any rollback failure for explicit inspection.

## Configuration integrity

Before any secure-profile command reads values, the complete default and local configuration is validated. Unknown or duplicate keys, malformed/CRLF/control-character lines, symlinks and group/world-writable files are rejected. `config/local.conf` should normally be mode 0600.
