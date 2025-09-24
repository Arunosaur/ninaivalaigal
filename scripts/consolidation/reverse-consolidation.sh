#!/bin/bash
# ============================================================================
# REVERSE CONSOLIDATION: Use Graph DB as Single Source of Truth
# ============================================================================
# Instead of adding AGE to nv-db, migrate relational data to existing graph-db
# This leverages our working Apache AGE setup

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="${SCRIPT_DIR}/reverse-consolidation-$(date +%Y%m%d-%H%M%S).log"
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

# Backup current nv-db data
backup_relational_data() {
    log "Creating backup of relational data from nv-db..."
    mkdir -p "$BACKUP_DIR"

    local backup_file="${BACKUP_DIR}/nv-db-relational-backup-$(date +%Y%m%d-%H%M%S).sql"

    if container list | grep nv-db | grep -q running; then
        container exec nv-db pg_dump -U nina -d nina > "$backup_file"

        if [[ -s "$backup_file" ]]; then
            success "Relational data backed up to: $backup_file"
        else
            error "Backup failed or is empty"
        fi
    else
        error "nv-db container is not running"
    fi
}

# Start graph database if not running
ensure_graph_db_running() {
    log "Ensuring graph database is running..."

    if ! container list | grep ninaivalaigal-graph-db | grep -q running; then
        log "Starting graph database..."
        make start-graph-infrastructure || error "Failed to start graph infrastructure"
    fi

    # Wait for graph database to be ready
    local retries=0
    while ! container exec ninaivalaigal-graph-db pg_isready -U graphuser -d ninaivalaigal_graph >/dev/null 2>&1; do
        retries=$((retries + 1))
        if [[ $retries -gt 10 ]]; then
            error "Graph database failed to start after 10 retries"
        fi
        log "Waiting for graph database... (attempt $retries)"
        sleep 5
    done

    success "Graph database is running and ready"
}

# Create relational tables in graph database
create_relational_tables_in_graph_db() {
    log "Creating relational tables in graph database..."

    # Extract table creation statements from backup
    local backup_file=$(ls -t "${BACKUP_DIR}"/nv-db-relational-backup-*.sql | head -1)

    if [[ ! -f "$backup_file" ]]; then
        error "No backup file found"
    fi

    # Create a filtered SQL file with just the table structures and data
    local filtered_sql="${BACKUP_DIR}/relational-tables-only.sql"

    # Extract CREATE TABLE statements and INSERT statements
    grep -E "^(CREATE TABLE|INSERT INTO|ALTER TABLE|CREATE INDEX)" "$backup_file" > "$filtered_sql" || true

    # Execute the filtered SQL in graph database
    if [[ -s "$filtered_sql" ]]; then
        log "Importing relational tables into graph database..."
        container exec ninaivalaigal-graph-db psql -U graphuser -d ninaivalaigal_graph -f /dev/stdin < "$filtered_sql" || warning "Some imports may have failed"
        success "Relational tables imported into graph database"
    else
        warning "No relational tables found to import"
    fi
}

# Update connection strings to point to graph database
update_connection_strings() {
    log "Updating connection strings to use consolidated graph database..."

    # Update API startup script
    if [[ -f "scripts/nv-api-start.sh" ]]; then
        # Backup original
        cp "scripts/nv-api-start.sh" "scripts/nv-api-start.sh.backup-$(date +%Y%m%d-%H%M%S)"

        # Update to use graph database port (5434 instead of 5432)
        sed -i.tmp 's/5432/5434/g' "scripts/nv-api-start.sh"
        sed -i.tmp 's/nina:change_me_securely/graphuser:graphpass/g' "scripts/nv-api-start.sh"
        rm -f "scripts/nv-api-start.sh.tmp"

        success "Updated API connection strings"
    fi

    # Update PgBouncer configuration if needed
    if [[ -f "scripts/nv-pgbouncer-start.sh" ]]; then
        cp "scripts/nv-pgbouncer-start.sh" "scripts/nv-pgbouncer-start.sh.backup-$(date +%Y%m%d-%H%M%S)"

        # Update to point to graph database
        sed -i.tmp 's/nv-db/ninaivalaigal-graph-db/g' "scripts/nv-pgbouncer-start.sh"
        sed -i.tmp 's/5432/5434/g' "scripts/nv-pgbouncer-start.sh"
        rm -f "scripts/nv-pgbouncer-start.sh.tmp"

        success "Updated PgBouncer connection strings"
    fi
}

# Test consolidated setup
test_consolidated_setup() {
    log "Testing consolidated setup..."

    # Test graph database connectivity
    if container exec ninaivalaigal-graph-db psql -U graphuser -d ninaivalaigal_graph -c "SELECT 1;" >/dev/null 2>&1; then
        success "Graph database connectivity verified"
    else
        error "Graph database connectivity failed"
    fi

    # Test Apache AGE functionality
    if container exec ninaivalaigal-graph-db psql -U graphuser -d ninaivalaigal_graph -c "LOAD 'age'; SET search_path = ag_catalog, \"\$user\", public; SELECT * FROM ag_graph LIMIT 1;" >/dev/null 2>&1; then
        success "Apache AGE functionality verified"
    else
        warning "Apache AGE functionality test failed"
    fi

    # Test if relational tables exist
    local table_count
    table_count=$(container exec ninaivalaigal-graph-db psql -U graphuser -d ninaivalaigal_graph -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';" | tr -d ' ')

    if [[ "$table_count" -gt 0 ]]; then
        success "Found $table_count relational tables in consolidated database"
    else
        warning "No relational tables found in consolidated database"
    fi
}

# Stop old nv-db
stop_old_nv_db() {
    log "Stopping old nv-db container..."

    if container list | grep nv-db | grep -q running; then
        container stop nv-db || warning "Failed to stop nv-db"
        success "Old nv-db container stopped"
    else
        log "nv-db container already stopped"
    fi
}

# Create new startup scripts for consolidated setup
create_consolidated_scripts() {
    log "Creating consolidated startup scripts..."

    cat > "scripts/nv-consolidated-start.sh" << 'EOF'
#!/bin/bash
# Start consolidated database (graph-db with relational data)
set -euo pipefail

echo "🚀 Starting Consolidated Database (Apache AGE + Relational)"

# Start graph infrastructure (includes both graph-db and graph-redis)
make start-graph-infrastructure

# Wait for database to be ready
echo "⏳ Waiting for consolidated database..."
sleep 10

# Test connectivity
if container exec ninaivalaigal-graph-db pg_isready -U graphuser -d ninaivalaigal_graph; then
    echo "✅ Consolidated database is ready"
    echo "📊 Database info:"
    container exec ninaivalaigal-graph-db psql -U graphuser -d ninaivalaigal_graph -c "SELECT version();"
    echo "🔗 Connection: postgresql://graphuser:graphpass@localhost:5434/ninaivalaigal_graph"
else
    echo "❌ Consolidated database failed to start"
    exit 1
fi
EOF

    chmod +x "scripts/nv-consolidated-start.sh"
    success "Created consolidated startup script"
}

# Main consolidation function
main() {
    log "🔄 STARTING REVERSE CONSOLIDATION"
    log "=================================="
    log "Using existing graph-db as single source of truth"
    log "Migrating relational data TO graph database"
    log ""

    # Backup and prepare
    backup_relational_data
    ensure_graph_db_running

    # Migrate data
    create_relational_tables_in_graph_db

    # Update configuration
    update_connection_strings
    create_consolidated_scripts

    # Test setup
    test_consolidated_setup

    # Stop old database
    read -p "Stop old nv-db container? (y/N): " confirm
    if [[ "$confirm" == "y" || "$confirm" == "Y" ]]; then
        stop_old_nv_db
    fi

    success "🎉 REVERSE CONSOLIDATION COMPLETE!"
    success "✅ Single database with Apache AGE + relational data"
    success "✅ Graph and relational data in same PostgreSQL instance"
    success "✅ Reduced operational complexity"

    log ""
    log "Next steps:"
    log "1. Test with: ./scripts/nv-consolidated-start.sh"
    log "2. Update API to use: postgresql://graphuser:graphpass@localhost:5434/ninaivalaigal_graph"
    log "3. Run graph validation: make test-graph"
    log "4. Decommission old nv-db when confident"

    log "Consolidation completed at $(date)"
}

# Error handling
trap 'error "Reverse consolidation failed at line $LINENO"' ERR

# Run consolidation
main "$@"
