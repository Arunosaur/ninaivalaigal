#!/bin/bash
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# Alembic Multi-Environment Verification Script
# Verifies all schemas are healthy and properly configured

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

PROJECT_ROOT="/Users/swami/WorkSpace/ninaivalaigal"
DB_USER="nina"
DB_NAME="ninaivalaigal_dev"

ERRORS=0

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║      ALEMBIC MULTI-ENVIRONMENT VERIFICATION                ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

cd "${PROJECT_ROOT}"

# Check 1: Directory structure
echo -e "${YELLOW}🔍 Checking directory structure...${NC}"
REQUIRED_DIRS=(
    "alembic/public"
    "alembic/public/versions"
    "alembic/graphops"
    "alembic/graphops/versions"
    "alembic/memory"
    "alembic/memory/versions"
    "alembic/intelligence"
    "alembic/intelligence/versions"
)

for dir in "${REQUIRED_DIRS[@]}"; do
    if [ -d "${PROJECT_ROOT}/${dir}" ]; then
        echo -e "${GREEN}  ✅ ${dir}${NC}"
    else
        echo -e "${RED}  ❌ ${dir} (MISSING)${NC}"
        ERRORS=$((ERRORS + 1))
    fi
done
echo ""

# Check 2: Configuration files
echo -e "${YELLOW}🔍 Checking configuration files...${NC}"
REQUIRED_FILES=(
    "alembic/public/env.py"
    "alembic/public/alembic.ini"
    "alembic/graphops/env.py"
    "alembic/graphops/alembic.ini"
    "alembic/memory/env.py"
    "alembic/memory/alembic.ini"
    "alembic/intelligence/env.py"
    "alembic/intelligence/alembic.ini"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "${PROJECT_ROOT}/${file}" ]; then
        echo -e "${GREEN}  ✅ ${file}${NC}"
    else
        echo -e "${RED}  ❌ ${file} (MISSING)${NC}"
        ERRORS=$((ERRORS + 1))
    fi
done
echo ""

# Check 3: Version tables in database
echo -e "${YELLOW}🔍 Checking version tables in database...${NC}"

check_version_table() {
    local schema=$1
    local result=$(container exec ninaivalaigal-dev-db psql -U "${DB_USER}" -d "${DB_NAME}" -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = '${schema}' AND table_name = 'alembic_version';" 2>/dev/null | tr -d ' ')

    if [ "$result" = "1" ]; then
        echo -e "${GREEN}  ✅ ${schema}.alembic_version${NC}"
        return 0
    else
        echo -e "${RED}  ❌ ${schema}.alembic_version (MISSING)${NC}"
        ERRORS=$((ERRORS + 1))
        return 1
    fi
}

check_version_table "public"
check_version_table "ag_catalog"
check_version_table "memory"
check_version_table "intelligence_graph"
echo ""

# Check 4: Alembic heads (should be exactly 1 per environment)
echo -e "${YELLOW}🔍 Checking Alembic heads...${NC}"

check_heads() {
    local env=$1
    local config=$2
    local heads=$(alembic -c "${config}" heads 2>/dev/null | grep -c "head" || echo "0")

    if [ "$heads" = "1" ]; then
        echo -e "${GREEN}  ✅ ${env}: 1 head${NC}"
        return 0
    elif [ "$heads" = "0" ]; then
        echo -e "${YELLOW}  ⚠️  ${env}: 0 heads (not yet stamped)${NC}"
        return 0
    else
        echo -e "${RED}  ❌ ${env}: ${heads} heads (CONFLICT!)${NC}"
        ERRORS=$((ERRORS + 1))
        return 1
    fi
}

check_heads "public" "alembic/public/alembic.ini"
check_heads "graphops" "alembic/graphops/alembic.ini"
check_heads "memory" "alembic/memory/alembic.ini"
check_heads "intelligence" "alembic/intelligence/alembic.ini"
echo ""

# Check 5: Migration files exist
echo -e "${YELLOW}🔍 Checking migration files...${NC}"

check_migrations() {
    local env=$1
    local path=$2
    local count=$(ls -1 "${PROJECT_ROOT}/${path}"/*.py 2>/dev/null | wc -l)

    if [ "$count" -gt "0" ]; then
        echo -e "${GREEN}  ✅ ${env}: ${count} migration(s)${NC}"
        return 0
    else
        echo -e "${YELLOW}  ⚠️  ${env}: 0 migrations (not yet generated)${NC}"
        return 0
    fi
}

check_migrations "public" "alembic/public/versions"
check_migrations "graphops" "alembic/graphops/versions"
check_migrations "memory" "alembic/memory/versions"
check_migrations "intelligence" "alembic/intelligence/versions"
echo ""

# Check 6: Old structure archived
echo -e "${YELLOW}🔍 Checking old structure cleanup...${NC}"

if [ -d "${PROJECT_ROOT}/alembic/versions" ] && [ ! -L "${PROJECT_ROOT}/alembic/versions" ]; then
    echo -e "${RED}  ❌ Old alembic/versions directory still exists (should be archived)${NC}"
    ERRORS=$((ERRORS + 1))
else
    echo -e "${GREEN}  ✅ Old alembic/versions directory archived or removed${NC}"
fi

if [ -f "${PROJECT_ROOT}/alembic.ini" ] && [ ! -L "${PROJECT_ROOT}/alembic.ini" ]; then
    echo -e "${RED}  ❌ Old alembic.ini still exists (should be archived)${NC}"
    ERRORS=$((ERRORS + 1))
else
    echo -e "${GREEN}  ✅ Old alembic.ini archived or removed${NC}"
fi
echo ""

# Summary
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}✅ VERIFICATION PASSED${NC}"
    echo -e "${GREEN}   All schemas are properly configured!${NC}"
    exit 0
else
    echo -e "${RED}❌ VERIFICATION FAILED${NC}"
    echo -e "${RED}   Found ${ERRORS} error(s)${NC}"
    echo ""
    echo -e "${YELLOW}💡 Run the reset script to fix issues:${NC}"
    echo "   ./scripts/alembic-reset-all.sh"
    exit 1
fi
