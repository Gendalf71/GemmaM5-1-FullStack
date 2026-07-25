# Model provenance and reproducibility boundary

## What this repository fixes

The release fixes and verifies the repository files, the supported catalog ID, the `Q4_0` requirement, the local model identifier, the initial context, the localhost bind policy and the validation procedure. Release ZIP files are deterministic and have a SHA-256 sidecar.

## What it cannot fix by itself

Model weights are external. The LM Studio catalog entry `google/gemma-4-26b-a4b-qat` and its upstream Hugging Face files are revisioned resources. An upstream maintainer can publish a correction without changing this repository. The phrase **repeatable configuration** is therefore more accurate than a claim of immutable model bytes.

The supported profile remains exact:

```text
Catalog ID: google/gemma-4-26b-a4b-qat
Format: GGUF
Quantization: Q4_0
Local identifier: gemma4-local
```

## Capture the installed artifact identity

After model download and exact-key discovery on the target Mac:

```bash
make provenance
cat artifacts/model-provenance.json
```

The command:

1. requires macOS and a working `lms` CLI;
2. re-validates the fixed catalog ID and `Q4_0` profile;
3. resolves and cross-checks the installed exact `ModelInfo.path`/`modelKey` pair;
4. reads `lms ls --json`;
5. stores only an allowlisted subset of model metadata;
6. omits local paths and credentials;
7. writes the result with owner-only permissions under the Git-ignored `artifacts/` directory.

The report is evidence of the installed catalog variant and runtime inventory. It is not a cryptographic checksum of every external weight file because current LM Studio inventory output does not provide a repository-controlled digest for that purpose.

## Evidence for a published benchmark

A benchmark entry should identify the repository release, the provenance report, macOS, LM Studio and runtime versions, model key, context length, thermal state and memory pressure. Never edit a historical benchmark to represent a different model download; add a new dated record instead.
