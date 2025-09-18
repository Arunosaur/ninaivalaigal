#!/usr/bin/env bash
# Start ninaivalaigal FastAPI server on Mac Studio via Apple Container CLI
# Connects to existing database (direct or via PgBouncer)

set -euo pipefail

# -------- settings (env overrides allowed) --------
CONTAINER_NAME="${API_CONTAINER_NAME:-nv-api}"
IMAGE="${API_IMAGE:-python:3.11-slim}"
HOST_PORT="${API_PORT:-13370}"           # host -> container 8000
DB_HOST="${POSTGRES_HOST:-localhost}"
DB_PORT="${PGBOUNCER_PORT:-6432}"        # Use PgBouncer by default, fallback to direct DB
DB_NAME="${POSTGRES_DB:-nina}"
DB_USER="${POSTGRES_USER:-nina}"
DB_PASS="${POSTGRES_PASSWORD:-change_me_securely}"
JWT_SECRET="${NINAIVALAIGAL_JWT_SECRET:-dev-secret-change-in-production}"
WAIT_SEC="${WAIT_SEC:-60}"
# --------------------------------------------------

log()  { printf "\033[1;34m[info]\033[0m %s\n" "$*"; }
warn() { printf "\033[1;33m[warn]\033[0m %s\n" "$*"; }
die()  { printf "\033[1;31m[fail]\033[0m %s\n" "$*"; exit 1; }

ensure_bin() {
  command -v "$1" >/dev/null 2>&1 || die "Missing '$1'. Install and retry."
}

port_in_use() {
  if command -v lsof >/dev/null 2>&1; then
    lsof -i TCP:"$1" -sTCP:LISTEN >/dev/null 2>&1
  else
    nc -z 127.0.0.1 "$1" >/dev/null 2>&1
  fi
}

maybe_pull() {
  if container images list | grep -q "$(echo "$IMAGE" | sed 's/:.*//')" ; then
    log "Image cache present; skipping pull."
  else
    log "Pulling image: $IMAGE"
    container images pull "$IMAGE" || warn "Pull failed, will try to run anyway"
  fi
}

ensure_container_system() {
  if ! container system status >/dev/null 2>&1; then
    log "Starting container system…"
    container system start
  fi
}

check_database() {
  log "Checking database connectivity..."
  
  # Try PgBouncer first, then direct database
  if nc -z "$DB_HOST" "$DB_PORT" >/dev/null 2>&1; then
    log "Database reachable at $DB_HOST:$DB_PORT (via PgBouncer)"
  elif nc -z "$DB_HOST" "${POSTGRES_PORT:-5433}" >/dev/null 2>&1; then
    warn "PgBouncer not available, using direct database connection"
    DB_PORT="${POSTGRES_PORT:-5433}"
    log "Database reachable at $DB_HOST:$DB_PORT (direct)"
  else
    die "Database not reachable. Start database and/or PgBouncer first:
  ./nv-db-start.sh
  ./nv-pgbouncer-start.sh"
  fi
}

stop_existing() {
  if container list | grep -q "$CONTAINER_NAME"; then
    warn "Container '$CONTAINER_NAME' exists. Stopping & removing…"
    container stop "$CONTAINER_NAME" >/dev/null 2>&1 || true
    container delete "$CONTAINER_NAME" >/dev/null 2>&1 || true
  fi
}

prepare_api_context() {
  local context_dir="/tmp/ninaivalaigal-api-$CONTAINER_NAME"
  rm -rf "$context_dir"
  mkdir -p "$context_dir"
  
  # Copy server code to container context
  if [ -d "server" ]; then
    cp -r server "$context_dir/"
    log "Copied server code to container context"
  else
    die "Server directory not found. Run from project root."
  fi
  
  # Copy requirements if available
  if [ -f "requirements.txt" ]; then
    cp requirements.txt "$context_dir/"
  fi
  
  # Create Dockerfile for ninaivalaigal API
  cat > "$context_dir/Dockerfile" <<EOF
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    gcc \\
    libpq-dev \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt* ./
RUN pip install --no-cache-dir "psycopg[binary]" sqlalchemy alembic fastapi "uvicorn[standard]" httpx
RUN if [ -f requirements.txt ]; then pip install --no-cache-dir -r requirements.txt; fi

# Copy server code
COPY server/ ./server/

# Set Python path
ENV PYTHONPATH=/app/server

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
  CMD curl -f http://localhost:8000/health || exit 1

# Run the API server
CMD ["uvicorn", "server.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
EOF

  echo "$context_dir"
}

build_api_image() {
  local context_dir="$1"
  local api_image="ninaivalaigal-api:latest"
  
  log "Building ninaivalaigal API image..."
  container build -t "$api_image" "$context_dir" || die "Failed to build API image"
  log "API image built successfully: $api_image"
  echo "$api_image"
}

run_api() {
  local context_dir
  local api_image
  
  context_dir=$(prepare_api_context)
  api_image=$(build_api_image "$context_dir")
  
  log "Starting ninaivalaigal API container '$CONTAINER_NAME' on host port ${HOST_PORT}…"
  container run --detach --name "$CONTAINER_NAME" \
    --publish "${HOST_PORT}:8000" \
    --env "DATABASE_URL=postgresql://${DB_USER}:${DB_PASS}@${DB_HOST}:${DB_PORT}/${DB_NAME}" \
    --env "NINAIVALAIGAL_JWT_SECRET=${JWT_SECRET}" \
    --env "PYTHONPATH=/app/server" \
    "$api_image"
  
  # Cleanup temporary context
  rm -rf "$context_dir"
}

wait_ready() {
  log "Waiting for API server to accept connections (timeout ${WAIT_SEC}s)…"
  local t=0
  until curl -f "http://127.0.0.1:${HOST_PORT}/health" >/dev/null 2>&1; do
    sleep 3
    t=$((t+3))
    if [ "$t" -ge "$WAIT_SEC" ]; then
      container logs "$CONTAINER_NAME" | tail -n 30 || true
      die "API server did not become ready within ${WAIT_SEC}s."
    fi
    echo -n "."
  done
  echo ""
  log "API server is ready."
}

test_api() {
  log "Testing API endpoints..."
  
  # Test health endpoint
  if curl -f "http://127.0.0.1:${HOST_PORT}/health" >/dev/null 2>&1; then
    log "✅ Health endpoint responding"
  else
    warn "❌ Health endpoint not responding"
  fi
  
  # Test API docs
  if curl -f "http://127.0.0.1:${HOST_PORT}/docs" >/dev/null 2>&1; then
    log "✅ API documentation available"
  else
    warn "❌ API documentation not available"
  fi
}

connection_summary() {
  cat <<EOF

✅ ninaivalaigal API is up via Apple Container CLI.

API Endpoints:
  Health:        http://localhost:${HOST_PORT}/health
  Documentation: http://localhost:${HOST_PORT}/docs
  API Base:      http://localhost:${HOST_PORT}/

Environment:
  DATABASE_URL=postgresql://${DB_USER}:***@${DB_HOST}:${DB_PORT}/${DB_NAME}
  JWT_SECRET=***

Container logs:
  container logs ${CONTAINER_NAME}

Stop:
  container stop ${CONTAINER_NAME} && container delete ${CONTAINER_NAME}

Full Stack Status:
  Database:  ./nv-db-status.sh
  PgBouncer: container list | grep nv-pgbouncer
  API:       curl http://localhost:${HOST_PORT}/health

EOF
}

main() {
  ensure_bin container
  ensure_bin curl
  ensure_container_system

  if port_in_use "$HOST_PORT"; then
    die "Host port ${HOST_PORT} is already in use. Choose another API_PORT or stop the conflicting service."
  fi

  check_database
  maybe_pull
  stop_existing
  run_api
  wait_ready
  test_api
  connection_summary
}

main "$@"
