#!/usr/bin/env bash
# run_cache_suite.sh — orchestrate the dev[ldn] caching benchmark.
#
# k6 cannot flush memcached, so cold-cache phases need an external flush.
# This script sequences the phases, flushes between them, and records the
# environment alongside the results (Gunicorn workers, throttle state,
# container stats) so a run is interpretable months later.
#
#   ./scripts/k6/run_cache_suite.sh              # full suite
#   ./scripts/k6/run_cache_suite.sh capacity     # one phase
#   RATE=30 ./scripts/k6/run_cache_suite.sh steady
#
set -euo pipefail

COMPOSE_FILES="-f docker-compose.yaml -f docker-compose.monitoring.yaml -f docker-compose.perf.yaml"
COMPOSE="docker compose ${COMPOSE_FILES}"
SCRIPT="cache_benchmark.js"

RATE="${RATE:-20}"
BURST_VUS="${BURST_VUS:-40}"
DURATION="${DURATION:-5m}"
SETTLE="${SETTLE:-20}"   # seconds between phases, lets rates return to zero

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
OUT="results/cache-suite-${STAMP}"
mkdir -p "${OUT}"

log() { printf '\n\033[1;32m==> %s\033[0m\n' "$*"; }
warn() { printf '\033[1;33m!!  %s\033[0m\n' "$*"; }

# --------------------------------------------------------------- preflight

record_env() {
  log "Recording environment → ${OUT}/environment.txt"
  {
    echo "timestamp_utc: ${STAMP}"
    echo "rate: ${RATE}  burst_vus: ${BURST_VUS}  duration: ${DURATION}"
    echo
    echo "--- gunicorn (stampede results are meaningless with WORKERS=1) ---"
    grep -E '^(WORKERS|THREADS|TIMEOUT)=' .env 2>/dev/null || echo "(.env not readable)"
    echo
    echo "--- pi thermal / throttle ---"
    vcgencmd get_throttled 2>/dev/null || echo "(vcgencmd unavailable)"
    awk '{printf "temp: %.1fC\n", $1/1000}' /sys/class/thermal/thermal_zone0/temp 2>/dev/null \
      || echo "(thermal zone unavailable)"
    echo
    echo "--- root filesystem (SD vs SSD materially changes these numbers) ---"
    findmnt -no SOURCE,FSTYPE / 2>/dev/null || echo "(findmnt unavailable)"
    echo
    echo "--- containers ---"
    docker stats --no-stream --format '{{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}' 2>/dev/null
  } > "${OUT}/environment.txt" 2>&1
  cat "${OUT}/environment.txt"
}

preflight() {
  log "Preflight"

  if ! curl -fsS -o /dev/null "http://localhost:8001/products/"; then
    warn "App not reachable on localhost:8001 — is the stack up?"
    exit 1
  fi

  local xc
  xc="$(curl -sI http://localhost:8001/products/ | grep -i '^x-cache:' || true)"
  if [[ -z "${xc}" ]]; then
    warn "No X-Cache header. Apply cache_dogpile_xcache.patch.md first."
    warn "Without it the stampede phase cannot distinguish one recomputation"
    warn "from forty, which is the entire point of that phase."
    read -r -p "Continue anyway? [y/N] " ans
    [[ "${ans}" == "y" ]] || exit 1
  else
    log "X-Cache present: ${xc}"
  fi
}

# --------------------------------------------------------------- helpers

flush_cache() {
  log "Flushing memcached"
  # memcached:1.6-alpine ships busybox, which includes nc.
  if ! ${COMPOSE} exec -T memcached sh -c \
      'printf "flush_all\r\nquit\r\n" | nc 127.0.0.1 11211' 2>/dev/null; then
    warn "flush via exec failed — falling back to a restart"
    ${COMPOSE} restart memcached
    sleep 5
  fi
}

# run_phase <phase> [extra env assignments...]
run_phase() {
  local phase="$1"; shift
  log "PHASE=${phase} $*"
  ${COMPOSE} run --rm \
    --env "K6_SCRIPT=${SCRIPT}" \
    --env "PHASE=${phase}" \
    --env "RATE=${RATE}" \
    --env "BURST_VUS=${BURST_VUS}" \
    --env "DURATION=${DURATION}" \
    "$@" \
    k6 2>&1 | tee "${OUT}/${phase}${PHASE_SUFFIX:-}.log"
  sleep "${SETTLE}"
}

# --------------------------------------------------------------- phases

phase_capacity() {
  flush_cache
  # Warm briefly so the ramp measures steady-state capacity, not cold starts.
  curl -fsS -o /dev/null "http://localhost:8001/products/?page=1" || true
  curl -fsS -o /dev/null "http://localhost:8001/api/products/?page=1" || true
  run_phase capacity
  warn "Read the ceiling off this run and set RATE to ~60% of it for the rest."
}

phase_coldwarm() {
  flush_cache
  run_phase coldwarm
}

phase_steady() {
  flush_cache
  run_phase steady
}

phase_stampede() {
  # Run twice: short-wait dogpile vs stale-while-revalidate, same conditions.
  flush_cache
  PHASE_SUFFIX="-list" run_phase stampede --env TARGET=list
  flush_cache
  PHASE_SUFFIX="-grid" run_phase stampede --env TARGET=grid
  unset PHASE_SUFFIX
}

phase_variant() {
  flush_cache
  run_phase variant
}

phase_keyspace() {
  flush_cache
  run_phase keyspace
}

# Phase 6 — fail-open. The ADR claims a cache outage degrades to normal
# rendering rather than erroring. Cheap to verify and rarely tested.
phase_failopen() {
  flush_cache
  log "PHASE=failopen — steady load with memcached stopped mid-run"
  ${COMPOSE} run --rm -d \
    --env "K6_SCRIPT=${SCRIPT}" --env "PHASE=steady" \
    --env "RATE=${RATE}" --env "DURATION=2m" \
    k6 > "${OUT}/failopen-container.txt"

  sleep 45
  log "Stopping memcached"
  ${COMPOSE} stop memcached
  sleep 30
  log "Restarting memcached"
  ${COMPOSE} start memcached
  sleep 45

  {
    echo "Expected: zero 5xx throughout; X-Cache=BYPASS while memcached is down;"
    echo "cache_hit rate recovers after restart. Check the Grafana error-rate"
    echo "panel and the k6 container logs for this window."
  } > "${OUT}/failopen-expectations.txt"
  warn "Check the k6 container log and the Grafana error panel for this window."
}

# --------------------------------------------------------------- main

main() {
  preflight
  record_env

  local only="${1:-all}"
  case "${only}" in
    capacity)  phase_capacity ;;
    coldwarm)  phase_coldwarm ;;
    steady)    phase_steady ;;
    stampede)  phase_stampede ;;
    variant)   phase_variant ;;
    keyspace)  phase_keyspace ;;
    failopen)  phase_failopen ;;
    all)
      phase_capacity
      phase_coldwarm
      phase_variant
      phase_steady
      phase_stampede
      phase_keyspace
      ;;
    *) echo "unknown phase: ${only}"; exit 2 ;;
  esac

  log "Results → ${OUT}"
}

main "$@"
