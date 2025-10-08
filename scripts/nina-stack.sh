#!/usr/bin/env bash
set -euo pipefail

# Ninaivalaigal Stack Manager
# Manages all 9 combinations: 3 runtimes × 3 environments
#
# Usage:
#   ./scripts/nina-stack.sh start docker dev
#   ./scripts/nina-stack.sh stop colima stage
#   ./scripts/nina-stack.sh status apple prod
#   ./scripts/nina-stack.sh logs docker dev api
#   ./scripts/nina-stack.sh restart colima dev customer-app

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() { echo -e "${BLUE}ℹ${NC} $*"; }
log_success() { echo -e "${GREEN}✓${NC} $*"; }
log_warning() { echo -e "${YELLOW}⚠${NC} $*"; }
log_error() { echo -e "${RED}✗${NC} $*"; }

# Valid options
VALID_RUNTIMES=("docker" "colima" "apple")
VALID_ENVIRONMENTS=("dev" "stage" "prod")
VALID_COMMANDS=("start" "stop" "restart" "status" "logs" "ps" "exec" "down" "clean")

# Help function
show_help() {
    cat << EOF
Ninaivalaigal Stack Manager - Manage all 9 runtime × environment combinations

USAGE:
    $(basename "$0") <command> <runtime> <environment> [service] [options]

    start       Start the stack
    stop        Stop the stack (preserves data)
    restart     Restart the stack or specific service
    status      Show stack status
    logs        Show logs (optionally for specific service)
    ps          List running containers
    exec        Execute command in container
    down        Stop and remove containers (preserves volumes)
    clean       Stop, remove containers AND volumes (destructive!)

RUNTIMES:
    docker      Docker Desktop (ports: 5432, 6379, 8000, 3000, 3001)
    colima      Colima (ports: 5442, 6389, 8010, 3010, 3011)
    apple       Apple Container CLI (ports: 5452, 6399, 8020, 3020, 3021)

ENVIRONMENTS:
    dev         Development (debug enabled, live reload)
    stage       Staging (production-like, with debug)
    prod        Production (optimized, no debug)

SERVICES:
    postgres        Shared database (per environment)
    redis           Shared cache (per environment)
    api             API server (runtime-specific)
    customer-app    Customer-facing app (runtime-specific)
    admin-console   Internal admin console (runtime-specific)

EXAMPLES:
    # Start Docker dev stack
    $(basename "$0") start docker dev

    # Stop Colima staging
    $(basename "$0") stop colima stage

    # View Apple prod API logs
    $(basename "$0") logs apple prod api

    # Restart customer app in Docker dev
    $(basename "$0") restart docker dev customer-app

    # Check status of all services
    $(basename "$0") status docker dev

    # Execute command in API container
    $(basename "$0") exec docker dev api bash

    # Clean everything (WARNING: deletes data!)
    $(basename "$0") clean docker dev

NOTES:
    - Database and Redis are SHARED per environment across runtimes
    - API and frontend apps are runtime-specific for parallel development
    - Each runtime uses different ports to avoid conflicts
    - Use 'clean' with caution - it deletes all data!

EOF
}

# Validate inputs
validate_runtime() {
    local runtime=$1
    for valid in "${VALID_RUNTIMES[@]}"; do
        [[ "$runtime" == "$valid" ]] && return 0
    done
    log_error "Invalid runtime: $runtime"
    log_info "Valid runtimes: ${VALID_RUNTIMES[*]}"
    exit 1
}

validate_environment() {
    local env=$1
    for valid in "${VALID_ENVIRONMENTS[@]}"; do
        [[ "$env" == "$valid" ]] && return 0
    done
    log_error "Invalid environment: $env"
    log_info "Valid environments: ${VALID_ENVIRONMENTS[*]}"
    exit 1
}

validate_command() {
    local cmd=$1
    for valid in "${VALID_COMMANDS[@]}"; do
        [[ "$cmd" == "$valid" ]] && return 0
    done
    log_error "Invalid command: $cmd"
    log_info "Valid commands: ${VALID_COMMANDS[*]}"
    exit 1
}

# Get compose command based on runtime
get_compose_cmd() {
    local runtime=$1
    case "$runtime" in
        docker|colima)
            echo "docker-compose"
            ;;
        apple)
            echo "container compose"
            ;;
        *)
            log_error "Unknown runtime: $runtime"
            exit 1
            ;;
    esac
}

# Get compose file and env file
get_files() {
    local runtime=$1
    local env=$2

    local compose_file="$PROJECT_ROOT/compose.${runtime}.${env}.yml"
    local env_file="$PROJECT_ROOT/configs/.env.${runtime}.${env}"

    if [[ ! -f "$compose_file" ]]; then
        log_error "Compose file not found: $compose_file"
        log_info "Run: make generate-compose-files"
        exit 1
    fi

    if [[ ! -f "$env_file" ]]; then
        log_error "Environment file not found: $env_file"
        exit 1
    fi

    echo "$compose_file $env_file"
}

# Execute compose command
run_compose() {
    local runtime=$1
    local env=$2
    shift 2

    local compose_cmd
    compose_cmd=$(get_compose_cmd "$runtime")

    local files
    mapfile -t files < <(get_files "$runtime" "$env")
    local compose_file="${files[0]}"
    local env_file="${files[1]}"

    log_info "Using: $compose_file with $env_file"

    cd "$PROJECT_ROOT"
    $compose_cmd --env-file "$env_file" -f "$compose_file" "$@"
}

# Command implementations
cmd_start() {
    local runtime=$1
    local env=$2

    log_info "Starting Ninaivalaigal stack: $runtime / $env"
    log_info "Services: postgres, redis, api, customer-app, admin-console"

    run_compose "$runtime" "$env" up -d

    log_success "Stack started successfully!"
    log_info "Waiting for services to be healthy..."
    sleep 5

    cmd_status "$runtime" "$env"

    # Show access URLs
    local api_port redis_port customer_port admin_port
    case "$runtime" in
        docker)
            api_port=8000; customer_port=3000; admin_port=3001; redis_port=6379
            ;;
        colima)
            api_port=8010; customer_port=3010; admin_port=3011; redis_port=6389
            ;;
        apple)
            api_port=8020; customer_port=3020; admin_port=3021; redis_port=6399
            ;;
    esac

    echo ""
    log_success "Access URLs:"
    echo "  API:            http://localhost:$api_port"
    echo "  Customer App:   http://localhost:$customer_port"
    echo "  Admin Console:  http://localhost:$admin_port"
    echo "  API Health:     http://localhost:$api_port/health"
    echo "  API Docs:       http://localhost:$api_port/docs"
}

cmd_stop() {
    local runtime=$1
    local env=$2

    log_info "Stopping Ninaivalaigal stack: $runtime / $env"
    run_compose "$runtime" "$env" stop
    log_success "Stack stopped (data preserved)"
}

cmd_restart() {
    local runtime=$1
    local env=$2
    local service=${3:-}

    if [[ -n "$service" ]]; then
        log_info "Restarting service: $service"
        run_compose "$runtime" "$env" restart "$service"
    else
        log_info "Restarting entire stack: $runtime / $env"
        run_compose "$runtime" "$env" restart
    fi

    log_success "Restart complete"
}

cmd_status() {
    local runtime=$1
    local env=$2

    log_info "Stack status: $runtime / $env"
    run_compose "$runtime" "$env" ps
}

cmd_logs() {
    local runtime=$1
    local env=$2
    local service=${3:-}

    if [[ -n "$service" ]]; then
        log_info "Showing logs for: $service"
        run_compose "$runtime" "$env" logs -f --tail=100 "$service"
    else
        log_info "Showing logs for all services"
        run_compose "$runtime" "$env" logs -f --tail=50
    fi
}

cmd_ps() {
    local runtime=$1
    local env=$2

    run_compose "$runtime" "$env" ps -a
}

cmd_exec() {
    local runtime=$1
    local env=$2
    local service=${3:-}
    shift 3 || true

    if [[ -z "$service" ]]; then
        log_error "Service name required for exec command"
        log_info "Example: $(basename "$0") exec docker dev api bash"
        exit 1
    fi

    run_compose "$runtime" "$env" exec "$service" "$@"
}

cmd_down() {
    local runtime=$1
    local env=$2

    log_warning "Stopping and removing containers (volumes preserved)"
    read -p "Continue? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "Cancelled"
        exit 0
    fi

    run_compose "$runtime" "$env" down
    log_success "Containers removed (data preserved in volumes)"
}

cmd_clean() {
    local runtime=$1
    local env=$2

    log_error "WARNING: This will DELETE ALL DATA including databases!"
    log_warning "This affects: ninaivalaigal_${env}_* volumes"
    read -p "Are you ABSOLUTELY SURE? Type 'yes' to confirm: " -r
    echo
    if [[ "$REPLY" != "yes" ]]; then
        log_info "Cancelled"
        exit 0
    fi

    run_compose "$runtime" "$env" down -v
    log_success "Stack cleaned (all data deleted)"
}

# Main
main() {
    if [[ $# -lt 1 ]]; then
        show_help
        exit 1
    fi

    local command=$1

    if [[ "$command" == "help" ]] || [[ "$command" == "-h" ]] || [[ "$command" == "--help" ]]; then
        show_help
        exit 0
    fi

    if [[ $# -lt 3 ]]; then
        log_error "Missing required arguments"
        show_help
        exit 1
    fi

    local runtime=$2
    local env=$3
    shift 3 || true

    validate_command "$command"
    validate_runtime "$runtime"
    validate_environment "$env"

    case "$command" in
        start)
            cmd_start "$runtime" "$env"
            ;;
        stop)
            cmd_stop "$runtime" "$env"
            ;;
        restart)
            cmd_restart "$runtime" "$env" "$@"
            ;;
        status)
            cmd_status "$runtime" "$env"
            ;;
        logs)
            cmd_logs "$runtime" "$env" "$@"
            ;;
        ps)
            cmd_ps "$runtime" "$env"
            ;;
        exec)
            cmd_exec "$runtime" "$env" "$@"
            ;;
        down)
            cmd_down "$runtime" "$env"
            ;;
        clean)
            cmd_clean "$runtime" "$env"
            ;;
        *)
            log_error "Unknown command: $command"
            show_help
            exit 1
            ;;
    esac
}

main "$@"
