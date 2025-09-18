#!/usr/bin/env bash
set -euo pipefail
NAME="${UI_CONTAINER_NAME:-nv-ui}"
PORT="${UI_PORT:-8080}"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

ok(){ printf "${GREEN}✓${NC} ui: %s\n" "$*"; }
fail(){ printf "${RED}✗${NC} ui: %s\n" "$*"; }
warn(){ printf "${YELLOW}⚠${NC} ui: %s\n" "$*"; }

# Check container status
if container list | awk '{print $NF}' | grep -qx "$NAME"; then
  ok "container running ($NAME)"
  CONTAINER_RUNNING=true
else
  fail "container not running"
  CONTAINER_RUNNING=false
fi

# Check port binding
if command -v nc >/dev/null 2>&1 && nc -z 127.0.0.1 "$PORT" >/dev/null 2>&1; then
  ok "port $PORT accessible"
  PORT_ACCESSIBLE=true
else
  fail "port $PORT not accessible"
  PORT_ACCESSIBLE=false
fi

# Check health endpoint
if curl -fsS "http://127.0.0.1:${PORT}/health" >/dev/null 2>&1; then
  ok "health endpoint responding"
  HEALTH_OK=true
else
  fail "health endpoint not responding"
  HEALTH_OK=false
fi

# Check main UI
if curl -fsS "http://127.0.0.1:${PORT}/" >/dev/null 2>&1; then
  ok "main UI responding"
  UI_OK=true
else
  fail "main UI not responding"
  UI_OK=false
fi

# Overall status
if [[ "$CONTAINER_RUNNING" == true && "$PORT_ACCESSIBLE" == true && "$HEALTH_OK" == true && "$UI_OK" == true ]]; then
  ok "all checks passed"
  exit 0
else
  fail "some checks failed"
  
  # Provide helpful diagnostics
  if [[ "$CONTAINER_RUNNING" == false ]]; then
    warn "start with: make ui-up or scripts/nv-ui-start.sh"
  elif [[ "$PORT_ACCESSIBLE" == false ]]; then
    warn "check port binding: container inspect $NAME"
  elif [[ "$HEALTH_OK" == false || "$UI_OK" == false ]]; then
    warn "check logs: container logs $NAME"
  fi
  
  exit 1
fi
