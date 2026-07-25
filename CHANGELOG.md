# Changelog

## 1.1.240 - 2026-07-24

- Performed a new clean-room audit of the supplied 1.1.150 package without access to the owner GitHub account.
- Replaced the ineffective whitespace gate with an independent UTF-8/text-quality validator and removed bytecode-producing syntax checks.
- Made LM Studio upgrades explicit, corrected all 0.4.20 fallbacks, required authenticated API examples, and validated image signatures and size bounds.
- Strengthened primary-source, release-assurance, repository-agent, issue-template and deterministic-package controls.
- Recorded versions 1.1.151-1.1.240 as sequential targeted engineering revisions; they are not independent human reviews or physical hardware benchmarks.
- Closed 90 x 24 bounded static controls with zero unresolved critical or major static findings; physical M5 runtime acceptance remains owner work.

## 1.1.150 - 2026-07-24

- Re-pinned GitHub Actions to immutable checkout v7.0.1 and setup-python v7.0.0 releases.
- Recommended LM Studio 0.4.20 while preserving the audited 0.4.11 minimum.
- Added explicit M5 documentation-lag, owner-acceptance, threat-model, GitHub-metadata, source-ledger and release-assurance boundaries.
- Expanded the bounded matrix to 60 × 20 controls and closed the terminal clean-extraction release cycle with zero critical or major static findings.

## 1.1.90 - 2026-07-24

- Corrected Apple M5 and LM Studio primary-source URLs and added exact high-risk source contracts.
- Replaced fabricated GitHub Actions v7 pins with immutable official checkout v6.0.2 and setup-python v6.2.0 release commits.
- Added pinned LM Studio CLI implementation evidence for hidden `--exact` and `--local` flags.
- Added complete fail-closed configuration grammar, duplicate/unknown-key and unsafe-mode rejection.
- Expanded the repeated static review matrix to 18 by 18 (324 controls).
- Rewrote the bilingual final audit and regenerated the deterministic release records.

# Changelog

## 1.1.70 - 2026-07-24

- Regenerated every release record, executed the 15 by 15 matrix, rebuilt the sorted SHA-256 manifest and created byte-identical validated archives.

## 1.1.69 - 2026-07-24

- Added targeted static and functional regressions and integrated the visual gate into verify_repo.

## 1.1.68 - 2026-07-24

- Reworked README navigation, evidence-status badge, quick commands and repository map without copying runtime claims.

## 1.1.67 - 2026-07-24

- Added a screenshot evidence template and a directory that refuses generated substitutes for owner captures.

## 1.1.66 - 2026-07-24

- Extended the benchmark protocol and validator with profile ID, run count, prompt digest, cold-start state and disaggregated rates.

## 1.1.65 - 2026-07-24

- Added bilingual backend-portability guidance that explicitly limits the verified implementation to LM Studio.

## 1.1.64 - 2026-07-24

- Added a local UTF-8 document plus image request followed by the existing fixed read-only memory-pressure tool.

## 1.1.63 - 2026-07-24

- Added an owner-only hardware report command that writes an ignored 0600 artifact and requires review before publication.

## 1.1.62 - 2026-07-24

- Redrew the banner and architecture diagram with protected margins and added a standard-library PNG dimension/margin validator.

## 1.1.61 - 2026-07-24

- Expanded the machine-readable evidence ledger with current primary sources and bounded claims.

## 1.1.60 - 2026-07-24

- Closed the requested version sequence with canonical complete ZIP ordering, a positive deterministic ZIP round-trip, final bilingual audits and the full release/clean-extraction verification chain.

## 1.1.59 - 2026-07-24

- Added a canonical machine-readable ledger for the sequential 1.1.47–1.1.59 findings, corrections, targeted checks and zero-critical closure status.

## 1.1.58 - 2026-07-24

- Reworked public onboarding to the same evidence-first class as the structural reference: a safe Try-it path, explicit is/is-not boundary, repository map, stronger Russian entry point and a dated structural comparison.

## 1.1.57 - 2026-07-24

- Added a versioned machine-readable ledger of primary external sources and bounded claims used by the audit, without vendoring or pretending to perform offline hardware validation.

## 1.1.56 - 2026-07-24

- Added an exact one-line checksum-sidecar validator and applied it during packaging and guarded GitHub Release creation.

## 1.1.55 - 2026-07-24

- Added reusable validation of repository-local Git author identity and rejection of placeholders, malformed addresses and control characters before publication or tagging.

## 1.1.54 - 2026-07-24

- Made the exact-account SSH probe non-interactive and bounded, with strict host-key checking and mandatory known-host verification.

## 1.1.53 - 2026-07-24

- Added fail-closed verification of the persisted `github.com` Ed25519 host key against GitHub's published fingerprint; unauthenticated `ssh-keyscan` output is explicitly insufficient.

## 1.1.52 - 2026-07-24

- Integrated exact ZIP structural/inventory validation into both independently built archives and documented the same pre-extraction check.

## 1.1.51 - 2026-07-24

- Added a fail-closed release ZIP validator for canonical paths, one exact package root, deterministic timestamps, stored entries, Unix regular-file types, exact manifest inventory, checksums and modes.

## 1.1.50 - 2026-07-24

- Made the LM Studio compatibility warning read the audited repository version from `VERSION` instead of embedding a stale release number.

## 1.1.49 - 2026-07-24

- Removed brittle hard-coded matrix paths; verification, Make targets and tests now derive the matrix filename from `VERSION`.

## 1.1.48 - 2026-07-24

- Added explicit subprocess timeouts and clear timeout failures to the repeated static review matrix.

## 1.1.47 - 2026-07-24

- Corrected the Q4_0 size statement to the official LM Studio catalog value, 15.60 GB (about 14.53 GiB), and separated download, disk and resident-memory units.


## 1.1.46 - 2026-07-24

- Fixed a clean-room fail-closed gap in model discovery: a Q4_0 lookalike from a different catalog publisher can no longer satisfy the exact Gemma identity gate.
- Made the isolated regression runner process bounded batches, eliminating whole-suite executor stalls observed during clean-room verification.
- Added a regression requiring the catalog portion of `modelKey` to equal `google/gemma-4-26b-a4b-qat`, while retaining variant-qualified keys such as `@q4_0`.
- Added explicit current-release positioning, a no-model-weights GitHub description, broader discovery topics, SSH backup/agent troubleshooting, and complete benchmark fields for macOS build and thermal state.
- Reconciled both language trees, executed the requested 15 by 15 static review matrix, rebuilt checksums and reverified the final deterministic archive after clean extraction.

## 1.1.45 - 2026-07-24

- Invalidated the previous zero-finding conclusion after a new clean-room audit of the 1.1.30 archive.
- Corrected the LM Studio exact-load chain: the resolver now returns a verified local `ModelInfo.path`/`modelKey` pair, and estimate/load pass only the path to `lms load --exact` while independently checking the modelKey.
- Made loading transactional and strictly idempotent: identifier/path/modelKey conflicts and duplicates fail before mutation; one fully matching instance is the only accepted no-op; failed partial loads are rolled back by exact identifier.
- Raised the application floor to LM Studio 0.4.11 for the updated Gemma 4 chat template and recommend 0.4.19 or newer, while retaining capability-based CLI checks.
- Added regression coverage for exact path semantics, model-key overrides, ambiguity, remote entries, pre/postconditions, rollback, canonical repository identity and bilingual version floors.
- Renamed every operational repository reference and release asset to `Gendalf71/GemmaM5-1-FullStack`, synchronized macOS 26.0 documentation, and rebuilt the deterministic release evidence.
## 1.1.30 - 2026-07-24

- Re-audited the complete 1.1.20 archive from a clean extraction and documented corrective cycles 1.1.21 through 1.1.30.
- Updated model download compatibility for current `lms get --select` while retaining feature-detected legacy fallback.
- Made estimate and load fail closed with exact/local selection and verified the loaded model identity and single-prediction postcondition.
- Rejected invalid GPU offload values, restricted the target to MacBook Air M5 identifiers `Mac17,3`/`Mac17,4` on macOS 26+, and required HTTPS for remote API opt-in.
- Added a machine-readable LM Studio CLI contract check, bounded parallel regression execution, and safe publication of reviewed updates to an existing Git repository.
- Added bilingual compatibility and final-audit documents and rebuilt deterministic release metadata.

## 1.1.20 2026-07-24

- Separated the standard `make test` regression target from the complete repository verification gate.
- Added fail-closed operational version-reference validation across release, installation, screenshot, citation and benchmark documents.
- Added a functional regression proving that a stale version in an operational document is rejected before packaging or publication.
- Completed eight fresh-sheet review cycles from 1.1.12 through the required terminal version 1.1.20.
- Made the secure target profile non-weakenable by local configuration and made release-version parsing reject embedded or leading whitespace.
- Made server startup transactional: reject pre-existing state and roll back a newly started server when listener or authentication postconditions fail.
- Extended GitHub publication postconditions to verify every canonical repository topic after metadata updates.

## 1.1.19 2026-07-24

- Added a machine-validated benchmark evidence schema that rejects fabricated, incomplete or profile-mismatched measurements.
- Added an assurance case mapping each major claim to its enforcing mechanism, regression evidence and remaining hardware limitation.
- Kept the canonical benchmark in an explicit `not_measured` state until the repository owner performs the M5 hardware acceptance.

## 1.1.18 2026-07-24

- Removed the ambiguous private-public publication split and made the requested public repository profile the only supported automated path.
- Added machine-readable GitHub repository postcondition validation for exact owner/name, public visibility, non-archived state, canonical description and `main` default branch.
- Re-inspect the repository after creation and after metadata changes instead of trusting successful CLI exit codes alone.

## 1.1.17 2026-07-24

- Hardened GitHub SSH verification by inspecting the effective `ssh -G` configuration before network authentication.
- Required `HostName github.com`, `User git`, the exact dedicated identity, `IdentitiesOnly yes`, and no ProxyCommand or ProxyJump.
- Updated bilingual SSH instructions to reject duplicate aliases and document the exact-key validation path.

## 1.1.16 2026-07-24

- Made preflight hardware acceptance specific to the requested MacBook Air M5 profile instead of treating every 24 GB Apple Silicon Mac as equivalent.
- Added machine-readable `system_profiler` JSON parsing, exact MacBook Air and M5 checks, arm64 and 24 GiB gates, and a documented macOS 14.0 minimum.
- Added a standalone tested hardware-profile parser and bilingual scope guidance for compatible-but-unvalidated Macs.

## 1.1.15 2026-07-24

- Made local API authentication mandatory for the secure target profile and added a post-start proof that unauthenticated access is rejected while token-authenticated access succeeds.
- Added `scripts/verify_api_auth.sh`, `make auth-check`, `REQUIRE_API_AUTH=1` and bilingual setup guidance.
- Removed bearer tokens from shell `curl` command-line arguments by using owner-only temporary header files with deterministic cleanup.

## 1.1.14 2026-07-24

- Unified OpenAI-compatible, constrained-tool and native MCP endpoint validation in one fail-closed URL-policy module.
- Required exact `/v1` or `/api/v1` paths, valid ports, no credentials, no query/fragment and no control characters before request data is read or sent.
- Removed duplicated endpoint parsers from the tool and MCP examples and added functional regression coverage for native-API path rejection.

## 1.1.13 2026-07-24

- Replaced permissive dotted-number checks with one canonical three-component release-version policy shared by packaging, publication, provenance and Release tooling.
- Removed hard-coded current-version literals from functional tests so release validation derives names and tags from `VERSION`.
- Added regression coverage for canonical `X.Y.Z` syntax and rejected malformed versions such as `1..13` or `01.1.13`.

## 1.1.12 2026-07-24

- Enforced the declared 24 GB operating point with `lms load --parallel 1` instead of relying on LM Studio's higher default parallelism.
- Added fail-closed `MAX_CONCURRENT_PREDICTIONS=1` configuration and preflight feature detection for LM Studio 0.4.1 or newer.
- Added explicit regression coverage for single-prediction enforcement and CLI capability checks.
- Added a Russian structural comparison with TurboFieldfare and clarified the external-runtime boundary.
- Expanded installation, validation, troubleshooting and reference documentation around parallel-request memory risk.
- Repeated static, deterministic-package, extraction and publication/release checks.

## 1.1.11 2026-07-24

- Replaced the ambiguous top-level reproducibility claim with a precise repeatable-and-auditable configuration boundary.
- Added privacy-filtered model provenance capture and bilingual provenance documentation.
- Added standard `make test` and `make provenance` entry points.
- Completed the extraction fallback command so Python entry points regain executable bits together with shell scripts.
- Added an explicit structural comparison with TurboFieldfare and the official upstream QAT GGUF reference.
- Re-ran isolated static tests, deterministic package checks and publication/release simulations.

## 1.1.10 2026-07-23

Test-runner and Release-postcondition hardening: execute every repository regression in its own bounded process group so shared interpreter state cannot stall verification; add optional index ranges for deterministic diagnostic shards; and verify after `gh release create` that the published Release is non-draft, non-prerelease, has the exact expected tag and contains both the deterministic ZIP and its SHA-256 sidecar.

## 1.1.9 2026-07-23
- Run repository regressions with a hard 60-second per-test deadline and isolate the LM Studio status regression in a separate process, preventing subprocess-state interactions from stalling CI.
- Bounded server-status regression subprocesses with explicit timeouts so CI cannot hang indefinitely.

Final network and release-boundary hardening: require every listener on the configured port to be a numeric loopback address, verify server shutdown and API readiness instead of suppressing failures, apply one shared fail-closed URL policy to text, vision and smoke-test clients before they can transmit prompts, images or `LM_API_TOKEN`, and create GitHub Releases only from a clean manifest-exact commit that equals `origin/main`, has a successful CI run and a matching remote tag. Changelog version history was also corrected.

## 1.1.8 2026-07-23

Publication, model-inventory and endpoint hardening: refuse to rewrite an unexpected existing `origin`, verify archived state and visibility of an existing GitHub repository, prefer machine-readable `lms ls --json --variants` and exact variant keys over deprecated human output, require LM Studio server status to confirm `running=true` on the configured port, and keep MCP API requests plus optional tokens on numeric loopback unless remote delivery is explicitly enabled.

## 1.1.7 2026-07-23

Local-identity and tool-host trust-boundary hardening: require repository-local Git author settings instead of accepting inherited global values; keep the read-only memory-pressure tool on loopback unless a separate explicit remote opt-in is supplied; and reject multiple tool calls, missing call IDs, non-object arguments and every non-empty argument object before host execution.

## 1.1.6 2026-07-23

Fail-closed model-profile enforcement: reject altered catalog IDs or non-Q4_0 quantization before any download, validate every MODEL_KEY override against the installed LM Studio inventory, and prefer variant-aware fallback output so an override cannot bypass the exact QAT/GGUF/Q4_0 gate.

## 1.1.5 2026-07-23

Exact-model and trust-boundary hardening: reject non-canonical, duplicate or unsorted checksum-manifest paths; require exact Gemma 4 26B A4B QAT GGUF Q4_0 discovery instead of accepting another quantization; make loopback listener verification mandatory and retry it during bounded server startup; separate remote repository creation from local `origin` configuration; and generate MCP request payloads from a validated allowlisted template while applying the selected model identifier.

## 1.1.4 2026-07-23

Publication-state hardening: verify that every tracked Git path exactly matches `SHA256SUMS`, reject manifest-external files even in an existing clean commit, prefer repository-local Git identity, make non-exact model selection an explicit opt-in, apply repository description/topics/default branch after push, require an existing remote tag when creating a release, and reject unsafe or traversal-bearing manifest paths before verification, staging or packaging.

## 1.1.3 2026-07-23

CI supply-chain and freshness hardening: update to the 20 July 2026 v7 releases of `actions/checkout` and `actions/setup-python`, pin both actions to immutable release commit SHAs, disable checkout credential persistence, bound the CI job with a timeout, and extend version-consistency checks across release and screenshot documentation.

## 1.1.2 2026-07-23

Publication and cross-toolchain reproducibility hardening: manifest-only first-commit staging with rejection of unexpected untracked files, compressor-independent stored ZIP entries, GitHub Actions v6, consistent ignored `artifacts/` environment reports, and four additional regression checks.

## 1.1.1 2026-07-23

Release-artifact and evidence hardening: reproducible ZIP builder with post-extraction verification, release and screenshot policies, owner-only canonical benchmark guidance, ignored local hardware reports, sanitized loaded-model environment output, stronger Markdown anchor validation and updated SSH/release instructions.

## 1.1.0 2026-07-23

Security and publication hardening: exact GitHub account checks for SSH and `gh`, explicit localhost binding, confirmed optional unload, English-primary documentation with Russian material under `docs/ru`, Dependabot, Code of Conduct, hardware result templates, environment collection, actual loopback-listener verification, complete Russian localization and stronger package-integrity tests.

## 1.0.0 2026-07-23

Initial repository package with LM Studio installation scripts, Gemma 4 26B A4B QAT configuration, memory estimate gate, local API examples, vision and tool smoke tests, MCP security guidance, SSH publication procedure, diagrams and static CI.
