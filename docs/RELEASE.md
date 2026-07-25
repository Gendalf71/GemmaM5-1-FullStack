# Release procedure

A GitHub Release is separate from the first push. The release script is dry-run by default and refuses to tag unless the local commit, `origin/main`, CI result, ZIP and checksum all agree.

## 1. Verify and package

```bash
./scripts/verify_repo.sh
./scripts/verify_git_inventory.sh --require-clean
make package
shasum -a 256 -c dist/GemmaM5-1-FullStack-1.1.240.zip.sha256
python3 scripts/validate_checksum_sidecar.py dist/GemmaM5-1-FullStack-1.1.240.zip.sha256 dist/GemmaM5-1-FullStack-1.1.240.zip
unzip -t dist/GemmaM5-1-FullStack-1.1.240.zip
```

Validate the archive structure and inventory before extraction:

```bash
python3 scripts/validate_release_zip.py \
  dist/GemmaM5-1-FullStack-1.1.240.zip \
  --expected-root GemmaM5-1-FullStack-1.1.240 \
  --manifest SHA256SUMS \
  --repository-root .
```

## 2. Dry-run the guarded Release

```bash
./scripts/create_github_release.sh
```

The dry run verifies repository-local Git identity, branch `main`, exact SSH `origin`, clean manifest-exact inventory, ZIP integrity, exact `Gendalf71` SSH and GitHub CLI accounts, public/non-archived repository state, equality of local `HEAD` and `origin/main`, successful GitHub Actions for that exact commit, matching local/remote tag targets and absence of a duplicate Release.

## 3. Create the Release

```bash
./scripts/create_github_release.sh --execute
```

The script creates and pushes annotated tag `v1.1.240` only when absent, verifies the remote tag after push, and attaches the ZIP plus `.sha256` sidecar through `gh release create --verify-tag`. It refuses retagging or duplicate Release creation. Model weights remain external.

After creation, the script re-reads the Release through `gh release view` and requires the exact tag, `isDraft=false`, `isPrerelease=false`, and both the ZIP and `.sha256` sidecar in the asset inventory.

The publication profile intentionally supports Public only: the Release procedure and README badge target the public `Gendalf71/GemmaM5-1-FullStack`. The script re-inspects exact `nameWithOwner`, visibility, archived state, description and the `main` branch after creation and after configuration.

## Clean-extraction verification boundary

The unit suite runs on the source tree before packaging. After safe extraction, the builder repeats every static gate with `--skip-unit-tests`: the exact manifest and safe-ZIP validator prove the released file inventory is identical, so the long unit suite is not duplicated in the same CI job. The independent terminal audit of 1.1.240 additionally repeated all 91 unit checks on a clean extraction.
