#!/usr/bin/env bash
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
# Dynamic Port Assignment for Environment + Runtime Combinations
# Usage: ./get-port.sh <service> <environment> <runtime>

set -eo pipefail

SERVICE="${1:-postgres}"
ENV="${2:-dev}"
RUNTIME="${3:-docker}"

# Get base port for service
get_base_port() {
    case "$1" in
        "postgres") echo "5432" ;;      # Main PostgreSQL (includes Apache AGE extension)
        "redis") echo "6379" ;;         # Main Redis cache
        "api") echo "13370" ;;          # FastAPI server
        "ui") echo "8081" ;;            # Frontend UI
        "pgbouncer") echo "6432" ;;     # PostgreSQL connection pooler
        *) echo "8000" ;;               # Default fallback
    esac
}

# Get environment offset
get_env_offset() {
    case "$1" in
        "dev") echo "0" ;;
        "test") echo "100" ;;
        "prod") echo "200" ;;
        *) echo "0" ;;
    esac
}

# Get runtime offset
get_runtime_offset() {
    case "$1" in
        "docker") echo "0" ;;
        "colima") echo "10" ;;
        "apple") echo "20" ;;
        *) echo "0" ;;
    esac
}

# Calculate final port
BASE_PORT=$(get_base_port "$SERVICE")
ENV_OFFSET=$(get_env_offset "$ENV")
RUNTIME_OFFSET=$(get_runtime_offset "$RUNTIME")

FINAL_PORT=$((BASE_PORT + ENV_OFFSET + RUNTIME_OFFSET))

echo "$FINAL_PORT"
