#!/bin/bash
# ============================================================================
# SINGLE DATABASE CONSOLIDATION: Decommission Separate Graph Database
# ============================================================================
# This script safely removes the separate graph-db container and related resources
# Only run AFTER successful migration to consolidated nv-db
# Includes safety checks and rollback capabilities

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="${SCRIPT_DIR}/decommission-$(date +%Y%m%d-%H%M%S).log"
BACKUP_DIR="${SCRIPT_DIR}/backups"

# Container and volume names
GRAPH_DB_CONTAINER="ninaivalaigal-graph-db"
GRAPH_REDIS_CONTAINER="ninaivalaigal-graph-redis"
GRAPH_DB_VOLUME="ninaivalaigal-graph-db-data"
GRAPH_REDIS_VOLUME="ninaivalaigal-graph-redis-data"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"
    exit 1
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "$LOG_FILE"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$LOG_FILE"
}

# Safety confirmation
confirm_decommission() {
    log "🚨 GRAPH DATABASE DECOMMISSION SAFETY CHECK 🚨"
    log ""
    log "This script will permanently remove:"
    log "- Container: $GRAPH_DB_CONTAINER"
    log "- Container: $GRAPH_REDIS_CONTAINER"
    log "- Volume: $GRAPH_DB_VOLUME"
    log "- Volume: $GRAPH_REDIS_VOLUME"
    log ""
    warning "This action is IRREVERSIBLE!"
    warning "Ensure migration to nv-db is complete and verified!"
    log ""

    read -p "Have you successfully migrated all graph data to nv-db? (yes/no): " migration_confirmed
    if [[ "$migration_confirmed" != "yes" ]]; then
        error "Migration not confirmed. Aborting decommission."
    fi

    read -p "Have you tested the consolidated database functionality? (yes/no): " testing_confirmed
    if [[ "$testing_confirmed" != "yes" ]]; then
        error "Testing not confirmed. Aborting decommission."
    fi

    read -p "Do you have recent backups of the graph database? (yes/no): " backup_confirmed
    if [[ "$backup_confirmed" != "yes" ]]; then
        error "Backups not confirmed. Aborting decommission."
    fi

    log ""
    log "Type 'DECOMMISSION' to proceed with permanent removal:"
    read -p "> " final_confirmation
    if [[ "$final_confirmation" != "DECOMMISSION" ]]; then
        error "Final confirmation not provided. Aborting decommission."
    fi

    success "Safety checks passed. Proceeding with decommission..."
}

# Check container status
check_container_status() {
    local container_name="$1"

    if container list | grep -q "$container_name"; then
        local status
        status=$(container list | grep "$container_name" | awk '{print $5}')
        log "Container $container_name status: $status"
        return 0
    else
        log "Container $container_name not found"
        return 1
    fi
}

# Create final backup before decommission
create_final_backup() {
    log "Creating final backup before decommission..."

    mkdir -p "$BACKUP_DIR"

    if check_container_status "$GRAPH_DB_CONTAINER"; then
        local backup_file="${BACKUP_DIR}/final-graph-db-backup-$(date +%Y%m%d-%H%M%S).sql"

        if container list | grep "$GRAPH_DB_CONTAINER" | grep -q "running"; then
            log "Creating final database dump..."
            container exec "$GRAPH_DB_CONTAINER" pg_dump -U postgres -d postgres > "$backup_file" || warning "Backup creation failed"

            if [[ -s "$backup_file" ]]; then
                success "Final backup created: $backup_file"
            else
                warning "Backup file is empty or creation failed"
            fi
        else
            warning "Graph database container not running, skipping backup"
        fi
    else
        log "Graph database container not found, skipping backup"
    fi
}

# Stop containers gracefully
stop_containers() {
    log "Stopping graph database containers..."

    # Stop graph database container
    if check_container_status "$GRAPH_DB_CONTAINER"; then
        if container list | grep "$GRAPH_DB_CONTAINER" | grep -q "running"; then
            log "Stopping $GRAPH_DB_CONTAINER..."
            container stop "$GRAPH_DB_CONTAINER" || warning "Failed to stop $GRAPH_DB_CONTAINER"
            success "$GRAPH_DB_CONTAINER stopped"
        else
            log "$GRAPH_DB_CONTAINER already stopped"
        fi
    fi

    # Stop graph Redis container
    if check_container_status "$GRAPH_REDIS_CONTAINER"; then
        if container list | grep "$GRAPH_REDIS_CONTAINER" | grep -q "running"; then
            log "Stopping $GRAPH_REDIS_CONTAINER..."
            container stop "$GRAPH_REDIS_CONTAINER" || warning "Failed to stop $GRAPH_REDIS_CONTAINER"
            success "$GRAPH_REDIS_CONTAINER stopped"
        else
            log "$GRAPH_REDIS_CONTAINER already stopped"
        fi
    fi
}

# Remove containers
remove_containers() {
    log "Removing graph database containers..."

    # Remove graph database container
    if check_container_status "$GRAPH_DB_CONTAINER"; then
        log "Removing $GRAPH_DB_CONTAINER..."
        container delete "$GRAPH_DB_CONTAINER" || warning "Failed to remove $GRAPH_DB_CONTAINER"
        success "$GRAPH_DB_CONTAINER removed"
    else
        log "$GRAPH_DB_CONTAINER not found, skipping removal"
    fi

    # Remove graph Redis container
    if check_container_status "$GRAPH_REDIS_CONTAINER"; then
        log "Removing $GRAPH_REDIS_CONTAINER..."
        container delete "$GRAPH_REDIS_CONTAINER" || warning "Failed to remove $GRAPH_REDIS_CONTAINER"
        success "$GRAPH_REDIS_CONTAINER removed"
    else
        log "$GRAPH_REDIS_CONTAINER not found, skipping removal"
    fi
}

# Remove volumes
remove_volumes() {
    log "Removing graph database volumes..."

    # List existing volumes
    log "Current volumes:"
    container volume list || true

    # Remove graph database volume
    if container volume list | grep -q "$GRAPH_DB_VOLUME"; then
        log "Removing volume $GRAPH_DB_VOLUME..."
        container volume delete "$GRAPH_DB_VOLUME" || warning "Failed to remove volume $GRAPH_DB_VOLUME"
        success "Volume $GRAPH_DB_VOLUME removed"
    else
        log "Volume $GRAPH_DB_VOLUME not found, skipping removal"
    fi

    # Remove graph Redis volume
    if container volume list | grep -q "$GRAPH_REDIS_VOLUME"; then
        log "Removing volume $GRAPH_REDIS_VOLUME..."
        container volume delete "$GRAPH_REDIS_VOLUME" || warning "Failed to remove volume $GRAPH_REDIS_VOLUME"
        success "Volume $GRAPH_REDIS_VOLUME removed"
    else
        log "Volume $GRAPH_REDIS_VOLUME not found, skipping removal"
    fi
}

# Clean up Docker Compose files
cleanup_compose_files() {
    log "Cleaning up Docker Compose references..."

    local compose_files=(
        "docker-compose.graph.yml"
        "docker-compose.graph.ci.yml"
    )

    for compose_file in "${compose_files[@]}"; do
        if [[ -f "$compose_file" ]]; then
            local backup_file="${compose_file}.decommissioned-$(date +%Y%m%d-%H%M%S)"
            log "Backing up $compose_file to $backup_file"
            cp "$compose_file" "$backup_file"

            warning "Consider removing or updating $compose_file"
            warning "Backup created at $backup_file"
        fi
    done
}

# Update Makefile
update_makefile() {
    log "Updating Makefile to remove graph database targets..."

    if [[ -f "Makefile" ]]; then
        local backup_file="Makefile.decommissioned-$(date +%Y%m%d-%H%M%S)"
        log "Backing up Makefile to $backup_file"
        cp "Makefile" "$backup_file"

        warning "Manual Makefile updates required:"
        warning "- Remove graph database targets (start-graph-infrastructure, etc.)"
        warning "- Update health checks to use single database"
        warning "- Remove graph-specific build targets"
        warning "Backup created at $backup_file"
    fi
}

# Verify decommission
verify_decommission() {
    log "Verifying decommission completion..."

    # Check containers are gone
    if check_container_status "$GRAPH_DB_CONTAINER"; then
        error "$GRAPH_DB_CONTAINER still exists after decommission"
    fi

    if check_container_status "$GRAPH_REDIS_CONTAINER"; then
        error "$GRAPH_REDIS_CONTAINER still exists after decommission"
    fi

    # Check volumes are gone
    if container volume list | grep -q "$GRAPH_DB_VOLUME"; then
        error "Volume $GRAPH_DB_VOLUME still exists after decommission"
    fi

    if container volume list | grep -q "$GRAPH_REDIS_VOLUME"; then
        error "Volume $GRAPH_REDIS_VOLUME still exists after decommission"
    fi

    success "Decommission verification completed"
}

# Provide rollback instructions
provide_rollback_instructions() {
    log ""
    log "🔄 ROLLBACK INSTRUCTIONS (if needed):"
    log ""
    log "If you need to restore the separate graph database:"
    log "1. Restore containers using: make start-graph-infrastructure"
    log "2. Restore data from backup files in: $BACKUP_DIR"
    log "3. Update configuration files to use separate database"
    log "4. Test functionality thoroughly"
    log ""
    warning "Rollback should only be done if consolidation fails"
}

# Main decommission function
main() {
    log "Starting graph database decommission process..."
    log "Log file: $LOG_FILE"

    # Safety checks
    confirm_decommission

    # Create final backup
    create_final_backup

    # Decommission process
    stop_containers
    remove_containers
    remove_volumes
    cleanup_compose_files
    update_makefile

    # Verification
    verify_decommission

    # Final instructions
    provide_rollback_instructions

    success "Graph database decommission completed successfully!"
    success ""
    success "✅ CONSOLIDATION COMPLETE:"
    success "- Separate graph database containers removed"
    success "- All graph functionality now in nv-db"
    success "- Single source of truth established"
    success "- Reduced operational complexity"
    success ""
    success "Next steps:"
    success "1. Update application configuration files"
    success "2. Test consolidated database functionality"
    success "3. Update documentation and deployment scripts"
    success "4. Run update-sync-to-internal-join.sh"

    log "Decommission completed at $(date)"
}

# Error handling
trap 'error "Decommission failed at line $LINENO"' ERR

# Run decommission
main "$@"
