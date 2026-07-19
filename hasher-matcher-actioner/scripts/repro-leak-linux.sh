#!/usr/bin/env bash
# Linux-adapted tier-1 leak localization. Runs curator + matcher as separate
# gunicorn workers with NO request load, samples RSS every 15s, logs pympler
# every 60s, and takes memray start+end snapshots.
#
# Designed to be paired with a LOW-RATE InfiniteRandomExchange collab so the
# leak signal >> legitimate index growth (50 pdq per 30s = ~100/min).
#
# Usage: repro-leak-linux.sh [duration_seconds]   (default: 3600 = 1h)
set -euo pipefail

DURATION="${1:-3600}"

ROOT="/home/tao/ThreatExchange/hasher-matcher-actioner"
VENV_BIN="$ROOT/.venv/bin"
CONFIG_PATH="$ROOT/reference_omm_configs/development_omm_config.py"
DB_URI="postgresql+psycopg2://postgres:postgres@localhost:5432/media_match"

ARTIFACTS="${ARTIFACTS:-/tmp/hma-linux}"
mkdir -p "$ARTIFACTS"
rm -f "$ARTIFACTS"/*.log "$ARTIFACTS"/*.bin*

: "${OMM_TASK_INDEXER_INTERVAL_SECONDS:=10}"
: "${OMM_TASK_INDEX_CACHE_INTERVAL_SECONDS:=5}"
: "${OMM_TASK_FETCHER_INTERVAL_SECONDS:=30}"
export OMM_TASK_INDEXER_INTERVAL_SECONDS OMM_TASK_INDEX_CACHE_INTERVAL_SECONDS OMM_TASK_FETCHER_INTERVAL_SECONDS
echo "intervals: fetcher=${OMM_TASK_FETCHER_INTERVAL_SECONDS}s indexer=${OMM_TASK_INDEXER_INTERVAL_SECONDS}s index_cache=${OMM_TASK_INDEX_CACHE_INTERVAL_SECONDS}s"

launch_role() {
  local role="$1" port="$2"
  shift 2
  (
    exec env "$@" \
      OMM_CONFIG="$CONFIG_PATH" \
      OMM_DATABASE_URI="$DB_URI" \
      OMM_ENABLE_PYMPLER=1 \
      "$VENV_BIN/gunicorn" \
        --bind "0.0.0.0:$port" \
        --workers 1 --threads 1 \
        --timeout 300 \
        --chdir "$ROOT/src" \
        'OpenMediaMatch.app:create_app()'
  ) > "$ARTIFACTS/$role.log" 2>&1 &
  echo $!
}

CURATOR_PID=$(launch_role curator 5101 \
  OMM_ROLE_CURATOR=true OMM_ROLE_MATCHER=false OMM_ROLE_HASHER=false \
  OMM_TASK_FETCHER=true OMM_TASK_INDEXER=true OMM_TASK_INDEX_CACHE=false)

MATCHER_PID=$(launch_role matcher 5102 \
  OMM_ROLE_CURATOR=false OMM_ROLE_MATCHER=true OMM_ROLE_HASHER=false \
  OMM_TASK_FETCHER=false OMM_TASK_INDEXER=false OMM_TASK_INDEX_CACHE=true)

echo "launched: curator=$CURATOR_PID matcher=$MATCHER_PID"

SAMPLERS=()
cleanup() {
  echo "--- cleanup ---"
  for p in ${SAMPLERS[@]+"${SAMPLERS[@]}"}; do
    kill -TERM "$p" 2>/dev/null || true
  done
  for p in "$CURATOR_PID" "$MATCHER_PID"; do
    kill -INT "$p" 2>/dev/null || true
  done
  sleep 3
  for p in "$CURATOR_PID" "$MATCHER_PID"; do
    kill -TERM "$p" 2>/dev/null || true
  done
  echo "--- done; artifacts in $ARTIFACTS ---"
  ls -lh "$ARTIFACTS" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

echo "waiting for curator + matcher ready (up to 3 min)..."
DEADLINE=$(( $(date +%s) + 180 ))
up=0
while [[ $(date +%s) -lt $DEADLINE ]]; do
  up=0
  for port in 5101 5102; do
    curl -sf "http://localhost:$port/status" > /dev/null 2>&1 && up=$((up+1)) || true
  done
  [[ $up -eq 2 ]] && { echo "both ready"; break; }
  sleep 2
done
if [[ $up -ne 2 ]]; then echo "ERROR: not ready" >&2; exit 1; fi

sample_rss() {
  local role="$1" master="$2"
  (
    while kill -0 "$master" 2>/dev/null; do
      local w
      w="$(pgrep -P "$master" | head -1 || true)"
      if [[ -n "$w" ]]; then
        printf "%s %s\n" "$(date -u +%FT%TZ)" "$(ps -o rss= -p "$w" 2>/dev/null)"
      fi
      sleep 15
    done
  ) > "$ARTIFACTS/$role-rss.log" 2>&1 &
  SAMPLERS+=($!)
}
sample_rss curator "$CURATOR_PID"
sample_rss matcher "$MATCHER_PID"

sample_pympler() {
  local role="$1" port="$2"
  (
    while :; do
      printf "=== %s ===\n" "$(date -u +%FT%TZ)"
      curl -sf --max-time 30 "http://localhost:$port/dev/pympler?top=40" \
        || echo "{\"error\":\"curl failed\"}"
      echo
      sleep 60
    done
  ) > "$ARTIFACTS/$role-pympler.log" 2>&1 &
  SAMPLERS+=($!)
}
sample_pympler curator 5101
sample_pympler matcher 5102

SNAPSHOT_SECONDS=${SNAPSHOT_SECONDS:-60}
START_OFFSET=${START_OFFSET:-300}
END_OFFSET=${END_OFFSET:-$(( DURATION - 360 ))}

SKIP_END_SNAPSHOT=false
if [[ $END_OFFSET -le $(( START_OFFSET + SNAPSHOT_SECONDS + 30 )) ]]; then
  echo "WARN: duration too short for two distinct snapshots; skipping end snapshot"
  SKIP_END_SNAPSHOT=true
fi

take_snapshots() {
  local tag="$1"
  echo "=== memray $tag snapshots ($(date -u +%FT%TZ)) ==="
  local cur_w mat_w
  cur_w="$(pgrep -P "$CURATOR_PID" | head -1 || true)"
  mat_w="$(pgrep -P "$MATCHER_PID" | head -1 || true)"
  for role_pid in "curator:$cur_w" "matcher:$mat_w"; do
    IFS=: read role pid <<< "$role_pid"
    if [[ -z "$pid" ]]; then
      echo "  $role: no worker, skipping"
      continue
    fi
    echo "  $role (pid=$pid) -> $tag.bin"
    "$VENV_BIN/memray" attach \
      --aggregate \
      --duration "$SNAPSHOT_SECONDS" \
      --output "$ARTIFACTS/$role-$tag.bin" \
      "$pid" 2>&1 | sed "s/^/    /" || echo "    FAILED for $role"
  done
}

(trap exit TERM; sleep "$START_OFFSET"; take_snapshots start) &
SAMPLERS+=($!)
if [[ "$SKIP_END_SNAPSHOT" == false ]]; then
  (trap exit TERM; sleep "$END_OFFSET"; take_snapshots end) &
  SAMPLERS+=($!)
fi

END_AT="$(date -d "@$(( $(date +%s) + DURATION ))" '+%Y-%m-%d %H:%M:%S')"
echo "running for ${DURATION}s; finishes ~$END_AT"
echo "  start snapshot at T+${START_OFFSET}s ($SNAPSHOT_SECONDS s)"
if [[ "$SKIP_END_SNAPSHOT" == false ]]; then
  echo "  end snapshot at T+${END_OFFSET}s"
fi
echo ""
echo "tail -f $ARTIFACTS/curator-rss.log $ARTIFACTS/matcher-rss.log"

sleep "$DURATION"

sleep $(( SNAPSHOT_SECONDS + 15 ))
echo "duration elapsed; cleanup trap will teardown"
