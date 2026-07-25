# Assurance case

This document maps the repository's public claims to executable controls. It is an evidence index, not a replacement for the target-Mac acceptance test.

| Claim | Preventive control | Verification evidence |
| --- | --- | --- |
| Exact model profile | Fixed catalog ID, GGUF and Q4_0 gates before download and load | model-discovery and target-profile regressions |
| 24 GB M5 Air operating point | machine-readable hardware, OS, memory and disk preflight | hardware-profile parser regression and target acceptance record |
| One active prediction | `MAX_CONCURRENT_PREDICTIONS=1` and `lms load --parallel 1` | single-prediction regression |
| Local API boundary | numeric loopback bind and listener inspection | listener and server-status regressions |
| Authenticated API | unauthenticated request must fail; token request must succeed | `scripts/verify_api_auth.sh` and auth regression |
| Controlled tools | exact tool name, one call, empty object arguments, fixed executable | constrained-tool regression |
| Restricted MCP | exact native API path and non-empty `allowed_tools` | MCP payload functional regression |
| Safe GitHub identity | effective SSH configuration, exact SSH greeting and exact `gh` login | SSH and publication regressions |
| Exact public repository | owner/name, public visibility, archive state, description and main branch postconditions | GitHub repository JSON validator |
| Deterministic release | manifest-only staging, fixed ZIP metadata, two-build byte comparison and extraction test | release-builder regressions and ZIP sidecar |
| Honest hardware evidence | `not_measured` default and strict measured-record schema | benchmark validator and owner-produced record |

`make verify` executes the static assurance gates. `make benchmark-check` validates the canonical evidence template. Physical performance, swap, thermals and visual results remain unproven until measured on the named Mac.

## New evidence controls in 1.1.240

Visual claims are bound to a PNG manifest and safety-margin validator; performance claims are bound to a prompt digest and repeated-run protocol; screenshot claims are bound to an explicit pending/captured/redacted state; backend support is limited to LM Studio.
