# Security policy

Do not report credentials, private keys, API tokens or confidential documents in public issues.

Project scripts bind the API to localhost, verify LM Studio server state and the loopback listener, do not enable CORS and never execute a model-provided shell string. Model loading and repository publication require explicit execution flags; unloading other models requires an additional explicit request and confirmation. MCP API requests and optional bearer tokens stay on numeric loopback unless a separate remote opt-in is supplied. Publication refuses to rewrite an unexpected existing origin or silently change repository visibility.

After publication, use GitHub private vulnerability reporting when available.

GitHub Actions are pinned to reviewed release commit SHAs, checkout credential persistence is disabled, and Dependabot proposes subsequent updates.
