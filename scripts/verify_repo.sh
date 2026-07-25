#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "$0")" && pwd)/lib/common.sh"

skip_unit_tests=0
case "${1:-}" in
  "") ;;
  --skip-unit-tests) skip_unit_tests=1 ;;
  *) fail "Usage: $0 [--skip-unit-tests]" ;;
esac

cd "$PROJECT_ROOT"
cleanup_transients() { find scripts examples tests -type d -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null || true; }
trap cleanup_transients EXIT
export PYTHONDONTWRITEBYTECODE=1

log "Bash syntax checks"
for file in scripts/*.sh scripts/lib/*.sh examples/*.sh; do
  [ -e "$file" ] || continue
  bash -n "$file"
done

log "Python AST syntax checks without bytecode"
python3 - <<'PY_AST'
import ast
from pathlib import Path
for directory in ('scripts', 'examples', 'tests'):
    for path in Path(directory).rglob('*.py'):
        ast.parse(path.read_text(encoding='utf-8'), filename=str(path))
print('Python AST files: OK')
PY_AST

log "Independent UTF-8 and whitespace quality"
python3 "$PROJECT_ROOT/scripts/verify_text_quality.py"

if [ "$skip_unit_tests" -eq 0 ]; then
  log "Repository unit checks"
  "$PROJECT_ROOT/scripts/run_repository_test_shards.sh"
else
  log "Repository unit checks explicitly skipped because the source tree was already verified and the archive inventory is exact"
fi

log "Requested 90 x 24 review matrix"
version="$(read_release_version)"
python3 "$PROJECT_ROOT/scripts/generate_iteration_matrix.py" --verify "$PROJECT_ROOT/docs/audit/iteration-matrix-${version}.json"

log "Operational release-version references"
python3 "$PROJECT_ROOT/scripts/verify_version_references.py"

log "External evidence ledger"
python3 "$PROJECT_ROOT/scripts/verify_external_sources.py"

log "Release assurance record"
python3 "$PROJECT_ROOT/scripts/validate_release_assurance.py"

log "Benchmark evidence schema"
python3 "$PROJECT_ROOT/scripts/validate_benchmark.py" "$PROJECT_ROOT/benchmarks/m5-air-24gb.template.json" --expected-repository-version "$(read_release_version)"

log "Visual asset dimensions and safe margins"
python3 "$PROJECT_ROOT/scripts/validate_png_assets.py" "$PROJECT_ROOT/docs/assets/assets-manifest.json"

log "JSON checks"
python3 -c 'import json; from pathlib import Path; [json.loads(p.read_text(encoding="utf-8")) for p in Path(".").rglob("*.json")]; print("JSON files: OK")'

if [ -f SHA256SUMS ]; then
  log "Checksum manifest"
  python3 "$PROJECT_ROOT/scripts/validate_manifest.py" "$PROJECT_ROOT/SHA256SUMS" --root "$PROJECT_ROOT" --require-files
  shasum -a 256 -c SHA256SUMS
fi

log "Static repository verification passed"
