#!/usr/bin/env bash
# Nina Intelligence Stack Orchestrator
# Starts the consolidated nina-intelligence-db + nina-intelligence-cache + API stack

set -euo pipefail

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

# 1) nina-intelligence-db (PostgreSQL + Apache AGE + pgvector)
log "Starting nina-intelligence-db..."
if container list | grep -q "nina-intelligence-db.*running"; then
  log "nina-intelligence-db already running, skipping start."
else
  # Clean up any stopped container first
  container stop nina-intelligence-db >/dev/null 2>&1 || true
  container delete nina-intelligence-db >/dev/null 2>&1 || true

  container run -d --name nina-intelligence-db \
    -p 5432:5432 \
    -e POSTGRES_DB=ninaivalaigal \
    -e POSTGRES_USER=nina \
    -e POSTGRES_PASSWORD=secure_nina_password \
    -v nina_intelligence_db_data:/var/lib/postgresql/data \
    nina-intelligence-db:arm64

  log "nina-intelligence-db started successfully."

  # Wait for database to be ready
  log "Waiting for database to be ready..."
  sleep 10

  # Initialize tables if needed
  container exec nina-intelligence-db psql -U nina -d ninaivalaigal -c "
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

# Stop early if db-only
if $DB_ONLY; then
  log "Database only requested. Done."
  exit 0
fi

# 2) nina-intelligence-cache (Redis)
if ! $SKIP_CACHE; then
  log "Starting nina-intelligence-cache..."
  if container list | grep -q "nina-intelligence-cache.*running"; then
    log "nina-intelligence-cache already running, skipping start."
  else
    # Clean up any stopped Redis container first
    container stop nina-intelligence-cache >/dev/null 2>&1 || true
    container delete nina-intelligence-cache >/dev/null 2>&1 || true

    container run -d --name nina-intelligence-cache \
      -p 6379:6379 \
      -v nina_intelligence_cache_data:/data \
      redis:7-alpine redis-server --maxmemory 256mb --maxmemory-policy allkeys-lru
    log "nina-intelligence-cache started successfully."
  fi
else
  log "Skipping nina-intelligence-cache per flag."
fi

# 3) API
if ! $SKIP_API; then
  log "Starting API..."

  # Get database and cache IPs
  DB_IP=$(container list | grep nina-intelligence-db | awk '{print $NF}')
  CACHE_IP=$(container list | grep nina-intelligence-cache | awk '{print $NF}')

  # Clean up any stopped API container first
  container stop nv-api >/dev/null 2>&1 || true
  container delete nv-api >/dev/null 2>&1 || true

  container run -d --name nv-api -p 13370:8000 \
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
  if container list | grep -q "nv-ui.*running"; then
    log "nv-ui already running, skipping start."
  else
    # Clean up any stopped UI container first
    container stop nv-ui >/dev/null 2>&1 || true
    container delete nv-ui >/dev/null 2>&1 || true

    # Build and start UI
    container build -t ninaivalaigal-ui:latest -f Dockerfile.ui . >/dev/null 2>&1
    container run -d --name nv-ui --publish 8081:8080 ninaivalaigal-ui:latest
    log "nv-ui started successfully."
  fi
else
  log "Skipping UI per flag."
fi

log "✅ Nina Intelligence Stack start complete."

# Show status
log "📊 Current stack status:"
container list | grep -E "(nina-intelligence|nv-api|nv-ui)" || log "No nina intelligence containers found."
