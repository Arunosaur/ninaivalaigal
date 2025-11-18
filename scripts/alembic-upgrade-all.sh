#!/bin/bash
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# Upgrade all Alembic environments with single source of truth

set -euo pipefail

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║         ALEMBIC UGRADE ALL ENVIRONMENTS                   ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo

# Function to upgrade a single environment
upgrade_env() {
    local env=$1
    local description=$2
    
    echo -e "${YELLOW}Upgrading $description...${NC}"
    
    if [ -f "alembic/$env/alembic.ini" ]; then
        /Users/swami/WorkSpace/ninaivalaigal/taiga/.venv/bin/alembic -c "alembic/$env/alembic.ini" upgrade head
        echo -e "${GREEN}✅ $description upgraded successfully${NC}"
    else
        echo -e "${YELLOW}⚠️  $environment not found, skipping${NC}"
    fi
    echo
}

# Core API (main application)
upgrade_env "public" "Core API Schema (core_api)"

# GraphOps
upgrade_env "graphops" "GraphOps Schema (ag_catalog)"

# Memory
upgrade_env "memory" "Memory Schema"

# Intelligence
upgrade_env "intelligence" "Intelligence Schema (intelligence_graph)"

# Compliance schemas (optional - only if they exist)
for env in compliance hipaa incident_response iso27001 pentest security soc2; do
    if [ -f "alembic/$env/alembic.ini" ] && [ -d "alembic/$env/versions" ] && [ "$(ls -A alembic/$env/versions)" ]; then
        upgrade_env "$env" "Compliance Schema ($env)"
    fi
done

echo -e "${GREEN}🎉 All environments upgraded successfully!${NC}"
echo
echo "Run './scripts/alembic-status-all.sh' to verify all schemas are up to date."
