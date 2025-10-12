#!/usr/bin/env bash
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
set -euo pipefail

# Generate all environment configuration files
# Creates configs/.env.{runtime}.{env} for all 9 combinations

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
CONFIGS_DIR="$PROJECT_ROOT/configs"

mkdir -p "$CONFIGS_DIR"

echo "🔧 Generating environment configuration files..."
echo ""

# Function to generate env file
generate_env() {
    local runtime=$1
    local env=$2
    local file="$CONFIGS_DIR/.env.${runtime}.${env}"

    # Port offsets
    local port_offset=0
    case "$runtime" in
        docker) port_offset=0 ;;
        colima) port_offset=10 ;;
        apple) port_offset=20 ;;
    esac

    local postgres_port=$((5432 + port_offset))
    local redis_port=$((6379 + port_offset))
    local api_port=$((8000 + port_offset))
    local customer_port=$((3000 + port_offset))
    local admin_port=$((3001 + port_offset))

    # Platform
    local platform="linux/amd64"
    [[ "$runtime" == "apple" ]] || [[ "$runtime" == "colima" ]] && platform="linux/arm64"

    # Environment-specific settings
    local node_env="development"
    local debug="1"
    local reload="1"
    local log_level="debug"
    local volume_mode="rw"
    local redis_maxmem="512mb"

    if [[ "$env" == "stage" ]]; then
        node_env="staging"
        log_level="info"
        redis_maxmem="1gb"
    elif [[ "$env" == "prod" ]]; then
        node_env="production"
        debug="0"
        reload="0"
        log_level="warning"
        volume_mode="ro"
        redis_maxmem="2gb"
    fi

    cat > "$file" << EOF
# ${runtime^} Runtime - ${env^} Environment
# Generated: $(date)
# Usage: docker-compose --env-file $file -f compose.${runtime}.${env}.yml up -d

# Environment & Runtime
NINA_ENV=$env
NINA_RUNTIME=$runtime
NODE_ENV=$node_env

# Platform
PLATFORM=$platform

# Ports (${runtime^}: +${port_offset} offset)
POSTGRES_PORT=$postgres_port
REDIS_PORT=$redis_port
API_PORT=$api_port
CUSTOMER_APP_PORT=$customer_port
ADMIN_CONSOLE_PORT=$admin_port

# Database (shared per environment)
NINA_DB_PASSWORD=${env}_${runtime}_db_password_CHANGE_ME
DATABASE_URL=postgresql://nina:${env}_${runtime}_db_password_CHANGE_ME@localhost:$postgres_port/ninaivalaigal_$env

# Redis (shared per environment)
NINA_REDIS_PASSWORD=${env}_${runtime}_redis_password_CHANGE_ME
REDIS_MAXMEMORY=$redis_maxmem
REDIS_DB=0

# Auth & Security
NINA_JWT_SECRET=${env}_${runtime}_jwt_secret_CHANGE_IN_PRODUCTION
JWT_SECRET_KEY=${env}_${runtime}_jwt_secret_CHANGE_IN_PRODUCTION

# API Configuration
NINA_DEBUG=$debug
UVICORN_RELOAD=$reload
LOG_LEVEL=$log_level
VOLUME_MODE=$volume_mode

# CORS
CORS_ORIGINS=http://localhost:$customer_port,http://localhost:$admin_port

# Project Root (for bind mounts)
PROJECT_ROOT=$PROJECT_ROOT
EOF

    echo "✓ Generated: .env.${runtime}.${env}"
}

# Generate all combinations
for runtime in docker colima apple; do
    for env in dev stage prod; do
        generate_env "$runtime" "$env"
    done
done

echo ""
echo "✅ Generated 9 environment configuration files in $CONFIGS_DIR"
echo ""
echo "⚠️  IMPORTANT: Update passwords in production!"
echo "   - NINA_DB_PASSWORD"
echo "   - NINA_REDIS_PASSWORD"
echo "   - NINA_JWT_SECRET"
