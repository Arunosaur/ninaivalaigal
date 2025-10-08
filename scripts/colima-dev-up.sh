#!/usr/bin/env bash
# Start ninaivalaigal dev environment on Colima
# Follows the Apple Container CLI pattern with dynamic configuration

set -euo pipefail

# -------- Runtime: Colima Dev Environment --------
NINA_ENV="${NINA_ENV:-dev}"
NINA_RUNTIME="colima"

# -------- Ports (from Runtime × Environment matrix) --------
POSTGRES_PORT="${POSTGRES_PORT:-5442}"
PGBOUNCER_PORT="${PGBOUNCER_PORT:-6442}"
REDIS_PORT="${REDIS_PORT:-6389}"
API_PORT="${API_PORT:-13380}"
CUSTOMER_APP_PORT="${CUSTOMER_APP_PORT:-8091}"
ADMIN_CONSOLE_PORT="${ADMIN_CONSOLE_PORT:-8191}"

# -------- Database Credentials --------
NINA_DB_USER="${NINA_DB_USER:-nina}"
NINA_DB_PASSWORD="${NINA_DB_PASSWORD:-dev_password_change_in_production}"

# -------- Redis --------
NINA_REDIS_PASSWORD="${NINA_REDIS_PASSWORD:-dev_redis_password}"

# -------- Auth --------
NINA_JWT_SECRET="${NINA_JWT_SECRET:-dev_jwt_secret_change_in_production}"

# -------- API Config --------
NINA_DEBUG="${NINA_DEBUG:-1}"
UVICORN_RELOAD="${UVICORN_RELOAD:-1}"
LOG_LEVEL="${LOG_LEVEL:-debug}"
VOLUME_MODE="${VOLUME_MODE:-rw}"

# --------------------------------------------------

log()  { printf "\033[1;34m[colima]\033[0m %s\n" "$*"; }
warn() { printf "\033[1;33m[warn]\033[0m %s\n" "$*"; }
die()  { printf "\033[1;31m[fail]\033[0m %s\n" "$*"; exit 1; }

ensure_colima() {
  command -v colima >/dev/null 2>&1 || die "Colima not installed. Run: brew install colima"

  if ! colima status >/dev/null 2>&1; then
    log "Starting Colima..."
    colima start --cpu 4 --memory 8 --disk 60 --arch aarch64
  fi

  log "Colima is running"
}

ensure_docker() {
  command -v docker >/dev/null 2>&1 || die "Docker CLI not installed"
  docker context use colima >/dev/null 2>&1 || warn "Could not switch to colima context"
}

start_stack() {
  local profile="${1:-all}"

  log "Starting Colima dev environment..."
  log "  Profile: ${profile}"
  log "  Ports: DB=${POSTGRES_PORT}, Redis=${REDIS_PORT}, API=${API_PORT}"
  log "  Data: ./data/postgres_${NINA_ENV} (shared across runtimes)"

  cd "$(dirname "$0")/.."

  # Use .env.colima.dev which has all the correct ports
  if [ "$profile" = "all" ]; then
    docker-compose -f compose.colima.yml --env-file .env.colima.dev \
      --profile external --profile internal up -d
  else
    docker-compose -f compose.colima.yml --env-file .env.colima.dev \
      --profile "$profile" up -d
  fi
}

wait_healthy() {
  log "Waiting for services to be healthy..."
  sleep 5

  local max_wait=60
  local elapsed=0

  while [ $elapsed -lt $max_wait ]; do
    if docker ps --filter "name=ninaivalaigal-${NINA_ENV}-db" --filter "health=healthy" | grep -q .; then
      log "✅ Database is healthy"
      break
    fi
    sleep 2
    elapsed=$((elapsed + 2))
  done

  if [ $elapsed -ge $max_wait ]; then
    warn "Database did not become healthy in ${max_wait}s"
  fi
}

verify_ports() {
  log "Verifying port bindings..."
  docker ps --filter "name=ninaivalaigal-${NINA_ENV}" --format "{{.Names}}\t{{.Ports}}" | \
    grep -E "(db|redis|api)" || true
}

test_connection() {
  log "Testing database connection on port ${POSTGRES_PORT}..."

  if command -v psql >/dev/null 2>&1; then
    if PGPASSWORD="${NINA_DB_PASSWORD}" psql -h localhost -p "${POSTGRES_PORT}" -U "${NINA_DB_USER}" -d "ninaivalaigal_${NINA_ENV}" -c "SELECT 1" >/dev/null 2>&1; then
      log "✅ Database connection successful"
    else
      warn "Could not connect to database on port ${POSTGRES_PORT}"
    fi
  fi
}

show_summary() {
  cat <<EOF

🦙 Colima dev environment is running!

📊 Services:
  Database:        localhost:${POSTGRES_PORT}
  Redis:           localhost:${REDIS_PORT}
  API:             http://localhost:${API_PORT}/docs
  Customer App:    http://localhost:${CUSTOMER_APP_PORT}
  Admin Console:   http://localhost:${ADMIN_CONSOLE_PORT}

📁 Data Directory:
  ./data/postgres_${NINA_ENV}  (shared across Docker/Colima/Apple CLI)
  ./data/redis_${NINA_ENV}

🔧 Manage:
  Logs:    docker-compose -f compose.colima.yml logs -f
  Stop:    docker-compose -f compose.colima.yml down
  Status:  docker ps --filter "name=ninaivalaigal-${NINA_ENV}"

🔌 Database URL:
  postgresql://${NINA_DB_USER}:${NINA_DB_PASSWORD}@localhost:${POSTGRES_PORT}/ninaivalaigal_${NINA_ENV}

EOF
}

main() {
  local profile="${1:-all}"

  ensure_colima
  ensure_docker
  start_stack "$profile"
  wait_healthy
  verify_ports
  test_connection
  show_summary
}

main "$@"
