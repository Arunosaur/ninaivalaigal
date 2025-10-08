#!/usr/bin/env bash
# Runtime-Aware Health Check
# Only monitors containers for the active runtime specified in .runtime-config

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
CONFIG_FILE="$PROJECT_ROOT/.runtime-config"

log() { printf "\033[1;32m[health]\033[0m %s\n" "$*"; }
warn() { printf "\033[1;33m[warn]\033[0m %s\n" "$*"; }
die() { printf "\033[1;31m[fail]\033[0m %s\n" "$*"; exit 1; }

# Load runtime configuration
if [ ! -f "$CONFIG_FILE" ]; then
    warn "No .runtime-config found, defaulting to docker"
    ACTIVE_RUNTIME="docker"
    HEALTH_MONITORING_ENABLED="true"
    AUTO_RESTART_ENABLED="false"
else
    source "$CONFIG_FILE"
fi

log "Active Runtime: $ACTIVE_RUNTIME"
log "Health Monitoring: $HEALTH_MONITORING_ENABLED"
log "Auto-Restart: $AUTO_RESTART_ENABLED"

# Exit if health monitoring is disabled
if [ "$HEALTH_MONITORING_ENABLED" != "true" ]; then
    log "Health monitoring disabled, exiting"
    exit 0
fi

# Detect which container command to use based on active runtime
case "$ACTIVE_RUNTIME" in
    docker)
        CONTAINER_CMD="docker"
        CONTAINER_LIST_CMD="docker ps --filter name=ninaivalaigal"
        ;;
    colima)
        CONTAINER_CMD="docker"  # Colima uses docker command
        CONTAINER_LIST_CMD="docker ps --filter name=ninaivalaigal"
        ;;
    apple)
        CONTAINER_CMD="container"
        CONTAINER_LIST_CMD="container list | grep -E 'nv-db|nv-api|nv-redis|nv-pgbouncer'"
        ;;
    *)
        die "Unknown runtime: $ACTIVE_RUNTIME. Valid: docker, colima, apple"
        ;;
esac

# Check if runtime is available
if ! command -v "$CONTAINER_CMD" >/dev/null 2>&1; then
    die "Runtime command '$CONTAINER_CMD' not found for $ACTIVE_RUNTIME runtime"
fi

log "Checking containers for $ACTIVE_RUNTIME runtime..."

# Get running containers
if [ "$ACTIVE_RUNTIME" = "apple" ]; then
    RUNNING_CONTAINERS=$(container list 2>/dev/null | grep -E 'ninaivalaigal-dev' | wc -l || echo "0")
else
    RUNNING_CONTAINERS=$(docker ps --filter name=ninaivalaigal --format '{{.Names}}' | wc -l)
fi

log "Found $RUNNING_CONTAINERS running containers"

# Check container health based on runtime
check_container_health() {
    local container_name=$1

    if [ "$ACTIVE_RUNTIME" = "apple" ]; then
        # Apple Container CLI health check
        container list | grep -q "$container_name" && echo "healthy" || echo "unhealthy"
    else
        # Docker/Colima health check
        docker inspect --format='{{.State.Health.Status}}' "$container_name" 2>/dev/null || echo "unknown"
    fi
}

# Restart container if auto-restart is enabled
restart_container() {
    local container_name=$1

    if [ "$AUTO_RESTART_ENABLED" != "true" ]; then
        warn "Auto-restart disabled, skipping restart of $container_name"
        return
    fi

    warn "Restarting unhealthy container: $container_name"

    if [ "$ACTIVE_RUNTIME" = "apple" ]; then
        container stop "$container_name" && container start "$container_name"
    else
        docker restart "$container_name"
    fi
}

# Main health check loop
if [ "$RUNNING_CONTAINERS" -eq 0 ]; then
    warn "No containers running for $ACTIVE_RUNTIME runtime"
    exit 0
fi

# List and check each container
if [ "$ACTIVE_RUNTIME" = "apple" ]; then
    CONTAINERS=$(container list | grep -E 'ninaivalaigal-dev' | awk '{print $1}')
else
    CONTAINERS=$(docker ps --filter name=ninaivalaigal --format '{{.Names}}')
fi

for container in $CONTAINERS; do
    health=$(check_container_health "$container")

    if [ "$health" = "unhealthy" ]; then
        warn "Container $container is unhealthy"
        restart_container "$container"
    else
        log "Container $container is $health"
    fi
done

log "Health check complete"
