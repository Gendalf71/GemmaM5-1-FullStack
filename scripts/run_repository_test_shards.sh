#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "$0")" && pwd)/lib/common.sh"

shard_size="${GEMMAM5_TEST_SHARD_SIZE:-11}"
jobs="${GEMMAM5_TEST_JOBS:-4}"
timeout="${GEMMAM5_TEST_TIMEOUT:-60}"
[[ "$shard_size" =~ ^[1-9][0-9]*$ ]] || fail "GEMMAM5_TEST_SHARD_SIZE must be a positive integer"
[[ "$jobs" =~ ^[1-9][0-9]*$ ]] || fail "GEMMAM5_TEST_JOBS must be a positive integer"
[[ "$timeout" =~ ^[1-9][0-9]*([.][0-9]+)?$ ]] || fail "GEMMAM5_TEST_TIMEOUT must be positive"

test_count="$(python3 - <<'PY'
from scripts.run_repository_tests import discover_test_ids
print(len(discover_test_ids()))
PY
)"
[[ "$test_count" =~ ^[1-9][0-9]*$ ]] || fail "No repository tests were discovered"

find "$PROJECT_ROOT/scripts" "$PROJECT_ROOT/examples" "$PROJECT_ROOT/tests" -type d -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null || true

start=1
while [ "$start" -le "$test_count" ]; do
  end=$((start + shard_size - 1))
  if [ "$end" -gt "$test_count" ]; then end="$test_count"; fi
  python3 "$PROJECT_ROOT/scripts/run_repository_tests.py" \
    --timeout "$timeout" --jobs "$jobs" --batch-size "$shard_size" \
    --from-index "$start" --to-index "$end"
  find "$PROJECT_ROOT/scripts" "$PROJECT_ROOT/examples" "$PROJECT_ROOT/tests" -type d -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null || true
  start=$((end + 1))
done

log "Repository test shards: $test_count passed."
