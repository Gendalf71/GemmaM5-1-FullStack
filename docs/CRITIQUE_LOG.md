# Engineering review log

## Clean-room correction of the 1.1.30 verdict and cycles 1.1.31–1.1.45

The new audit rejected the previous zero-finding conclusion. The release-blocking cause was an incorrect identity abstraction: current `lms load --exact` requires `ModelInfo.path`, while the repository passed `modelKey`. A second serious issue was the LM Studio 0.4.1 floor, which preceded the updated Gemma 4 chat template added in 0.4.11.

Versions 1.1.31–1.1.45 replaced model-key-only discovery with a unique local path/modelKey pair, added pre/postcondition checks and rollback by exact identifier, raised the minimum to 0.4.11 with 0.4.20 recommended, synchronized bilingual documentation and canonical repository identity, and added regressions that reproduce the two original failures. The complete release gate and clean-extraction rerun end with zero critical findings.

## Baseline package 1.0.0

Static syntax, JSON, unit tests and local links passed. The package already had strong memory discipline, dry-run publication, a constrained tool example and a clear separation between static and hardware acceptance.

## Revision cycle 1

Critical findings: 7.

1. SSH verification accepted any authenticated GitHub account.
2. GitHub CLI publication did not verify that `gh` was authenticated as Gendalf71.
3. Server startup relied on an implicit local bind instead of passing `127.0.0.1` explicitly.
4. Russian documentation was not isolated under `docs/ru/` despite an international primary README.
5. The requested unload-other-models path did not exist.
6. Dependency maintenance and community conduct files were absent.
7. The repository had no structured target-hardware result template.

All seven were corrected.

## Revision cycle 2

Critical findings: 3.

1. Relative fixture paths made vision examples dependent on the current directory.
2. Version consistency and local Markdown links were not enforced by unit tests.
3. The environment collector could expose excessive model-list output.

All three were corrected: fixture paths are repository-relative, tests enforce metadata and links, and environment output is reduced to the target model fields.

## Revision cycle 3

Critical findings: 0.

Bash and Python syntax, JSON, unit tests, checksums, executable bits, local links, version metadata, safe bind defaults, exact GitHub account validation and package contents were rechecked. Hardware acceptance on the physical Mac remains mandatory and is not classified as a repository defect.

## Revision cycle 4

Critical findings: 0. Polish findings: 3. Russian architecture/troubleshooting were fully localized, a Russian MCP guide and index were added, and server startup gained CLI capability and post-start listener verification.

## Revision cycle 5

Critical findings: 1 during test-design validation. A release-package test initially rejected any `.git` directory, which would have broken the documented publication script after `git init`. The test now validates the release inventory and checksum manifest instead, so verification remains valid both in an extracted package and in a normal Git checkout. Final critical findings: 0.

## Revision cycle 6

Critical findings: 2 during artifact-level review.

1. A raw `hardware-environment.txt` could be created in the repository root and then enter the first broad `git add .`; local reports now live under ignored `artifacts/`, and loaded-model inventory is filtered to the target model.
2. The repository described GitHub releases but had no self-verifying release builder. `scripts/build_release.sh` now stages only the checksum manifest inventory, preserves executable modes, creates two fixed-metadata ZIPs and requires byte identity, extracts the accepted archive, reruns verification, and emits a SHA-256 sidecar.

Polish from the supplied review was also completed: owner-only canonical benchmark wording, an explicit no-fabricated-screenshot policy, release documentation and stronger Markdown fragment validation. Final critical findings after recheck: 0.

## Revision cycle 7

Critical findings: 1 during literal execution of the packaged SSH guide. The release ZIP extracts to `GemmaM5-1-FullStack-1.1.1`, while one guide still changed directory to the unversioned `GemmaM5-1-FullStack`. Both language guides now use the actual package root, and the unit suite derives and verifies that directory from `VERSION`. Final critical findings after recheck: 0.
## Cycle 6 — release 1.1.2

A literal first-publication simulation found that `git add .` could stage an unexpected non-ignored local file. Publication now stages only the checksum-manifest inventory and fails on any additional untracked path. Environment-report examples now consistently write to ignored `artifacts/`. The release ZIP uses stored entries so its bytes do not depend on a Deflate implementation, and CI was moved from older major tags to the then-selected v6 releases of the official checkout and Python setup actions. Regression tests cover all four conditions.

## Revision cycle 8

Critical findings during current-state verification: 1.

The CI regression test still described the v6 majors of `actions/checkout` and `actions/setup-python` as current, although both projects released v7 on 20 July 2026. The workflow now uses the verified v7 release commits, pins them by full SHA, disables persisted checkout credentials and adds a finite job timeout. Version-consistency checks now cover the current release and screenshot documents. Final critical findings after the complete recheck: 0.

## Revision cycle 9

Critical findings during state-transition testing: 3.

1. `verify_repo.sh` accepted a clean existing commit containing a tracked file outside `SHA256SUMS`; a new Git inventory verifier now compares the entire index with the release manifest and is enforced in CI and before push.
2. Publication required global Git identity, creating an unnecessary side effect across unrelated repositories; documentation now uses repository-local identity and automation checks the effective local-or-inherited values.
3. Failure of the exact LM Studio catalog reference silently opened an interactive choice; manual fallback is now explicit and the resulting local model key is verified.

Repository metadata is also applied automatically after push, and release creation requires the already-pushed tag. Final critical findings after recheck: 0.

Manifest trust boundary: release operations now reject absolute, traversal-bearing, backslash-containing, control-character and self-referential paths before any file access. A functional regression test proves that `../outside-secret.txt` cannot be accepted.

## Revision cycle 10

Critical findings during independent exactness and failure-mode review: 4.

1. Model discovery accepted another Gemma 4 26B A4B QAT quantization when Q4_0 was absent; discovery now requires the exact QAT, GGUF and Q4_0 evidence and fails closed.
2. Manifest validation did not reject every embedded `.` component and did not require unique, sorted canonical entries; a dedicated parser now validates the complete manifest before verification, staging, inventory comparison or packaging.
3. Loopback listener verification could be skipped when `lsof` was unavailable and could race server startup; it is now mandatory and retried for a bounded interval.
4. `gh repo create --source . --remote origin` unnecessarily coupled remote repository creation to local remote mutation and could conflict with an existing `origin`; repository creation and remote configuration are now separate operations.

All four conditions are covered by regression tests. Final critical findings after artifact and publication simulation: 0.

## Revision cycle 11

Critical findings during executable-example review: 1.

The MCP request example read `MODEL_IDENTIFIER` and printed it, but sent the unchanged template whose `model` field remained `gemma4-local`. The script now resolves its default template relative to the repository, creates a temporary payload, validates that every ephemeral MCP integration has a non-empty `allowed_tools` list, applies the selected model identifier and removes the temporary file after the request. A functional fake-`curl` regression test verifies both model substitution and fail-closed allowlist validation. Final critical findings after recheck: 0.
## Cycle 10: exact-profile override audit

The 1.1.5 scripts strictly discovered Q4_0 by default, but an exported `MODEL_KEY` bypassed that discovery before estimate/load, and a local configuration could retarget the download to another catalog entry or quantization before failing later. Version 1.1.6 validates overrides against the installed LM Studio inventory and rejects any catalog/quantization change before network activity. Variant-aware human-output fallback now prefers `lms ls --variants`. Final critical findings after recheck: 0.

## Revision cycle 12

Critical findings during publication-identity and tool-host review: 2.

1. Publication documentation promised repository-local Git identity, but the automation read effective values and therefore accepted inherited global `user.name` and `user.email`. It now requires both values from the repository-local `.git/config`, and a functional regression test proves that global-only identity is rejected.
2. The read-only tool example accepted any `--base-url` and treated falsy non-object JSON values such as `[]`, `null` or `false` as an empty argument object. It now restricts the endpoint to numeric loopback addresses unless a separate explicit remote opt-in is supplied, requires exactly one approved call with a non-empty ID, and accepts only arguments that decode to an empty JSON object.

Final critical findings after recheck: 0.

During the final publication simulation, the new identity regression test itself was found to copy `.git` from an already initialized source checkout. The test is now hermetic and excludes Git metadata, release output, local artifacts and Python caches before asserting global-only rejection.

## Revision cycle 13

Critical findings during repeat-publication and current-CLI review: 4.

1. An existing unexpected `origin` was silently rewritten to the canonical SSH URL. Publication now fails closed and requires the user to review any corrective `git remote set-url` command explicitly.
2. Model discovery relied on plain JSON and human-readable variant output even though current `lms ls` exposes a machine-readable `--json --variants` inventory. The variant-aware JSON path is now preferred, exact quantized keys outrank base model keys, and deprecated `--detailed` output is no longer used.
3. The MCP request example accepted `LM_NATIVE_BASE_URL` from the environment and could transmit request content or `LM_API_TOKEN` to a remote endpoint without a separate opt-in. Numeric loopback is now the default trust boundary; remote delivery requires `--allow-remote-base-url` and emits a disclosure warning.
4. Server startup printed `lms server status` with errors ignored. It now requires machine-readable status to confirm `running=true` on the configured port before the independent loopback-listener check.

Existing GitHub repositories are also inspected for archived state and exact requested visibility; neither condition is changed implicitly. Final critical findings after deterministic packaging and publication simulation: 0.

## Cycle 14

Critical findings: mixed loopback-plus-LAN listeners were accepted; text, vision and smoke-test clients lacked a shared remote-endpoint gate; server stop/status suppressed material failures; and manual Release steps did not prove the tag targeted the successful `origin/main` commit. Version 1.1.9 validates every listener endpoint, protects all OpenAI-compatible clients, verifies shutdown and API readiness, and adds a guarded dry-run Release script. The duplicated changelog heading was corrected. Final critical findings after packaging and publication/release simulation: 0.

## Revision cycle 15

- Replaced the monolithic unittest runner with bounded individual results and isolated the LM Studio status regression in a separate process.

- Added explicit subprocess deadlines to the server-status regression test so a broken mock or CLI cannot stall CI indefinitely.

## Cycle for 1.1.10

Critical findings: the bounded test runner still executed most tests in one interpreter and reproducibly stalled after subprocess-heavy cases, so its nominal per-test timer did not guarantee completion; the Release helper also trusted the successful CLI exit without checking the resulting Release state and asset inventory. Version 1.1.10 executes every test in a separate process group with a hard timeout and diagnostic ranges, then verifies the created GitHub Release tag, publication state and both expected assets. Final critical findings after clean extraction, deterministic packaging, Git publication and Release simulation: 0.

## Cycle for 1.1.11

Independent audit against the current public structure of `drumih/turbo-fieldfare` and the documented LM Studio model workflow found one serious documentation issue and one usability issue. The headline called the deployment reproducible even though the external LM Studio catalog artifact is revisioned and not pinned by a repository-controlled weight digest; the Makefile also lacked the conventional `test` target. Version 1.1.11 narrows the claim to a repeatable and auditable configuration, documents the immutable-repository versus mutable-model boundary, adds privacy-filtered provenance capture, exposes `make test` and `make provenance`, and makes the structural comparison explicit without copying TurboFieldfare implementation or assets. Final critical findings after isolated tests, clean extraction, deterministic packaging and publication/release simulation: 0.

A second audit found one cosmetic extraction-path inconsistency: the fallback `chmod` command restored shell entry points but not executable Python entry points. The command and its regression check now cover both file types. Critical findings remained 0.

## Cycle for 1.1.12

A fresh comparison against the current LM Studio documentation found one serious operating-profile inconsistency: the repository stated one concurrent prediction, but version 1.1.11 did not pass a loader flag, while supported LM Studio llama.cpp runtimes default Max Concurrent Predictions to 4. Version 1.1.12 requires the `lms load --parallel` capability, raises the documented minimum to LM Studio 0.4.1, adds a fail-closed `MAX_CONCURRENT_PREDICTIONS=1` setting and passes `--parallel 1` on every project-controlled load. Preflight now detects an older CLI before a model run. A Russian structural comparison with TurboFieldfare and explicit regression coverage were also added. Final critical and serious findings after repeated verification: 0.

## Fresh cycle for 1.1.13

A clean-room version-boundary audit found that packaging and Release scripts accepted any string composed of digits and dots, including malformed values such as `1..13`. Several functional tests also embedded the previous version literally. Version 1.1.13 introduces one canonical `X.Y.Z` parser, uses it in every release-sensitive shell path and derives test asset names from `VERSION`. Critical findings after recheck: 0.

## Fresh cycle for 1.1.14

A new trust-boundary audit found three independent URL parsers. The constrained-tool and MCP variants did not enforce the complete canonical policy used by the text, vision and smoke-test clients; in particular, the native MCP path could be noncanonical. Version 1.1.14 routes every example through one policy module and requires exact API path, valid port, no credentials, no query or fragment, no controls and numeric loopback unless remote delivery is explicitly enabled. Critical findings after recheck: 0.

## Fresh cycle for 1.1.15

A process-boundary security audit found that localhost alone did not prove LM Studio authentication was enabled, and two shell clients exposed `LM_API_TOKEN` in `curl` arguments visible to same-user process inspection. Version 1.1.15 makes API authentication part of the target profile, verifies the unauthenticated and authenticated HTTP postconditions, and supplies tokens to curl through owner-only temporary header files. Critical findings after recheck: 0.

## Fresh cycle for 1.1.16

A clean target-definition audit found that preflight accepted any arm64 Mac with enough memory, although the repository is presented specifically for a MacBook Air M5. It also printed but did not enforce an operating-system floor. Version 1.1.16 parses `system_profiler` JSON, requires the exact product family and M5 token, enforces arm64, memory and macOS 14.0, and classifies other Macs as outside the validated profile. Critical findings after recheck: 0.

## Fresh cycle for 1.1.17

A new SSH identity audit found that matching GitHub's greeting did not prove the alias resolved to the intended host, key and direct connection. A duplicated Host block or proxy setting could alter the effective configuration. Version 1.1.17 checks `ssh -G` before connecting and requires github.com, user git, the dedicated key, IdentitiesOnly and no proxy. The guides now prohibit duplicate aliases. Critical findings after recheck: 0.

## Fresh cycle for 1.1.18

A publication-state audit found an inconsistent contract: the publication helper advertised a private mode while the Release helper, README badges and requested project profile required a public repository. Successful `gh` commands also lacked a final identity postcondition. Version 1.1.18 supports the public profile only and validates exact owner/name, visibility, archived state, description and default branch after creation and after editing. Critical findings after recheck: 0.

## Fresh-sheet cycle for version 1.1.19

Critical findings: 1. The benchmark template was intentionally unmeasured, but its state and completeness were not machine-enforced; a hand-edited file could therefore look canonical while containing fabricated or internally inconsistent numbers. Version 1.1.19 adds a fail-closed benchmark validator, binds the evidence to the exact repository and hardware/model profile, and records an assurance case linking claims, controls, tests and residual hardware uncertainty. Critical findings after correction: 0.

## Fresh-sheet terminal cycle for version 1.1.20

Critical findings: 1. The `make test` target was an alias for the larger verification pipeline rather than a semantically direct regression-test entry point, and no standalone fail-closed check rejected a stale current-version reference across every operational document. Version 1.1.20 makes `make test` invoke the isolated regression runner directly, adds `make version-check`, integrates version-reference validation into `verify_repo.sh`, and functionally proves rejection of a stale document. Critical findings after correction: 0.

### Additional terminal recheck within 1.1.20

Critical findings: 2. A reviewed local configuration could still lower memory, disk and macOS safeguards or set `REQUIRE_API_AUTH=0`, contradicting the declared secure profile. In addition, the release-version reader removed all whitespace before validation and therefore accepted malformed content such as `1.1. 20`. The final 1.1.20 introduces a shared non-weakenable target-profile gate across preflight, download, estimate, load, server and authentication paths, makes authentication unconditional, and validates the literal VERSION content without whitespace normalization. Functional regressions prove the rejection paths. Critical findings after correction: 0.

### Startup rollback recheck within 1.1.20

Critical finding: 1. If listener or authentication postconditions failed after `lms server start`, the script exited but could leave the newly started server running; this was especially undesirable when authentication itself was the failed postcondition. The final startup path now refuses to take over a pre-existing server and installs a rollback trap that stops only the server it started when any subsequent postcondition fails. A functional mock regression proves the stop call. Critical findings after correction: 0.

### GitHub metadata postcondition recheck within 1.1.20

Serious finding: 1. Publication verified repository identity, visibility, archive state, description and default branch, but trusted the exit status of `gh repo edit --add-topic` without proving that every canonical topic was present. The final postcondition now reads `repositoryTopics` and validates the required topic set machine-readably. Serious findings after correction: 0.

## Independent corrective cycles 1.1.21–1.1.30

A new clean-room review rejected the previous zero-finding conclusion as an input and repeated the technical and publication audit. Ten bounded corrective releases addressed current `lms` option drift, exact/local model selection, post-load identity, canonical GPU validation, exact M5 Air identifiers and macOS generation, truthful evidence wording, HTTPS for remote opt-in, bounded parallel tests, existing-repository release updates, CLI contract verification and final metadata reconciliation. The complete rationale and residual limits are in [FINAL_AUDIT.md](FINAL_AUDIT.md). Critical findings after version 1.1.30 verification: 0.

## Independent corrective cycles 1.1.31–1.1.45

A second clean-room audit began from the supplied 1.1.30 archive and treated the requested repository name and terminal version as new constraints. Fifteen bounded cycles corrected canonical identity, package naming, current macOS documentation, evidence wording, external model provenance, API/MCP boundaries, public presentation, SSH and GitHub postconditions, regression coverage, deterministic packaging and final metadata. The detailed finding-to-correction matrix is in [FINAL_AUDIT.md](FINAL_AUDIT.md). Critical findings after the extracted 1.1.45 release was reverified: 0.

## Clean-room correction 1.1.46

A new review of the supplied 1.1.45 release invalidated its zero-critical-finding claim: the resolver named the exact Google catalog ID but did not enforce it. Version 1.1.46 requires the catalog part of `modelKey` to equal `google/gemma-4-26b-a4b-qat`, adds a third-party lookalike rejection test, reconciles publication metadata and SSH diagnostics, completes benchmark evidence fields, and records the requested 15 by 15 static review matrix. See [FINAL_AUDIT.md](FINAL_AUDIT.md).

## Sequential clean-room revisions 1.1.47–1.1.59

The independent restart from 1.1.46 produced thirteen bounded engineering revisions before the final 1.1.60 closure. The canonical machine-readable record is `docs/audit/revision-ledger-1.1.60.json`. Each entry names the finding, correction and targeted validation; the record explicitly does not represent independent human reviews or physical M5 benchmarks.

## Closure 1.1.61–1.1.90

A second clean-room pass rejected one visible presentation defect (banner overflow) and identified evidence gaps that were important but not hardware claims: source indexing, visual regression, owner report privacy, integrated acceptance, backend boundary, benchmark protocol and screenshot state. Ten bounded revisions closed them without inventing M5 measurements. The terminal status is zero unresolved critical findings.

## Clean-room revisions 1.1.71–1.1.90

A fresh audit of 1.1.70 found two critical false-positive assurance defects: M4 Apple pages were cited as M5 evidence, and CI tests blessed non-existent GitHub Action releases. Versions 1.1.71–1.1.90 correct the primary-source ledger, immutable CI pins, LM Studio source attribution, strict configuration grammar, bilingual audit, 18 by 18 matrix and deterministic release closure. The canonical record is `docs/audit/revision-ledger-1.1.90.json`. Remaining critical findings: 0.
