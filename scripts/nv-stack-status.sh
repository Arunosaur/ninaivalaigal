#!/usr/bin/env bash
# Show concise status for DB, PgBouncer, API

set -euo pipefail
RED=$'\033[31m'; GRN=$'\033[32m'; YLW=$'\033[33m'; NC=$'\033[0m'

ok(){ echo "${GRN}✔${NC} $*"; }
warn(){ echo "${YLW}⚠${NC} $*"; }
bad(){ echo "${RED}✘${NC} $*"; }

# Defaults must match your start scripts
DB_PORT="${POSTGRES_PORT:-5433}"
PGB_PORT="${PGBOUNCER_PORT:-6432}"
API_PORT="${API_PORT:-13370}"
MEM0_PORT="${MEM0_PORT:-7070}"
UI_PORT="${UI_PORT:-8080}"

# container names
DB_NAME="${DB_CONTAINER_NAME:-nv-db}"
PGB_NAME="${PGBOUNCER_CONTAINER_NAME:-nv-pgbouncer}"
API_NAME="${API_CONTAINER_NAME:-nv-api}"
MEM0_NAME="${MEM0_CONTAINER_NAME:-nv-mem0}"
UI_NAME="${UI_CONTAINER_NAME:-nv-ui}"

c_exists() { container list | awk 'NR>1 {print $1}' | grep -qx "$1"; }
port_listen() { nc -z 127.0.0.1 "$1" >/dev/null 2>&1; }

echo "== Containers =="
c_exists "$DB_NAME"   && ok "DB: $DB_NAME running"      || bad  "DB: $DB_NAME not running"
c_exists "$PGB_NAME"  && ok "PgB: $PGB_NAME running"     || warn "PgB: $PGB_NAME not running"
c_exists "$MEM0_NAME" && ok "mem0: $MEM0_NAME running"   || warn "mem0: $MEM0_NAME not running"
c_exists "$API_NAME"  && ok "API: $API_NAME running"     || warn "API: $API_NAME not running"
c_exists "$UI_NAME"   && ok "UI: $UI_NAME running"       || warn "UI: $UI_NAME not running"

echo ""
echo "== Ports (localhost) =="
port_listen "$DB_PORT"  && ok "DB port $DB_PORT open"     || warn "DB port $DB_PORT closed"
port_listen "$PGB_PORT" && ok "PgB port $PGB_PORT open"   || warn "PgB port $PGB_PORT closed"
port_listen "$MEM0_PORT"&& ok "mem0 port $MEM0_PORT open" || warn "mem0 port $MEM0_PORT closed"
port_listen "$API_PORT" && ok "API port $API_PORT open"   || warn "API port $API_PORT closed"
port_listen "$UI_PORT"  && ok "UI port $UI_PORT open"     || warn "UI port $UI_PORT closed"

echo ""
echo "== Health =="
if command -v psql >/dev/null 2>&1 && port_listen "$PGB_PORT"; then
  if PGPASSWORD="${POSTGRES_PASSWORD:-change_me_securely}" psql \
       "postgresql://${POSTGRES_USER:-nina}@127.0.0.1:${PGB_PORT}/${POSTGRES_DB:-nina}" \
       -c "select 1" >/dev/null 2>&1; then
    ok "DB via PgBouncer: SELECT 1 OK"
  else
    warn "DB via PgBouncer: SELECT 1 failed"
  fi
else
  warn "Skipping DB check (psql missing or port closed)"
fi

if command -v curl >/dev/null 2>&1 && port_listen "$MEM0_PORT"; then
  curl -fsS "http://127.0.0.1:${MEM0_PORT}/health" >/dev/null 2>&1 && ok "mem0 /health OK" || warn "mem0 /health failed"
else
  warn "Skipping mem0 health (curl missing or port closed)"
fi

if command -v curl >/dev/null 2>&1 && port_listen "$API_PORT"; then
  curl -fsS "http://127.0.0.1:${API_PORT}/health" >/dev/null 2>&1 && ok "API /health OK" || warn "API /health failed"
else
  warn "Skipping API health (curl missing or port closed)"
fi

if command -v curl >/dev/null 2>&1 && port_listen "$UI_PORT"; then
  curl -fsS "http://127.0.0.1:${UI_PORT}/health" >/dev/null 2>&1 && ok "UI /health OK" || warn "UI /health failed"
else
  warn "Skipping UI health (curl missing or port closed)"
fi

echo ""
echo "== Tips =="
echo "  container logs -f ${DB_NAME}"
echo "  container logs -f ${PGB_NAME}"
echo "  container logs -f ${MEM0_NAME}"
echo "  container logs -f ${API_NAME}"
echo "  container logs -f ${UI_NAME}"
