# Validation and hardware acceptance

## Static verification

```bash
./scripts/verify_repo.sh
```

Static verification does not prove that the model fits or performs acceptably on a particular Mac.

## Target-Mac protocol

1. Run `preflight.sh`.
2. Capture `collect_environment.sh` output.
3. Run the 8K estimate.
4. Record memory pressure and swap before load.
5. Load one model and confirm that the project command used `--parallel 1`; then start the localhost server.
6. Run text, vision and forced-tool-schema tests.
7. Test a normal text PDF or DOCX in LM Studio.
8. Run 15 minutes of mixed work with one concurrent prediction. Do not substitute LM Studio's higher default parallelism for this test.
9. Record memory pressure, swap, errors and observed throughput.

Use `benchmarks/m5-air-24gb.template.json` for the result. The repository owner alone populates the canonical M5 Air result; replace `null` fields only with measured values and never publish inferred benchmark numbers. Store raw environment captures under ignored `artifacts/` until they have been reviewed and redacted.

## Network and release acceptance

Treat a mixed loopback plus LAN listener as a failure. `scripts/status.sh` must obtain `/v1/models` successfully. After stopping, LM Studio must report `running=false` and no listener may remain. Before a GitHub Release, require local `HEAD`, `origin/main`, successful CI and the tag target to agree through `scripts/create_github_release.sh`.

## Release 1.1.90 evidence gates

`verify_repo.sh` now validates diagram dimensions and protected margins. Owner-only runtime evidence is captured separately with `make hardware-report`; the full-stack acceptance path is `make fullstack`. Neither result is committed automatically.

## Clean-extraction verification boundary

The unit suite runs on the source tree before packaging. After safe extraction, the builder repeats every static gate with `--skip-unit-tests`: the exact manifest and safe-ZIP validator prove the released file inventory is identical, so the long unit suite is not duplicated in the same CI job. The independent terminal audit of 1.1.240 additionally repeated all 91 unit checks on a clean extraction.
