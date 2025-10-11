#!/usr/bin/env bash
# Nina Intelligence Stack Orchestrator
# Starts the consolidated ninaivalaigal-{env}-{service}-{runtime} stack

set -euo pipefail

# Environment and runtime detection
NINA_ENV="${NINA_ENV:-dev}"
NINA_RUNTIME="${NINA_RUNTIME:-apple}"

# Dynamic port assignment
POSTGRES_PORT="$("$(dirname "$0")/get-port.sh" postgres "$NINA_ENV" "$NINA_RUNTIME")"
REDIS_PORT="$("$(dirname "$0")/get-port.sh" redis "$NINA_ENV" "$NINA_RUNTIME")"
API_PORT="$("$(dirname "$0")/get-port.sh" api "$NINA_ENV" "$NINA_RUNTIME")"
UI_PORT="$("$(dirname "$0")/get-port.sh" ui "$NINA_ENV" "$NINA_RUNTIME")"

# Unified container names
DB_CONTAINER="ninaivalaigal-${NINA_ENV}-db-${NINA_RUNTIME}"
REDIS_CONTAINER="ninaivalaigal-${NINA_ENV}-redis-${NINA_RUNTIME}"
API_CONTAINER="ninaivalaigal-${NINA_ENV}-api-${NINA_RUNTIME}"
UI_CONTAINER="ninaivalaigal-${NINA_ENV}-ui-${NINA_RUNTIME}"

# Database name
DB_NAME="ninaivalaigal_${NINA_ENV}"

DB_ONLY=false
SKIP_API=false
SKIP_CACHE=false
WITH_UI=false
SKIP_UI=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --db-only) DB_ONLY=true ;;
    --skip-api) SKIP_API=true ;;
    --skip-cache) SKIP_CACHE=true ;;
    --with-ui) WITH_UI=true ;;
    --skip-ui) SKIP_UI=true ;;
    *) echo "Unknown flag: $1"; exit 1 ;;
  esac
  shift
done

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")"/.. && pwd)"
SCRIPTS="${ROOT}/scripts"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [NINA-STACK] $*"
}

log "🚀 Starting Nina Intelligence Stack..."
log "📍 Environment: $NINA_ENV"
log "🐳 Runtime: $NINA_RUNTIME"
log "🔌 Postgres: localhost:$POSTGRES_PORT"
log "🔴 Redis: localhost:$REDIS_PORT"
log "🌐 API: localhost:$API_PORT"
log "🎨 UI: localhost:$UI_PORT"
echo

# 1) Database (PostgreSQL + Apache AGE + pgvector)
log "Starting $DB_CONTAINER..."
if container list | grep -q "$DB_CONTAINER.*running"; then
  log "$DB_CONTAINER already running, skipping start."
else
  # Clean up any stopped container first
  container stop "$DB_CONTAINER" >/dev/null 2>&1 || true
  container delete "$DB_CONTAINER" >/dev/null 2>&1 || true

  container run -d --name "$DB_CONTAINER" \
    -p "$POSTGRES_PORT:5432" \
    -e POSTGRES_DB="$DB_NAME" \
    -e POSTGRES_USER=nina \
    -e POSTGRES_PASSWORD="${NINA_DB_PASSWORD:-secure_nina_password}" \
    -v "ninaivalaigal_${NINA_ENV}_db_data:/var/lib/postgresql/data" \
    nina-intelligence-db:arm64

  log "$DB_CONTAINER started successfully."

  # Wait for database to be ready
  log "Waiting for database to be ready..."
  sleep 10

  # Initialize tables if needed
  container exec "$DB_CONTAINER" psql -U nina -d "$DB_NAME" -c "
    CREATE TABLE IF NOT EXISTS users (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        email VARCHAR(255) NOT NULL UNIQUE,
        name VARCHAR(255) NOT NULL,
        password_hash VARCHAR(255) NOT NULL,
        account_type VARCHAR(50) NOT NULL DEFAULT 'individual',
        subscription_tier VARCHAR(50) NOT NULL DEFAULT 'free',
        role VARCHAR(50) NOT NULL DEFAULT 'user',
        created_via VARCHAR(50) NOT NULL DEFAULT 'api',
        email_verified BOOLEAN DEFAULT true,
        is_active BOOLEAN DEFAULT true,
        created_at TIMESTAMP DEFAULT NOW(),
        updated_at TIMESTAMP DEFAULT NOW()
    );

    INSERT INTO users (id, email, name, password_hash) VALUES (
        '00000000-0000-0000-0000-000000000001'::UUID,
        'test@ninaivalaigal.com',
        'Test User',
        '\$2b\$12\$LQv3c1yqBwEHxPuNYuTuT.BVf1ejmflPDcwLcaekRWC/vUiKvRg/2'
    ) ON CONFLICT (id) DO NOTHING;
  " >/dev/null 2>&1 || log "Database initialization completed or already done."
fi

if $DB_ONLY; then
  log "Database only requested. Done."
  exit 0
fi

# 2) Redis Cache
log "Starting $REDIS_CONTAINER..."
if container list | grep -q "$REDIS_CONTAINER.*running"; then
  log "$REDIS_CONTAINER already running, skipping start."
else
  # Clean up any stopped container first
  container stop "$REDIS_CONTAINER" >/dev/null 2>&1 || true
  container delete "$REDIS_CONTAINER" >/dev/null 2>&1 || true

  container run -d --name "$REDIS_CONTAINER" \
    -p "$REDIS_PORT:6379" \
    -e REDIS_PASSWORD="${NINA_REDIS_PASSWORD:-nina_redis_${NINA_ENV}_password}" \
    -v "ninaivalaigal_${NINA_ENV}_redis_data:/data" \
    redis:7-alpine redis-server --requirepass "${NINA_REDIS_PASSWORD:-nina_redis_${NINA_ENV}_password}" --maxmemory 512mb --maxmemory-policy allkeys-lru

  log "$REDIS_CONTAINER started successfully."
fi

# 3) API Server
if ! $SKIP_API; then
  log "Starting API..."

  # Get database and cache IPs
  DB_IP=$(container list | grep nina-intelligence-db | awk '{print $NF}')
  CACHE_IP=$(container list | grep nina-intelligence-cache | awk '{print $NF}')

  # Clean up any stopped API container first
  container stop ninaivalaigal-dev-api >/dev/null 2>&1 || true
  container delete ninaivalaigal-dev-api >/dev/null 2>&1 || true

  container run -d --name ninaivalaigal-dev-api -p 13370:8000 \
    -e DATABASE_URL=postgresql://nina:secure_nina_password@${DB_IP}:5432/ninaivalaigal \
    -e NINAIVALAIGAL_DATABASE_URL=postgresql://nina:secure_nina_password@${DB_IP}:5432/ninaivalaigal \
    -e REDIS_HOST=${CACHE_IP} \
    -e REDIS_PORT=6379 \
    -e NINAIVALAIGAL_JWT_SECRET=test-jwt-secret-for-ci \
    nina-api:arm64

  log "API started successfully."
else
  log "Skipping API per flag."
fi

# 4) UI
if ! $SKIP_UI; then
  log "Starting UI..."
  if container list | grep -q "ninaivalaigal-dev-ui.*running"; then
    log "ninaivalaigal-dev-ui already running, skipping start."
  else
    # Clean up any stopped UI container first
    container stop ninaivalaigal-dev-ui-customer >/dev/null 2>&1 || true
    container delete ninaivalaigal-dev-ui-customer >/dev/null 2>&1 || true

    # Build and start UI
    container build -t ninaivalaigal-ui:latest -f Dockerfile.ui . >/dev/null 2>&1
    container run -d --name ninaivalaigal-dev-ui-customer --publish 8081:8080 ninaivalaigal-ui:latest
    log "ninaivalaigal-dev-ui-customer started successfully."
  fi
else
  log "Skipping UI per flag."
fi

log "✅ Nina Intelligence Stack start complete."

# Show status
log "📊 Current stack status:"
container list | grep -E "(nina-intelligence|ninaivalaigal-dev)" || log "No nina intelligence containers found."
