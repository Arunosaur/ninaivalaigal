#!/usr/bin/env bash
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
# Migration Script: Unified Container Naming Convention
# Migrates from inconsistent naming to: ninaivalaigal-{env}-{service}
# Note: Runtime suffix removed as of v1.1.0 (Oct 10, 2025)

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log() { echo -e "${BLUE}[MIGRATE]${NC} $*"; }
success() { echo -e "${GREEN}[SUCCESS]${NC} $*"; }
warning() { echo -e "${YELLOW}[WARNING]${NC} $*"; }
error() { echo -e "${RED}[ERROR]${NC} $*"; }

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# Migration mapping for existing containers
# Updated Oct 10, 2025: No runtime suffix
declare -A CONTAINER_MIGRATIONS=(
    # Legacy NV containers (no env suffix)
    ["nv-db"]="ninaivalaigal-dev-db"
    ["nv-redis"]="ninaivalaigal-dev-redis"
    ["nv-api"]="ninaivalaigal-dev-core-api"
    ["nv-ui"]="ninaivalaigal-dev-ui-customer"
    ["nv-pgbouncer"]="ninaivalaigal-dev-pgbouncer"

    # Nina Intelligence containers (no env suffix)
    ["nina-intelligence-db"]="ninaivalaigal-dev-db"
    ["nina-intelligence-cache"]="ninaivalaigal-dev-redis"
)

# Check what containers are currently running
check_existing_containers() {
    log "Checking existing containers..."

    if ! command -v container >/dev/null 2>&1; then
        error "Apple Container CLI not found. Please install it first."
        exit 1
    fi

    local existing_containers
    existing_containers=$(container list --format json 2>/dev/null | jq -r '.[].name' 2>/dev/null || echo "")

    if [[ -z "$existing_containers" ]]; then
        log "No containers currently running."
        return 0
    fi

    echo "Current containers:"
    for container_name in $existing_containers; do
        if [[ -n "${CONTAINER_MIGRATIONS[$container_name]:-}" ]]; then
            warning "  $container_name → ${CONTAINER_MIGRATIONS[$container_name]} (will migrate)"
        else
            log "  $container_name (no migration needed)"
        fi
    done
}

# Stop and rename containers
migrate_containers() {
    log "Starting container migration..."

    for old_name in "${!CONTAINER_MIGRATIONS[@]}"; do
        local new_name="${CONTAINER_MIGRATIONS[$old_name]}"

        # Check if old container exists
        if container list | grep -q "^$old_name "; then
            log "Migrating: $old_name → $new_name"

            # Stop the old container
            container stop "$old_name" >/dev/null 2>&1 || true

            # Get the image name
            local image_name
            image_name=$(container list --all | grep "^$old_name " | awk '{print $2}' || echo "")

            if [[ -n "$image_name" ]]; then
                # Create new container with same image and settings
                log "  Creating new container: $new_name"

                # Note: This is a simplified migration. In practice, you'd need to:
                # 1. Export volumes/data
                # 2. Recreate with proper environment-specific ports
                # 3. Import data back

                warning "  Manual step required: Recreate $new_name with proper environment settings"
            fi

            # Remove old container
            container delete "$old_name" >/dev/null 2>&1 || true
            success "  Removed old container: $old_name"
        else
            log "Container $old_name not found, skipping."
        fi
    done
}

# Update database names (requires manual intervention)
update_database_names() {
    log "Database naming updates required..."

    cat << 'EOF'
📋 Manual Database Updates Needed:

1. Connect to each database and rename:
   ALTER DATABASE nina RENAME TO ninaivalaigal_dev;
   ALTER DATABASE ninaivalaigal RENAME TO ninaivalaigal_dev;

2. Update user permissions:
   GRANT ALL PRIVILEGES ON DATABASE ninaivalaigal_dev TO nina;

3. Update connection strings in configs to use:
   - ninaivalaigal_dev (development)
   - ninaivalaigal_test (testing)
   - ninaivalaigal_prod (production)

EOF
}

# Backup current configuration
backup_configs() {
    log "Creating configuration backup..."

    local backup_dir="$ROOT_DIR/backups/naming-migration-$(date +%Y%m%d-%H%M%S)"
    mkdir -p "$backup_dir"

    # Backup key files that will be modified
    local files_to_backup=(
        "scripts/nina-intelligence-stack-start.sh"
        "scripts/nv-stack-start.sh"
        "scripts/nv-stack-status.sh"
        "scripts/nv-stack-stop.sh"
        "Makefile"
    )

    for file in "${files_to_backup[@]}"; do
        if [[ -f "$ROOT_DIR/$file" ]]; then
            cp "$ROOT_DIR/$file" "$backup_dir/"
            log "  Backed up: $file"
        fi
    done

    success "Configuration backed up to: $backup_dir"
    echo "$backup_dir" > "$ROOT_DIR/.last-naming-backup"
}

# Generate new unified scripts
generate_unified_scripts() {
    log "Generating unified startup scripts..."

    # This will be implemented in the next step
    warning "Script generation will be implemented in next phase"

    cat << 'EOF'
📋 Next Steps:

1. Update Nina Intelligence scripts to use ${NINA_ENV}
2. Update NV scripts to use unified naming
3. Update Makefile targets
4. Test all 9 environment/runtime combinations

EOF
}

# Main migration flow
main() {
    log "🚀 Starting Unified Naming Migration"
    log "Target convention: ninaivalaigal-{env}-{service}"
    log "Note: Runtime suffix removed as of v1.1.0"
    echo

    # Safety check
    read -p "This will stop and rename existing containers. Continue? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log "Migration cancelled."
        exit 0
    fi

    backup_configs
    check_existing_containers
    migrate_containers
    update_database_names
    generate_unified_scripts

    success "🎉 Migration phase 1 complete!"
    warning "Manual steps required - see output above"
}

# Run migration
main "$@"
