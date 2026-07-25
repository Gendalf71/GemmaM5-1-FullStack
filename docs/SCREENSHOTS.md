# Screenshot evidence policy

## Current status

Version 1.1.240 includes engineering diagrams, not screenshots presented as proof of a completed hardware run. A generated or reconstructed LM Studio interface must never be labelled as runtime evidence.

## Canonical screenshots

Only the repository owner may add canonical screenshots after direct acceptance on the target MacBook Air M5. Capture only what is needed to substantiate a documented step:

1. LM Studio and runtime version.
2. Exact downloaded model and quantization.
3. The 8K resource estimate.
4. The loaded identifier and localhost-only server.
5. Successful text, vision, document and constrained-tool tests.
6. Memory pressure or Activity Monitor during the measured run.

## Redaction and provenance

Before committing an image, remove API tokens, email addresses, account identifiers, unrelated model names, private documents, full home-directory paths and browser or terminal history. Record the UTC date, hardware, macOS, LM Studio/runtime version, model key and context in the accompanying caption or benchmark JSON.

Place accepted captures under `docs/assets/screenshots/`, use descriptive lowercase names, provide meaningful alt text, and update `REPOSITORY_TREE.txt` and `SHA256SUMS`. PNG or lossless WebP is preferred for interface text.

## Evidence state in 1.1.240

Generated diagrams are not runtime evidence. Keep `docs/screenshot-manifest.template.json` in `not_captured` state until direct owner acceptance, redaction review and exact software/model metadata are available.
