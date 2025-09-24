#!/usr/bin/env bash
# Start eM sidecar (FastAPI) with Apple `container`
set -euo pipefail

CONTAINER_NAME="${EM_CONTAINER_NAME:-nv-em}"
IMAGE="${EM_IMAGE:-ninaivalaigal-em:latest}"
HOST_PORT="${EM_PORT:-7070}"
WAIT_SEC="${WAIT_SEC:-45}"

log(){ printf "\033[1;35m[eM]\033[0m %s\n" "$*"; }
die(){ printf "\033[1;31m[fail]\033[0m %s\n" "$*"; exit 1; }

need(){ command -v "$1" >/dev/null 2>&1 || die "Missing '$1'"; }

ensure_container(){ container system status >/dev/null 2>&1 || container system start; }

stop_existing(){
  if container list | awk '{print $NF}' | grep -qx "$CONTAINER_NAME"; then
    log "Stopping existing $CONTAINER_NAME…"
    container stop "$CONTAINER_NAME" >/dev/null 2>&1 || true
    container delete "$CONTAINER_NAME" >/dev/null 2>&1 || true
  fi
}

build_image(){
  # expects Dockerfile.em and sidecar/ present at repo root
  log "Building eM image: $IMAGE"
  container build -t "$IMAGE" -f Dockerfile.em .
}

run_container(){
  log "Starting $CONTAINER_NAME on :$HOST_PORT…"

  # Pass EM_SHARED_SECRET to container if set
  local env_args=""
  if [[ -n "${EM_SHARED_SECRET:-}" ]]; then
    env_args="--env EM_SHARED_SECRET=${EM_SHARED_SECRET}"
    log "Authentication enabled with shared secret"
  else
    log "⚠️  No EM_SHARED_SECRET set - authentication disabled"
  fi

  container run -d --name "$CONTAINER_NAME" \
    --publish "${HOST_PORT}:7070" \
    ${env_args} \
    "$IMAGE"
}

wait_ready(){
  log "Waiting for eM /health (timeout ${WAIT_SEC}s)…"
  local t=0
  until curl -fsS "http://127.0.0.1:${HOST_PORT}/health" >/dev/null 2>&1; do
    sleep 2; t=$((t+2))
    if [ "$t" -ge "$WAIT_SEC" ]; then
      container logs "$CONTAINER_NAME" | tail -n 80 || true
      die "eM did not become healthy in ${WAIT_SEC}s."
    fi
  done
  log "eM is healthy."
}

summary(){
  cat <<EOF

✅ eM sidecar up

Base:    http://localhost:${HOST_PORT}
Health:  http://localhost:${HOST_PORT}/health
Logs:    container logs -f ${CONTAINER_NAME}
Stop:    container stop ${CONTAINER_NAME} && container delete ${CONTAINER_NAME}

EOF
}

main(){
  need container
  need curl
  ensure_container
  stop_existing
  build_image
  run_container
  wait_ready
  summary
}
main "$@"
