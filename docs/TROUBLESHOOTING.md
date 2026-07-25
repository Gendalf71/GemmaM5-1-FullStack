# Troubleshooting

## `lms` is not found

Open LM Studio once and start a new Terminal. Run `lms --help`. On a legacy installation only, `~/.lmstudio/bin/lms bootstrap` may add the CLI to the shell path.

## `lms load --parallel` is unavailable

Update LM Studio to 0.4.11 or newer (0.4.20 or newer recommended), launch it once and reopen Terminal. Verify the required loader capability:

```bash
lms load --help | grep -- --parallel
```

Do not remove the project guard or rely on LM Studio's higher default Max Concurrent Predictions; this 24 GB profile requires exactly one.

## Model key is not found

Run `python3 scripts/resolve_model_identity.py --format json`. Confirm that one local QAT GGUF `Q4_0` path/modelKey pair is reported. An override is accepted only after the same installed-model verification:

```bash
python3 scripts/resolve_model_identity.py --format json
export MODEL_KEY="exact-model-key-from-that-output"
```

## Memory estimate is too high

Close heavy applications, unload other models deliberately, reduce context and confirm that the selected variant is `Q4_0`. Do not assume partial CPU offload fixes total unified-memory pressure.

## SSH authenticates the wrong account

Run:

```bash
ssh -vT git@github-gendalf71
./scripts/check_github_ssh.sh github-gendalf71 Gendalf71
```

Inspect `IdentityFile`, `IdentitiesOnly`, the loaded keys and the public key registered in the Gendalf71 account.

## A clean commit still fails inventory verification

Run `git ls-files` and compare it with `SHA256SUMS`. A clean working tree is not sufficient if an earlier commit tracked an additional path. Remove the unintended file from Git, update the manifest only for deliberate release files, and rerun `./scripts/verify_git_inventory.sh --require-clean`.

## Exact model reference is rejected

Do not silently select another quantization. Inspect the `lms get` error, update LM Studio if appropriate, and retry. Only when a deliberate manual selection is necessary, run `./scripts/download_model.sh --interactive-fallback`, select GGUF `Q4_0`, and let the script verify the resulting local model key.

## Exact hardware profile

`preflight.sh` does not treat every 24 GB Apple Silicon Mac as equivalent to the target. It reads machine JSON from `system_profiler` and requires `MacBook Air` plus an `M5` chip token, arm64, at least 24 GiB of reported memory and macOS 26.0 or newer. Another Mac may be compatible, but it is outside this validated profile and requires a separate configuration.
