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

# container names
DB_NAME="${DB_CONTAINER_NAME:-nv-db}"
PGB_NAME="${PGBOUNCER_CONTAINER_NAME:-nv-pgbouncer}"
API_NAME="${API_CONTAINER_NAME:-nv-api}"

c_exists() { container list | awk '{print $NF}' | grep -qx "$1"; }
port_listen() { nc -z 127.0.0.1 "$1" >/dev/null 2>&1; }

echo "== Containers =="
c_exists "$DB_NAME"  && ok "DB: $DB_NAME running" || bad "DB: $DB_NAME not running"
c_exists "$PGB_NAME" && ok "PgBouncer: $PGB_NAME running" || warn "PgBouncer: $PGB_NAME not running"
c_exists "$API_NAME" && ok "API: $API_NAME running" || warn "API: $API_NAME not running"

echo ""
echo "== Ports (localhost) =="
port_listen "$DB_PORT"  && ok "DB port $DB_PORT open"  || warn "DB port $DB_PORT closed"
port_listen "$PGB_PORT" && ok "PgBouncer port $PGB_PORT open" || warn "PgBouncer port $PGB_PORT closed"
port_listen "$API_PORT" && ok "API port $API_PORT open" || warn "API port $API_PORT closed"

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

if command -v curl >/dev/null 2>&1 && port_listen "$API_PORT"; then
  curl -fsS "http://127.0.0.1:${API_PORT}/health" >/dev/null 2>&1 && ok "API /health OK" || warn "API /health not responding"
else
  warn "Skipping API health (curl missing or port closed)"
fi

echo ""
echo "== Tips =="
echo "  container logs -f ${DB_NAME}         # DB logs"
echo "  container logs -f ${PGB_NAME}        # PgBouncer logs"
echo "  container logs -f ${API_NAME}        # API logs"
