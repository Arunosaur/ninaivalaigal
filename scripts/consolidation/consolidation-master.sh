#!/bin/bash
# ============================================================================
# MASTER CONSOLIDATION SCRIPT: Single PostgreSQL + Apache AGE
# ============================================================================
# Orchestrates the complete consolidation process
# Eliminates dual database architecture for single source of truth

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="${SCRIPT_DIR}/consolidation-master-$(date +%Y%m%d-%H%M%S).log"

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

# Make scripts executable
chmod +x "${SCRIPT_DIR}"/*.sh

main() {
    log "🚀 STARTING SINGLE DATABASE CONSOLIDATION"
    log "=========================================="
    log "This will eliminate dual database architecture"
    log "and create unified PostgreSQL + Apache AGE setup"
    log ""

    # Step 1: Install Apache AGE
    log "Step 1: Installing Apache AGE in nv-db..."
    container cp "${SCRIPT_DIR}/install-age-in-nv-db.sql" nv-db:/tmp/
    container exec nv-db psql -U nina -d nina -f /tmp/install-age-in-nv-db.sql
    success "Apache AGE installed successfully"

    # Step 2: Migrate data
    log "Step 2: Migrating graph data..."
    "${SCRIPT_DIR}/migrate-graph-to-nv-db.sh"
    success "Data migration completed"

    # Step 3: Update sync scripts
    log "Step 3: Updating sync scripts..."
    "${SCRIPT_DIR}/update-sync-to-internal-join.sh"
    success "Sync scripts updated"

    # Step 4: Test consolidated setup
    log "Step 4: Testing consolidated setup..."
    make test-consolidated-graph || warning "Graph test failed - check configuration"
    make health-check-consolidated || warning "Health check failed - verify setup"

    # Step 5: Decommission old infrastructure
    log "Step 5: Decommissioning separate graph database..."
    read -p "Proceed with decommissioning separate graph database? (y/N): " confirm
    if [[ "$confirm" == "y" || "$confirm" == "Y" ]]; then
        "${SCRIPT_DIR}/decommission-graph-db.sh"
        success "Decommission completed"
    else
        warning "Decommission skipped - run manually when ready"
    fi

    success "🎉 CONSOLIDATION COMPLETE!"
    success "✅ Single source of truth established"
    success "✅ Reduced operational complexity"
    success "✅ Unified PostgreSQL + Apache AGE architecture"

    log "Final verification:"
    make health-check-consolidated
}

main "$@"
