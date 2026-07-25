# Dependency policy

Repository version: 1.1.240

The release scripts use the Python standard library and macOS command-line tools. GitHub Actions are pinned to immutable full commits and mirrored in the source ledger. Runtime installation is not silently upgraded: `scripts/install_lm_studio.sh` installs when absent and requires the explicit `--upgrade` flag when already installed.

A dependency update must preserve the exact source record, current-version documentation, unit checks, static matrix, deterministic ZIP build and clean-extraction rerun. A newer release is not automatically inside the audited runtime boundary until these gates are regenerated.
