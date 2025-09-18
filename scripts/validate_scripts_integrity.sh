#!/usr/bin/env bash
set -euo pipefail

RED=$'\033[31m'; GRN=$'\033[32m'; YLW=$'\033[33m'; NC=$'\033[0m'
ok(){ echo "${GRN}✔${NC} $*"; }
warn(){ echo "${YLW}⚠${NC} $*"; }
fail(){ echo "${RED}✘${NC} $*"; exit 1; }

need() { command -v "$1" >/dev/null || fail "Missing required command: $1"; }

FILES=(
  "scripts/nv-db-start.sh"
  "scripts/nv-db-stop.sh"
  "scripts/nv-db-status.sh"
  "scripts/nv-pgbouncer-start.sh"
  "scripts/nv-pgbouncer-stop.sh"
  "scripts/nv-api-start.sh"
  "scripts/nv-api-stop.sh"
  "scripts/nv-stack-start.sh"
  "scripts/nv-stack-stop.sh"
  "scripts/nv-stack-status.sh"
)

echo "== Tooling =="
need container
command -v psql >/dev/null || warn "psql not found (only needed for connectivity tests)"
command -v curl >/dev/null || warn "curl not found (API health check)"
command -v nc >/dev/null || warn "nc not found (port checks)"
command -v md5 >/dev/null || warn "md5 not found (PgBouncer userlist hash on macOS)"

echo "== Files present & executable =="
for f in "${FILES[@]}"; do
  if [[ -f "$f" ]]; then
    [[ -x "$f" ]] || warn "Not executable: $f (fix: git update-index --chmod=+x $f)"
    ok "$f"
  else
    warn "Missing expected file: $f"
  fi
done

echo "== Static scan for common issues =="
grep -L '^#!/usr/bin/env bash' scripts/nv-*.sh && warn "Some scripts missing shebang"
grep -L 'set -euo pipefail' scripts/nv-*.sh && warn "Some scripts missing 'set -euo pipefail'"

# Using Apple Container (not Docker)
if grep -R --line-number -E '\bdocker\b' scripts/nv-*.sh; then
  warn "Found 'docker' usage. Prefer Apple 'container' CLI everywhere."
else
  ok "No 'docker' usage found; using 'container' CLI."
fi

# PgBouncer MD5 format check (md5(password+username))
if [[ -f scripts/nv-pgbouncer-start.sh ]]; then
  if grep -q 'md5' scripts/nv-pgbouncer-start.sh; then
    ok "PgBouncer script contains MD5 auth generation."
  else
    warn "PgBouncer script may not generate MD5 userlist entries."
  fi
fi

# DB wait / API health probes
grep -R --line-number -E 'pg_isready|select 1' scripts/nv-*.sh >/dev/null && ok "DB readiness checks found" || warn "No DB readiness check detected"
grep -R --line-number -E 'healthz|curl -f|curl -fsS' scripts/nv-api-start.sh >/dev/null && ok "API health probe found" || warn "No API health probe in nv-api-start.sh"

# Ports check
for P in 5433 6432 13370; do
  if lsof -i TCP:$P -sTCP:LISTEN >/dev/null 2>&1; then
    warn "Port $P currently in use on this host"
  else
    ok "Port $P free"
  fi
done

echo "== Quick dry-run syntax checks =="
# Show what images would be used (non-fatal if not present)
grep -R --line-number -E 'container (run|build|pull|image pull)' scripts/nv-*.sh && ok "Container invocations detected"

echo "== Summary =="
echo "If you saw only green checks (or benign warnings), scripts look good."
