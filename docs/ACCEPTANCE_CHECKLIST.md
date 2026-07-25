# Owner acceptance checklist

Repository version: 1.1.240

Static verification proves the package, not physical performance. Complete this checklist on the target MacBook Air M5 before changing any pending evidence badge.

## 1. Environment

- Confirm `Mac17,3` or `Mac17,4`, M5, arm64, at least 24 GiB reported memory and macOS 26.0 or newer with `./scripts/preflight.sh`.
- Record LM Studio 0.4.20 (recommended) or a later explicitly reviewed release.
- Close memory-intensive applications and record the thermal state.

## 2. Model identity

- Download only `google/gemma-4-26b-a4b-qat`, GGUF `Q4_0`.
- Run `make provenance` and review `artifacts/model-provenance.json` before publication.
- Do not publish raw local paths, tokens or model weights.

## 3. Functional acceptance

- Validate text, vision, document, controlled-tool and localhost API paths.
- Keep MCP disabled unless every server, permission and tool is explicitly allowlisted.
- Confirm the API listener is loopback-only and authentication is enabled.

## 4. Memory and stability

- Start at 4K, then 8K context; keep one concurrent prediction.
- Record memory pressure, swap, load duration, failure mode and recovery.
- Treat 32K and higher as experimental for this 24 GB profile.

## 5. Evidence

- Complete `benchmarks/m5-air-24gb.template.json` only from measured runs.
- Capture owner screenshots according to `docs/SCREENSHOTS.md`; redact paths, tokens and personal data.
- Keep status `not_measured` and `not_captured` until evidence is complete.
