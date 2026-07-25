# Images

- `banner.png` is the README title image.
- `architecture.png` separates hardware, runtime, model and controlled application functions.
- `memory_budget.png` is an illustrative budget, not a measured M5 allocation.
- `installation_flow.png` shows the publication and model-acceptance sequence.
- `tests/fixtures/vision_test.png` is the deterministic image fixture; the expected large number is 417.

## Automated visual gate (1.1.90)

`docs/assets/assets-manifest.json` fixes dimensions, role and minimum blank margin for every engineering PNG. `make assets-check` fails when content enters that margin.
