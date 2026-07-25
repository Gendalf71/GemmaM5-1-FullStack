# Threat model

Repository version: 1.1.240

## Protected assets

GitHub SSH keys, API tokens, local file paths, private documents, model provenance, the integrity of the selected model identity and the localhost execution boundary.

## Principal threats

1. A lookalike model catalog entry or quantization is selected.
2. Prompt injection attempts to turn model output into a shell command or unsafe MCP action.
3. The API binds beyond loopback or runs without authentication.
4. A writable, malformed or symlinked configuration changes policy.
5. A release archive contains undeclared files, weights, secrets or path traversal.
6. A mutable or stale CI action pin makes a green workflow misleading.
7. Owner screenshots or reports disclose personal paths, tokens or document content.

## Controls

Exact model identity, fail-closed configuration grammar, fixed read-only tool invocation, MCP allowlists, loopback/auth gates, immutable GitHub Action commits, manifest-only staging, deterministic ZIP validation, owner-only 0600 evidence artifacts and explicit redaction review.

## Residual risk

LM Studio, its runtimes and upstream model files remain third-party components. Static checks do not prove future source availability, absence of upstream vulnerabilities or physical M5 performance. Review external releases before updating and repeat owner acceptance after every runtime, model or macOS change.
