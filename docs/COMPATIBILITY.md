# Runtime compatibility contract

Repository version: 1.1.240

The repository does not infer compatibility from an application version alone. On the target Mac, `scripts/check_lm_studio_version.sh` first requires LM Studio 0.4.11 or newer and recommends 0.4.20 or newer. The minimum is tied to the updated Gemma 4 chat template; the recommendation tracks the stable runtime line audited on 2026-07-24. `scripts/verify_lms_cli_contract.sh` then checks the actually installed command surface.

Required public CLI contract:

- `lms get`: `--gguf`, `--yes`, and current `--select` or the detected legacy selection flag;
- `lms load`: `--context-length`, `--gpu`, `--parallel`, `--identifier`, `--ttl`, `--estimate-only`, `--yes`;
- `lms ls`: `--json`;
- `lms ps`: `--json`;
- `lms unload`: exact positional identifier;
- `lms server start`: `--bind`, `--port`;
- `lms server status`: `--json`.

## Exact identity contract

On 2026-07-24 the behavior was independently checked against `lmstudio-ai/lms` revision `71bd99ccf882a0410cfd574ee220a99083608930`.

The current `lms load --exact` implementation treats its positional value as `ModelInfo.path`, not as `modelKey`. After finding the exact path it loads the corresponding `model.modelKey`. The repository therefore resolves one indivisible local pair from `lms ls --json`:

1. `ModelInfo.path` — supplied to `lms load --exact --local` and to the estimator;
2. `modelKey` — retained as an independent precondition and postcondition for the loaded instance.

The resolver rejects non-Q4_0 entries, remote LM Link entries, incomplete records and more than one exact path/modelKey pair. The loader blocks identifier/path/modelKey collisions before mutation, accepts an idempotent no-op only for one unique fully matching instance, and rolls back a failed partial load by exact identifier.

Hidden `--exact` and `--local` flags are exercised by the managed estimate/load commands. If an installed CLI no longer accepts them, the operation stops rather than selecting a different or remote model.

## Target hardware contract

Preflight requires:

- `MacBook Air`;
- Apple M5 chip token;
- model identifier `Mac17,3` or `Mac17,4`;
- arm64;
- at least 24 GiB reported unified memory;
- macOS 26.0 or newer.

These checks identify the requested profile; they do not prove performance. Physical acceptance remains mandatory after every LM Studio/runtime update.

## Current release boundary (2026-07-24)

The guarded profile requires LM Studio 0.4.11 or newer because 0.4.11 introduced the updated Gemma 4 chat-template support used by this package. Version 0.4.20 is the recommended validated application release for this repository. The generic LM Studio system-requirements page currently names M1/M2/M3/M4, not M5; that documentation lag is not converted into an unsupported claim. Apple sources establish the M5 hardware identity, while physical LM Studio operation remains subject to the owner acceptance checklist.
