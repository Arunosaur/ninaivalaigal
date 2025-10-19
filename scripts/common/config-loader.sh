#!/usr/bin/env bash
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
# Unified Configuration Loader - The Right Way™
# Loads config in proper hierarchy: defaults → runtime → env → secrets
# Version: 1.0.0 - Day 4 Uniform Architecture

# Get root directory
SCRIPT_DIR_CONFIG="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR_CONFIG="$(cd "$SCRIPT_DIR_CONFIG/../.." && pwd)"

# Colors for logging
readonly GREEN='\033[0;32m'
readonly BLUE='\033[0;34m'
readonly YELLOW='\033[1;33m'
readonly RED='\033[0;31m'
readonly NC='\033[0m'

log_config() {
    echo -e "${BLUE}[CONFIG]${NC} $*"
}

log_config_success() {
    echo -e "${GREEN}[CONFIG]${NC} ✅ $*"
}

log_config_error() {
    echo -e "${RED}[CONFIG]${NC} ❌ $*"
}

log_config_warning() {
    echo -e "${YELLOW}[CONFIG]${NC} ⚠️  $*"
}

# Main configuration loader
load_config() {
    local runtime=${1:-apple}
    local env=${2:-dev}

    log_config "Loading configuration for runtime=$runtime, env=$env"

    # 1. Load defaults (required)
    local defaults_file="${ROOT_DIR_CONFIG}/configs/defaults.env"
    if [ ! -f "$defaults_file" ]; then
        log_config_error "Defaults file not found: $defaults_file"
        return 1
    fi
    # shellcheck source=/dev/null
    source "$defaults_file"
    log_config_success "Loaded defaults"

    # 2. Load runtime config (required)
    local runtime_file="${ROOT_DIR_CONFIG}/configs/runtime-${runtime}.env"
    if [ ! -f "$runtime_file" ]; then
        log_config_error "Runtime config not found: $runtime_file"
        log_config "Available runtimes: docker, colima, apple"
        return 1
    fi
    # shellcheck source=/dev/null
    source "$runtime_file"
    log_config_success "Loaded runtime: $runtime"

    # 3. Load environment config (required)
    local env_file="${ROOT_DIR_CONFIG}/configs/env-${env}.env"
    if [ ! -f "$env_file" ]; then
        log_config_error "Environment config not found: $env_file"
        log_config "Available environments: dev, test, prod"
        return 1
    fi
    # shellcheck source=/dev/null
    source "$env_file"
    log_config_success "Loaded environment: $env"

    # 4. Load secrets (required for non-dev)
    local secrets_file="${ROOT_DIR_CONFIG}/configs/secrets-${runtime}-${env}.env"
    if [ -f "$secrets_file" ]; then
        # shellcheck source=/dev/null
        source "$secrets_file"
        log_config_success "Loaded secrets from: secrets-${runtime}-${env}.env"
    else
        if [ "$env" != "dev" ]; then
            log_config_error "Secrets file required for ${env}: ${secrets_file}"
            log_config "Copy configs/secrets.env.template to ${secrets_file} and fill in values"
            return 1
        fi
        # Dev fallback to safe defaults
        log_config_warning "No secrets file found, using dev defaults"
        export NINA_DB_PASSWORD="${NINA_DB_PASSWORD:-dev_password_change_in_production}"
        export NINA_REDIS_PASSWORD="${NINA_REDIS_PASSWORD:-dev_redis_password}"
        export NINA_JWT_SECRET="${NINA_JWT_SECRET:-dev_jwt_secret_change_in_production}"
    fi

    # 5. Calculate ports using SPEC-086 formula
    calculate_ports

    # 6. Set derived configuration
    set_derived_config

    # 7. Validate configuration
    validate_config

    # 8. Display configuration summary
    show_config_summary

    return 0
}

# Calculate all ports using SPEC-086 formula
calculate_ports() {
    log_config "Calculating ports (SPEC-086 formula)..."

    # Final Port = Base Port + Environment Offset + Runtime Offset
    export DB_PORT=$((BASE_DB_PORT + ENV_OFFSET + RUNTIME_OFFSET))
    export PGBOUNCER_PORT=$((BASE_PGBOUNCER_PORT + ENV_OFFSET + RUNTIME_OFFSET))
    export REDIS_PORT=$((BASE_REDIS_PORT + ENV_OFFSET + RUNTIME_OFFSET))
    export API_PORT=$((BASE_API_PORT + ENV_OFFSET + RUNTIME_OFFSET))
    export CUSTOMER_UI_PORT=$((BASE_CUSTOMER_UI_PORT + ENV_OFFSET + RUNTIME_OFFSET))
    export ADMIN_UI_PORT=$((BASE_ADMIN_UI_PORT + ENV_OFFSET + RUNTIME_OFFSET))

    log_config "Ports calculated: DB=$DB_PORT, PgBouncer=$PGBOUNCER_PORT, Redis=$REDIS_PORT, API=$API_PORT"
}

# Set derived configuration values
set_derived_config() {
    # Container names (SPEC-086)
    export DB_CONTAINER="${CONTAINER_PREFIX}-${NINA_ENV}-db"
    export PGBOUNCER_CONTAINER="${CONTAINER_PREFIX}-${NINA_ENV}-pgbouncer"
    export REDIS_CONTAINER="${CONTAINER_PREFIX}-${NINA_ENV}-redis"
    export API_CONTAINER="${CONTAINER_PREFIX}-${NINA_ENV}-core-api"
    export MEMORY_SERVICE_CONTAINER="${CONTAINER_PREFIX}-${NINA_ENV}-memory-service"
    export GRPC_GATEWAY_CONTAINER="${CONTAINER_PREFIX}-${NINA_ENV}-grpc-gateway"
    export GRAPH_SERVICE_CONTAINER="${CONTAINER_PREFIX}-${NINA_ENV}-graph-service"
    export ADMIN_VENDOR_CONTAINER="${CONTAINER_PREFIX}-${NINA_ENV}-admin-vendor"
    export BUSINESS_SERVICE_CONTAINER="${CONTAINER_PREFIX}-${NINA_ENV}-business-service"
    export CUSTOMER_APP_CONTAINER="${CONTAINER_PREFIX}-${NINA_ENV}-customer-app"
    export ADMIN_CONSOLE_CONTAINER="${CONTAINER_PREFIX}-${NINA_ENV}-admin-console"

    # Database configuration
    export DB_NAME="${DB_NAME_PREFIX}_${NINA_ENV}"
    export DB_USER="${DB_USER:-nina}"

    # Volume names
    export DB_VOLUME="${CONTAINER_PREFIX}_${NINA_ENV}_db_data"
    export REDIS_VOLUME="${CONTAINER_PREFIX}_${NINA_ENV}_redis_data"
}

# Validate all required configuration
validate_config() {
    log_config "Validating configuration..."

    local required_vars=(
        "NINA_RUNTIME"
        "NINA_ENV"
        "CONTAINER_COMMAND"
        "DB_PORT"
        "PGBOUNCER_PORT"
        "REDIS_PORT"
        "API_PORT"
        "NINA_DB_PASSWORD"
        "NINA_REDIS_PASSWORD"
        "NINA_JWT_SECRET"
        "DB_CONTAINER"
        "PGBOUNCER_CONTAINER"
        "REDIS_CONTAINER"
    )

    local missing_vars=()
    for var in "${required_vars[@]}"; do
        if [ -z "${!var}" ]; then
            missing_vars+=("$var")
        fi
    done

    if [ ${#missing_vars[@]} -gt 0 ]; then
        log_config_error "Missing required configuration variables:"
        for var in "${missing_vars[@]}"; do
            echo "  - $var"
        done
        return 1
    fi

    # Validate container command exists
    if ! command -v "$CONTAINER_COMMAND" &> /dev/null; then
        log_config_error "Container command not found: $CONTAINER_COMMAND"
        log_config "For Apple CLI, ensure /opt/homebrew/bin/container exists"
        return 1
    fi

    log_config_success "Configuration validated"
    return 0
}

# Display configuration summary
show_config_summary() {
    echo ""
    log_config "═══════════════════════════════════════════════════════"
    log_config " Configuration Summary"
    log_config "═══════════════════════════════════════════════════════"
    log_config " Runtime:     $NINA_RUNTIME (offset: +$RUNTIME_OFFSET)"
    log_config " Environment: $NINA_ENV (offset: +$ENV_OFFSET)"
    log_config " Command:     $CONTAINER_COMMAND"
    log_config ""
    log_config " Ports (SPEC-086):"
    log_config "   Database:   $DB_PORT"
    log_config "   PgBouncer:  $PGBOUNCER_PORT"
    log_config "   Redis:      $REDIS_PORT"
    log_config "   API:        $API_PORT"
    log_config "   Customer:   $CUSTOMER_UI_PORT"
    log_config "   Admin:      $ADMIN_UI_PORT"
    log_config ""
    log_config " Containers:"
    log_config "   DB:         $DB_CONTAINER"
    log_config "   PgBouncer:  $PGBOUNCER_CONTAINER"
    log_config "   Redis:      $REDIS_CONTAINER"
    log_config "   API:        $API_CONTAINER"
    log_config "═══════════════════════════════════════════════════════"
    echo ""
}

# Export function for use in other scripts
export -f load_config
export -f calculate_ports
export -f validate_config
