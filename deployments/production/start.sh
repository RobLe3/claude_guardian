#!/usr/bin/env bash
set -euo pipefail

log() { echo "[cg] $*"; }

wait_for_postgres() {
  local tries=${PG_RETRIES:-50}
  for i in $(seq 1 "$tries"); do
    if PGPASSWORD="$PGPASSWORD" psql -h "$PGHOST" -U "$PGUSER" -d "$PGDATABASE" -c "select 1" >/dev/null 2>&1; then
      log "Postgres ready"
      return 0
    fi
    log "Waiting Postgres $i/$tries"
    sleep 1
  done
  log "Postgres not reachable"
  return 1
}

wait_for_qdrant() {
  local tries=${QDRANT_RETRIES:-50}
  local timeout=${QDRANT_TIMEOUT:-3}
  for i in $(seq 1 "$tries"); do
    if curl -fsS --max-time "$timeout" "$QDRANT_URL/readyz" >/dev/null; then
      log "Qdrant ready"
      return 0
    fi
    log "Waiting Qdrant $i/$tries"
    sleep 1
  done
  log "Qdrant not reachable"
  return 1
}

apply_sql() {
  shopt -s nullglob
  for f in /app/init/sql/*.sql; do
    log "Applying SQL, $(basename "$f")"
    PGPASSWORD="$PGPASSWORD" psql -v ON_ERROR_STOP=1 -h "$PGHOST" -U "$PGUSER" -d "$PGDATABASE" -f "$f"
  done
}

create_collection() {
  local name="$1"
  local spec="/app/init/qdrant/${name}.json"
  if [[ ! -f "$spec" ]]; then
    log "Spec missing for ${name}, skipping"
    return 0
  fi
  log "Ensuring Qdrant collection, ${name}"
  curl -fsS -X PUT "$QDRANT_URL/collections/${name}"     -H "Content-Type: application/json"     --data-binary @"$spec" >/dev/null || log "Collection ${name} may already exist"
}

bootstrap_datastores() {
  wait_for_postgres
  wait_for_qdrant
  apply_sql
  create_collection guard_case
  create_collection snippet
  create_collection policy
  create_collection ioc
  create_collection tool_call
}

main() {
  log "Starting Claude Guardian init, mode=${CG_INIT}"
  if [[ "${CG_INIT}" != "skip" ]]; then
    bootstrap_datastores
    log "Bootstrap complete"
  else
    log "Bootstrap skipped"
  fi

  if [[ -z "${MCP_CMD}" ]]; then
    log "No MCP_CMD provided, sleeping to keep container observable"
    tail -f /dev/null
  else
    log "Launching MCP server"
    exec bash -lc "${MCP_CMD}"
  fi
}

main "$@"
