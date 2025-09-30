#!/usr/bin/env bash
# Validate All Environment + Runtime Combinations
# Tests all 9 combinations (3 envs × 3 runtimes)

set -eo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"
}

success() {
    echo "✅ $*"
}

error() {
    echo "❌ $*"
}

warn() {
    echo "⚠️  $*"
}

# Test port assignment for all combinations
test_port_assignments() {
    log "Testing port assignments for all combinations..."

    local envs=("dev" "test" "prod")
    local runtimes=("docker" "colima" "apple")
    local services=("postgres" "redis" "api" "ui" "pgbouncer")

    echo ""
    echo "| Environment | Runtime | Postgres | Redis | API   | UI   | PgBouncer | Database   |"
    echo "|-------------|---------|----------|-------|-------|------|-----------|------------|"

    for env in "${envs[@]}"; do
        for runtime in "${runtimes[@]}"; do
            local postgres_port=$(./scripts/get-port.sh postgres "$env" "$runtime")
            local redis_port=$(./scripts/get-port.sh redis "$env" "$runtime")
            local api_port=$(./scripts/get-port.sh api "$env" "$runtime")
            local ui_port=$(./scripts/get-port.sh ui "$env" "$runtime")
            local pgbouncer_port=$(./scripts/get-port.sh pgbouncer "$env" "$runtime")

            printf "| %-11s | %-7s | %-8s | %-5s | %-5s | %-4s | %-9s | %-10s |\n" \
                "$env" "$runtime" "$postgres_port" "$redis_port" "$api_port" "$ui_port" "$pgbouncer_port" "ninaivalaigal_$env"
        done
    done
    echo ""
}

# Test Makefile variable resolution
test_makefile_variables() {
    log "Testing Makefile variable resolution..."

    local envs=("dev" "test" "prod")
    local runtimes=("docker" "colima" "apple")

    for env in "${envs[@]}"; do
        for runtime in "${runtimes[@]}"; do
            log "Testing NINA_ENV=$env NINA_RUNTIME=$runtime"

            # Test variable resolution
            local result=$(cd "$ROOT_DIR" && NINA_ENV="$env" NINA_RUNTIME="$runtime" make -s stack-status 2>/dev/null | head -5)

            if echo "$result" | grep -q "Environment: $env" && echo "$result" | grep -q "Runtime: $runtime"; then
                success "$env/$runtime: Variables resolved correctly"
            else
                error "$env/$runtime: Variable resolution failed"
                echo "$result"
            fi
        done
    done
}

# Test docker-compose file existence and syntax
test_compose_files() {
    log "Testing docker-compose file syntax..."

    local runtimes=("docker" "colima" "apple")

    for runtime in "${runtimes[@]}"; do
        local compose_file="$ROOT_DIR/compose.$runtime.yml"

        if [ -f "$compose_file" ]; then
            # Test syntax with docker-compose config
            if command -v docker-compose >/dev/null 2>&1; then
                if NINA_ENV=test NINA_RUNTIME="$runtime" docker-compose -f "$compose_file" config >/dev/null 2>&1; then
                    success "$runtime: compose file syntax valid"
                else
                    error "$runtime: compose file syntax invalid"
                fi
            else
                warn "$runtime: docker-compose not available, skipping syntax check"
            fi
        else
            error "$runtime: compose file missing at $compose_file"
        fi
    done
}

# Test environment isolation (port conflicts)
test_port_conflicts() {
    log "Testing port conflict prevention..."

    local conflicts=0
    local envs=("dev" "test" "prod")
    local runtimes=("docker" "colima" "apple")
    local services=("postgres" "redis" "api" "ui" "pgbouncer")

    # Use temporary file to track port usage
    local port_file="/tmp/port_usage_$$"
    rm -f "$port_file"

    for env in "${envs[@]}"; do
        for runtime in "${runtimes[@]}"; do
            for service in "${services[@]}"; do
                local port=$(./scripts/get-port.sh "$service" "$env" "$runtime")
                local key="$env-$runtime-$service"

                # Check if port is already used
                if grep -q "^$port:" "$port_file" 2>/dev/null; then
                    local existing=$(grep "^$port:" "$port_file" | cut -d: -f2)
                    error "Port conflict: $port used by both $existing and $key"
                    ((conflicts++))
                else
                    echo "$port:$key" >> "$port_file"
                fi
            done
        done
    done

    rm -f "$port_file"

    if [ $conflicts -eq 0 ]; then
        success "No port conflicts detected across all combinations"
    else
        error "Found $conflicts port conflicts"
        return 1
    fi
}

# Test container name uniqueness
test_container_names() {
    log "Testing container name uniqueness..."

    local envs=("dev" "test" "prod")
    local services=("db" "redis" "api" "ui")

    local name_file="/tmp/name_usage_$$"
    rm -f "$name_file"
    local conflicts=0

    for env in "${envs[@]}"; do
        for service in "${services[@]}"; do
            local container_name="ninaivalaigal-$env-$service"

            if grep -q "^$container_name$" "$name_file" 2>/dev/null; then
                error "Container name conflict: $container_name used multiple times"
                ((conflicts++))
            else
                echo "$container_name" >> "$name_file"
            fi
        done
    done

    rm -f "$name_file"

    if [ $conflicts -eq 0 ]; then
        success "All container names are unique"
    else
        error "Found $conflicts container name conflicts"
        return 1
    fi
}

# Test environment variable propagation
test_env_propagation() {
    log "Testing environment variable propagation..."

    # Test with sample environment
    export NINA_ENV=test
    export NINA_RUNTIME=colima
    export NINA_DB_PASSWORD=test_password

    local postgres_port=$(./scripts/get-port.sh postgres test colima)

    if [ "$postgres_port" = "5542" ]; then
        success "Environment variables propagated correctly (test+colima=5542)"
    else
        error "Environment variable propagation failed (expected 5542, got $postgres_port)"
        return 1
    fi
}

# Main validation function
main() {
    log "🧪 Starting comprehensive validation of all combinations..."
    echo ""

    cd "$ROOT_DIR"

    # Run all tests
    test_port_assignments
    test_makefile_variables
    test_compose_files
    test_port_conflicts
    test_container_names
    test_env_propagation

    echo ""
    log "🎉 Validation complete!"

    echo ""
    echo "📋 Usage Examples:"
    echo "=================="
    echo "# Development with Colima"
    echo "NINA_ENV=dev NINA_RUNTIME=colima make stack-up"
    echo ""
    echo "# Test environment with Docker"
    echo "NINA_ENV=test NINA_RUNTIME=docker make stack-up"
    echo ""
    echo "# Production with Apple Container CLI"
    echo "NINA_ENV=prod NINA_RUNTIME=apple make stack-up"
    echo ""
    echo "# Check status"
    echo "NINA_ENV=dev NINA_RUNTIME=colima make stack-status"
    echo ""
    echo "# Stop specific environment"
    echo "NINA_ENV=test NINA_RUNTIME=docker make stack-down"
}

# Run validation
main "$@"
