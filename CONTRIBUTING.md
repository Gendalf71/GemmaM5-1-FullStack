# Contributing

Use a focused branch and run `make verify`. Do not commit model weights, tokens, private keys, local configuration, private diagnostic output or benchmark claims without a reproducible protocol.

Performance contributions must include the exact Mac, memory, macOS, LM Studio and runtime versions, model key, quantization, context, prompt, sampling parameters, thermal state and measurement method. Start from `benchmarks/m5-air-24gb.template.json`.

By participating, follow `CODE_OF_CONDUCT.md`.

## Release inventory

After committing release-oriented changes, run `./scripts/verify_git_inventory.sh --require-clean`. The command proves that the tracked tree contains exactly `SHA256SUMS` plus the manifest itself.
