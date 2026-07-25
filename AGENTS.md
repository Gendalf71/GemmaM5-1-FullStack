# Repository agent contract

This file defines the safe change boundary for human and automated contributors.

1. Do not add model weights, API tokens, private keys, local paths, hardware reports or unredacted screenshots.
2. Keep `VERSION`, `CITATION.cff`, operational documentation and versioned audit records synchronized.
3. Run `make verify` before proposing a change. Release changes also require `make package`.
4. Runtime claims must be tied to owner-captured evidence; templates remain `not_measured` and `not_captured`.
5. Network publication is explicit. Dry-run and local validation must precede `--execute`.
6. Preserve loopback-only defaults, required API authentication, exact model identity and single-prediction constraints.
7. Do not weaken immutable GitHub Action pins, checksum manifests, safe ZIP inventory or SSH account checks.

The repository is an auditable deployment profile, not a new inference engine and not a substitute for physical MacBook Air M5 acceptance.
