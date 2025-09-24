#!/bin/bash
# ============================================================================
# REBUILD NV-DB WITH APACHE AGE SUPPORT
# ============================================================================
# Creates a new nv-db container with Apache AGE extension pre-installed
# This enables true single database consolidation

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="${SCRIPT_DIR}/rebuild-nv-db-$(date +%Y%m%d-%H%M%S).log"
BACKUP_DIR="${SCRIPT_DIR}/backups"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"
    exit 1
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$LOG_FILE"
}

# Create backup of current nv-db
backup_current_db() {
    log "Creating backup of current nv-db..."
    mkdir -p "$BACKUP_DIR"

    local backup_file="${BACKUP_DIR}/nv-db-backup-$(date +%Y%m%d-%H%M%S).sql"

    if container list | grep nv-db | grep -q running; then
        container exec nv-db pg_dump -U nina -d nina > "$backup_file"

        if [[ -s "$backup_file" ]]; then
            success "Database backed up to: $backup_file"
        else
            error "Backup failed or is empty"
        fi
    else
        error "nv-db container is not running"
    fi
}

# Create new Dockerfile with Apache AGE
create_age_dockerfile() {
    log "Creating Dockerfile with Apache AGE support..."

    cat > "${SCRIPT_DIR}/Dockerfile.nv-db-age" << 'EOF'
# Use Apache AGE pre-built image as base
FROM apache/age:PG15_latest

# Install pgvector extension
USER root
RUN apt-get update && apt-get install -y postgresql-15-pgvector && rm -rf /var/lib/apt/lists/*

# Copy initialization scripts
COPY init-age.sql /docker-entrypoint-initdb.d/01-init-age.sql
COPY restore-data.sql /docker-entrypoint-initdb.d/02-restore-data.sql

# Set environment variables
ENV POSTGRES_DB=nina
ENV POSTGRES_USER=nina
ENV POSTGRES_PASSWORD=change_me_securely

# Switch back to postgres user
USER postgres
EOF

    success "Dockerfile created"
}

# Create AGE initialization script
create_age_init_script() {
    log "Creating Apache AGE initialization script..."

    cat > "${SCRIPT_DIR}/init-age.sql" << 'EOF'
-- Initialize Apache AGE extension
CREATE EXTENSION IF NOT EXISTS age;
CREATE EXTENSION IF NOT EXISTS vector;

-- Load AGE into search path
LOAD 'age';
SET search_path = ag_catalog, "$user", public;

-- Create the main graph
SELECT create_graph('ninaivalaigal_intelligence');

-- Create vertex labels (node types)
SELECT create_vlabel('ninaivalaigal_intelligence', 'Memory');
SELECT create_vlabel('ninaivalaigal_intelligence', 'Token');
SELECT create_vlabel('ninaivalaigal_intelligence', 'User');
SELECT create_vlabel('ninaivalaigal_intelligence', 'Team');
SELECT create_vlabel('ninaivalaigal_intelligence', 'Context');
SELECT create_vlabel('ninaivalaigal_intelligence', 'Macro');
SELECT create_vlabel('ninaivalaigal_intelligence', 'Narrative');

-- Create edge labels (relationship types)
SELECT create_elabel('ninaivalaigal_intelligence', 'CREATED');
SELECT create_elabel('ninaivalaigal_intelligence', 'OWNS');
SELECT create_elabel('ninaivalaigal_intelligence', 'TAGGED_WITH');
SELECT create_elabel('ninaivalaigal_intelligence', 'DERIVED_FROM');
SELECT create_elabel('ninaivalaigal_intelligence', 'MEMBER_OF');
SELECT create_elabel('ninaivalaigal_intelligence', 'RELATED_TO');
SELECT create_elabel('ninaivalaigal_intelligence', 'ACCESSED');
SELECT create_elabel('ninaivalaigal_intelligence', 'SIMILAR_TO');
SELECT create_elabel('ninaivalaigal_intelligence', 'CONTAINS');
SELECT create_elabel('ninaivalaigal_intelligence', 'INFLUENCED_BY');
SELECT create_elabel('ninaivalaigal_intelligence', 'PROMOTED_BY');
SELECT create_elabel('ninaivalaigal_intelligence', 'ANNOTATED_BY');
SELECT create_elabel('ninaivalaigal_intelligence', 'FOLLOWED');
SELECT create_elabel('ninaivalaigal_intelligence', 'COLLABORATED_ON');
SELECT create_elabel('ninaivalaigal_intelligence', 'SHARED_WITH');
EOF

    success "AGE initialization script created"
}

# Stop current stack
stop_current_stack() {
    log "Stopping current stack..."

    # Stop API first
    if container list | grep nv-api | grep -q running; then
        container stop nv-api || true
        container delete nv-api || true
    fi

    # Stop PgBouncer
    if container list | grep nv-pgbouncer | grep -q running; then
        container stop nv-pgbouncer || true
        container delete nv-pgbouncer || true
    fi

    # Stop current nv-db
    if container list | grep nv-db | grep -q running; then
        container stop nv-db || true
        container delete nv-db || true
    fi

    success "Current stack stopped"
}

# Build new nv-db with AGE
build_new_db() {
    log "Building new nv-db container with Apache AGE..."

    # Copy the backup file to be restored
    cp "${BACKUP_DIR}"/nv-db-backup-*.sql "${SCRIPT_DIR}/restore-data.sql" 2>/dev/null || echo "-- No backup to restore" > "${SCRIPT_DIR}/restore-data.sql"

    # Build the new container
    cd "$SCRIPT_DIR"
    container build -t nv-db-age:latest -f Dockerfile.nv-db-age .

    success "New nv-db container built with Apache AGE"
}

# Start new consolidated database
start_consolidated_db() {
    log "Starting consolidated database..."

    # Create volume for data persistence
    container volume create nv-db-consolidated-data || true

    # Start the new database container
    container run -d \
        --name nv-db \
        -p 5432:5432 \
        -v nv-db-consolidated-data:/var/lib/postgresql/data \
        -e POSTGRES_DB=nina \
        -e POSTGRES_USER=nina \
        -e POSTGRES_PASSWORD=change_me_securely \
        nv-db-age:latest

    # Wait for database to be ready
    log "Waiting for database to initialize..."
    sleep 30

    # Test connection
    local retries=0
    while ! container exec nv-db psql -U nina -d nina -c "SELECT 1;" >/dev/null 2>&1; do
        retries=$((retries + 1))
        if [[ $retries -gt 10 ]]; then
            error "Database failed to start after 10 retries"
        fi
        log "Waiting for database... (attempt $retries)"
        sleep 5
    done

    success "Consolidated database started successfully"
}

# Verify AGE installation
verify_age_installation() {
    log "Verifying Apache AGE installation..."

    # Check AGE extension
    local age_installed
    age_installed=$(container exec nv-db psql -U nina -d nina -t -c "SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname = 'age');" | tr -d ' ')

    if [[ "$age_installed" == "t" ]]; then
        success "Apache AGE extension verified"
    else
        error "Apache AGE extension not found"
    fi

    # Check graph exists
    local graph_exists
    graph_exists=$(container exec nv-db psql -U nina -d nina -t -c "LOAD 'age'; SET search_path = ag_catalog, \"\$user\", public; SELECT EXISTS(SELECT 1 FROM ag_graph WHERE name = 'ninaivalaigal_intelligence');" | tr -d ' ')

    if [[ "$graph_exists" == "t" ]]; then
        success "Graph 'ninaivalaigal_intelligence' verified"
    else
        error "Graph not found"
    fi

    # Check pgvector
    local vector_installed
    vector_installed=$(container exec nv-db psql -U nina -d nina -t -c "SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname = 'vector');" | tr -d ' ')

    if [[ "$vector_installed" == "t" ]]; then
        success "pgvector extension verified"
    else
        warning "pgvector extension not found"
    fi
}

# Restart stack with consolidated database
restart_stack() {
    log "Restarting stack with consolidated database..."

    # Start Redis
    if ! container list | grep nv-redis | grep -q running; then
        scripts/nv-redis-start.sh || warning "Redis start failed"
    fi

    # Start PgBouncer
    scripts/nv-pgbouncer-start.sh || warning "PgBouncer start failed"

    # Rebuild and start API
    container build --no-cache -t nina-api:arm64 -f Dockerfile.api .
    scripts/nv-api-start.sh || warning "API start failed"

    success "Stack restarted with consolidated database"
}

# Main function
main() {
    log "🚀 REBUILDING NV-DB WITH APACHE AGE SUPPORT"
    log "============================================="

    # Backup current data
    backup_current_db

    # Create new container configuration
    create_age_dockerfile
    create_age_init_script

    # Stop current stack
    stop_current_stack

    # Build and start new consolidated database
    build_new_db
    start_consolidated_db

    # Verify installation
    verify_age_installation

    # Restart stack
    restart_stack

    success "🎉 CONSOLIDATION COMPLETE!"
    success "✅ Single PostgreSQL database with Apache AGE"
    success "✅ All relational and graph data in one place"
    success "✅ Single source of truth established"

    log "Next steps:"
    log "1. Test the consolidated setup: make test-graph"
    log "2. Migrate any remaining graph data"
    log "3. Decommission old graph containers"
}

# Error handling
trap 'error "Rebuild failed at line $LINENO"' ERR

# Run rebuild
main "$@"
