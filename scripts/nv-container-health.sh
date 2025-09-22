#!/bin/bash
# Container Health Monitoring and Auto-Recovery for ninaivalaigal stack
# Addresses frequent container shutdowns by monitoring and auto-restarting

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

log() { printf "\033[1;36m[health]\033[0m %s\n" "$*"; }
warn() { printf "\033[1;33m[warn]\033[0m %s\n" "$*"; }
error() { printf "\033[1;31m[error]\033[0m %s\n" "$*"; }
success() { printf "\033[1;32m[ok]\033[0m %s\n" "$*"; }

# Container definitions with health checks
get_container_health_url() {
    local container_name="$1"
    local ip="$2"
    
    case "$container_name" in
        "nv-db")
            echo "postgresql://nina:change_me_securely@${ip}:5432/nina"
            ;;
        "nv-pgbouncer")
            echo "postgresql://nina:change_me_securely@${ip}:6432/nina"
            ;;
        "nv-redis")
            echo "redis://${ip}:6379"
            ;;
        "nv-api")
            echo "http://${ip}:8000/health"
            ;;
        *)
            echo ""
            ;;
    esac
}

# List of containers to monitor
CONTAINER_LIST="nv-db nv-pgbouncer nv-redis nv-api"

# Detect container command (Apple Container CLI or Docker)
detect_container_cmd() {
    if command -v container >/dev/null 2>&1; then
        echo "container"
    elif command -v docker >/dev/null 2>&1; then
        echo "docker"
    else
        return 1
    fi
}

# Check if container exists and is running
check_container_status() {
    local container_name="$1"
    local status
    local container_cmd
    
    container_cmd=$(detect_container_cmd) || {
        echo "no_container_runtime"
        return
    }
    
    if [[ "$container_cmd" == "container" ]]; then
        if ! container list | grep -q "^${container_name}"; then
            echo "missing"
            return
        fi
        status=$(container list | grep "^${container_name}" | awk '{print $5}' || echo "unknown")
    else
        # Docker
        if ! docker ps -a --format "table {{.Names}}\t{{.Status}}" | grep -q "^${container_name}"; then
            echo "missing"
            return
        fi
        if docker ps --format "table {{.Names}}\t{{.Status}}" | grep -q "^${container_name}.*Up"; then
            status="running"
        else
            status="stopped"
        fi
    fi
    
    echo "$status"
}

# Get container IP address
get_container_ip() {
    local container_name="$1"
    local ip
    local container_cmd
    
    container_cmd=$(detect_container_cmd) || return 1
    
    if [[ "$container_cmd" == "container" ]]; then
        ip=$(container inspect "$container_name" 2>/dev/null | jq -r '.[0].networks[0].address' 2>/dev/null | cut -d'/' -f1 || echo "")
    else
        # Docker
        ip=$(docker inspect "$container_name" 2>/dev/null | jq -r '.[0].NetworkSettings.IPAddress' 2>/dev/null || echo "")
    fi
    
    if [[ -z "$ip" || "$ip" == "null" ]]; then
        echo ""
        return 1
    fi
    
    echo "$ip"
}

# Health check specific container
health_check_container() {
    local container_name="$1"
    local container_ip
    local health_url
    
    container_ip=$(get_container_ip "$container_name")
    if [[ -z "$container_ip" ]]; then
        return 1
    fi
    
    health_url=$(get_container_health_url "$container_name" "$container_ip")
    
    case "$container_name" in
        "nv-db"|"nv-pgbouncer")
            # PostgreSQL health check
            if command -v psql >/dev/null 2>&1; then
                psql "$health_url" -c "SELECT 1;" >/dev/null 2>&1
            else
                # Fallback: check if port is open
                nc -z "$container_ip" "${health_url##*:}" 2>/dev/null
            fi
            ;;
        "nv-redis")
            # Redis health check
            if command -v redis-cli >/dev/null 2>&1; then
                redis-cli -h "$container_ip" -p 6379 -a "nina_redis_dev_password" ping >/dev/null 2>&1
            else
                # Fallback: check if port is open
                nc -z "$container_ip" 6379 2>/dev/null
            fi
            ;;
        "nv-api")
            # HTTP health check
            curl -fsS "$health_url" >/dev/null 2>&1
            ;;
        *)
            return 1
            ;;
    esac
}

# Get container resource usage
get_container_resources() {
    local container_name="$1"
    local stats
    
    # Get basic container stats (if available)
    if container stats --no-stream "$container_name" >/dev/null 2>&1; then
        stats=$(container stats --no-stream "$container_name" 2>/dev/null | tail -n 1)
        echo "$stats"
    else
        echo "stats unavailable"
    fi
}

# Check container logs for errors
check_container_logs() {
    local container_name="$1"
    local error_count
    
    # Check last 50 lines for common error patterns
    local container_cmd
    container_cmd=$(detect_container_cmd) || {
        echo "0"
        return
    }
    
    error_count=$($container_cmd logs --tail 50 "$container_name" 2>/dev/null | \
        grep -iE "(error|fatal|panic|exception|failed|crash)" | wc -l | xargs || echo "0")
    
    echo "$error_count"
}

# Restart container if needed
restart_container() {
    local container_name="$1"
    
    warn "Restarting unhealthy container: $container_name"
    
    case "$container_name" in
        "nv-db")
            bash "${SCRIPT_DIR}/nv-db-start.sh"
            ;;
        "nv-pgbouncer")
            bash "${SCRIPT_DIR}/nv-pgbouncer-start.sh"
            ;;
        "nv-redis")
            container stop "$container_name" >/dev/null 2>&1 || true
            container delete "$container_name" >/dev/null 2>&1 || true
            container run -d --name nv-redis -p 6379:6379 \
                -e REDIS_PASSWORD=nina_redis_dev_password \
                -v nv_redis_data:/data \
                redis:7-alpine redis-server --requirepass nina_redis_dev_password --maxmemory 256mb --maxmemory-policy allkeys-lru
            ;;
        "nv-api")
            bash "${SCRIPT_DIR}/nv-api-start.sh"
            ;;
    esac
}

# Main health monitoring function
monitor_containers() {
    local auto_restart="${1:-false}"
    local unhealthy_containers=()
    
    log "Checking container health..."
    
    for container_name in $CONTAINER_LIST; do
        local status error_count resources
        
        status=$(check_container_status "$container_name")
        
        case "$status" in
            "running")
                if health_check_container "$container_name"; then
                    success "$container_name: healthy"
                else
                    error "$container_name: unhealthy (health check failed)"
                    unhealthy_containers+=("$container_name")
                fi
                
                # Check for excessive errors in logs
                error_count=$(check_container_logs "$container_name")
                if [[ -n "$error_count" && "$error_count" =~ ^[0-9]+$ && "$error_count" -gt 10 ]]; then
                    warn "$container_name: $error_count errors in recent logs"
                fi
                
                # Show resource usage if available
                resources=$(get_container_resources "$container_name")
                if [[ "$resources" != "stats unavailable" ]]; then
                    log "$container_name resources: $resources"
                fi
                ;;
            "stopped")
                error "$container_name: stopped"
                unhealthy_containers+=("$container_name")
                ;;
            "missing")
                error "$container_name: missing"
                unhealthy_containers+=("$container_name")
                ;;
            *)
                warn "$container_name: unknown status ($status)"
                ;;
        esac
    done
    
    # Auto-restart if requested and containers are unhealthy
    if [[ "$auto_restart" == "true" && ${#unhealthy_containers[@]} -gt 0 ]]; then
        log "Auto-restarting ${#unhealthy_containers[@]} unhealthy containers..."
        
        for container_name in "${unhealthy_containers[@]}"; do
            restart_container "$container_name"
            sleep 5  # Give container time to start
        done
        
        # Re-check after restart
        log "Re-checking health after restart..."
        sleep 10
        monitor_containers false
    fi
    
    return ${#unhealthy_containers[@]}
}

# Continuous monitoring mode
continuous_monitor() {
    local interval="${1:-30}"
    local auto_restart="${2:-true}"
    
    log "Starting continuous monitoring (interval: ${interval}s, auto-restart: $auto_restart)"
    
    while true; do
        monitor_containers "$auto_restart"
        sleep "$interval"
    done
}

# Main script logic
main() {
    case "${1:-check}" in
        "check")
            monitor_containers false
            ;;
        "auto-restart")
            monitor_containers true
            ;;
        "continuous")
            continuous_monitor "${2:-30}" "${3:-true}"
            ;;
        "help"|"-h"|"--help")
            echo "Usage: $0 [check|auto-restart|continuous [interval] [auto_restart]]"
            echo ""
            echo "Commands:"
            echo "  check        - Check container health (default)"
            echo "  auto-restart - Check and restart unhealthy containers"
            echo "  continuous   - Continuous monitoring with optional auto-restart"
            echo ""
            echo "Examples:"
            echo "  $0                           # Basic health check"
            echo "  $0 auto-restart             # Check and restart if needed"
            echo "  $0 continuous 60 true       # Monitor every 60s with auto-restart"
            echo "  $0 continuous 30 false      # Monitor every 30s without auto-restart"
            ;;
        *)
            error "Unknown command: $1"
            echo "Use '$0 help' for usage information"
            exit 1
            ;;
    esac
}

# Ensure we have required tools
command -v container >/dev/null 2>&1 || { error "container CLI not found"; exit 1; }
command -v jq >/dev/null 2>&1 || { error "jq not found"; exit 1; }

main "$@"
