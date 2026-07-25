#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "$0")" && pwd)/lib/common.sh"

output_dir="$PROJECT_ROOT/dist"
source_already_verified=0
while [ "$#" -gt 0 ]; do
  case "$1" in
    --source-already-verified)
      source_already_verified=1
      ;;
    --output-dir)
      shift
      [ "$#" -gt 0 ] || fail "--output-dir requires a path"
      output_dir="$1"
      ;;
    -h|--help)
      printf '%s\n' 'Usage: scripts/build_release.sh [--source-already-verified] [--output-dir PATH]'
      exit 0
      ;;
    *) fail "Unknown argument: $1" ;;
  esac
  shift
done

for command_name in python3 unzip shasum mktemp cp cmp; do
  require_command "$command_name"
done

version="$(read_release_version)"
package_name="GemmaM5-1-FullStack-$version"
mkdir -p "$output_dir"
output_dir="$(cd "$output_dir" && pwd)"
archive="$output_dir/$package_name.zip"
sidecar="$archive.sha256"

tmp="$(mktemp -d "${TMPDIR:-/tmp}/gemmam5-release.XXXXXX")"
cleanup() { rm -rf "$tmp"; }
trap cleanup EXIT
stage="$tmp/stage/$package_name"
verify_dir="$tmp/verify"
mkdir -p "$stage" "$verify_dir"

if [ "$source_already_verified" -eq 0 ]; then
  "$PROJECT_ROOT/scripts/verify_repo.sh"
else
  log "Source verification explicitly acknowledged as already completed in this job."
fi

manifest_paths="$tmp/manifest-paths.txt"
python3 "$PROJECT_ROOT/scripts/validate_manifest.py" "$PROJECT_ROOT/SHA256SUMS" \
  --root "$PROJECT_ROOT" --require-files --print-paths > "$manifest_paths"
while IFS= read -r relative; do
  source_path="$PROJECT_ROOT/$relative"
  mkdir -p "$stage/$(dirname "$relative")"
  cp -p "$source_path" "$stage/$relative"
done < "$manifest_paths"
cp -p "$PROJECT_ROOT/SHA256SUMS" "$stage/SHA256SUMS"

rm -f "$archive" "$sidecar"
second_archive="$tmp/$package_name.second.zip"
python3 "$PROJECT_ROOT/scripts/create_release_zip.py" "$tmp/stage" "$archive"
python3 "$PROJECT_ROOT/scripts/create_release_zip.py" "$tmp/stage" "$second_archive"
cmp -s "$archive" "$second_archive" || fail "Release ZIP creation is not byte-for-byte reproducible"
python3 "$PROJECT_ROOT/scripts/validate_release_zip.py" "$archive" \
  --expected-root "$package_name" --manifest "$PROJECT_ROOT/SHA256SUMS" --repository-root "$PROJECT_ROOT"
python3 "$PROJECT_ROOT/scripts/validate_release_zip.py" "$second_archive" \
  --expected-root "$package_name" --manifest "$PROJECT_ROOT/SHA256SUMS" --repository-root "$PROJECT_ROOT"

unzip -t "$archive" >/dev/null
unzip -q "$archive" -d "$verify_dir"
extracted="$verify_dir/$package_name"
[ -x "$extracted/scripts/verify_repo.sh" ] || fail "Archive did not preserve executable mode for scripts/verify_repo.sh"
(
  cd "$extracted"
  # The source unit suite has already passed in this release job. The exact
  # manifest and safe ZIP inventory prove that the extracted tracked files are
  # identical, so repeat every static gate without re-running the long suite.
  ./scripts/verify_repo.sh --skip-unit-tests
)

(
  cd "$output_dir"
  shasum -a 256 "$(basename "$archive")" > "$(basename "$sidecar")"
)
python3 "$PROJECT_ROOT/scripts/validate_checksum_sidecar.py" "$sidecar" "$archive"

log "Release archive: $archive"
log "Checksum file: $sidecar"
cat "$sidecar"
