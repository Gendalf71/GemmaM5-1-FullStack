# Hardware benchmark protocol

Repository version: 1.1.240

This protocol is the only supported path for changing `benchmarks/m5-air-24gb.template.json` from `not_measured` to `measured`. Static verification cannot substitute for direct execution on the owner's MacBook Air M5.

## Evidence profile

Use a fixed prompt corpus and record its SHA-256 digest. Run at least three repetitions per operating point. State whether the first repetition is a cold start. Record prefill and decode rates separately in addition to time to first token and aggregate tokens per second.

Required operating points are 4K and 8K context. A 32K run is optional and remains experimental for the 24 GB profile. Keep concurrent predictions at one. Capture macOS build, LM Studio version, resolved `modelKey`, memory pressure before/load/peak, swap before/after and thermal state.

## Acceptance sequence

1. Run `./scripts/verify_repo.sh` and `./scripts/preflight.sh`.
2. Run `make hardware-report`; review the 0600 file before retaining or publishing it.
3. Capture model provenance with `make provenance`.
4. Run text, vision, controlled-tool and `make fullstack` acceptance.
5. Execute the fixed benchmark prompt at least three times at each declared context.
6. Populate only directly observed values, then run `make benchmark-check`.

A failed or interrupted run is recorded as `rejected` with notes, not converted into a performance number.
