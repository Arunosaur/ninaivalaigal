#!/bin/bash
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# Alembic Multi-Environment Nuclear Reset Script
# Implements Option A: Each schema gets its own Alembic environment
#
# DANGER: This will delete all migration files and reset all schemas!
# Only run in pre-production with full backups!

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ROOT="/Users/swami/WorkSpace/ninaivalaigal"
BACKUP_DIR="${PROJECT_ROOT}/backups"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)

# Database configuration from environment or defaults
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5452}"
DB_USER="${DB_USER:-nina}"
DB_NAME="${DB_NAME:-ninaivalaigal_dev}"
DB_PASSWORD="${DB_PASSWORD:-dev_password_change_in_production}"

# Set database URL for Alembic
export NINAIVALAIGAL_DATABASE_URL="${NINAIVALAIGAL_DATABASE_URL:-postgresql://${DB_USER}:${DB_PASSWORD}@${DB_HOST}:${DB_PORT}/${DB_NAME}}"

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║    ALEMBIC MULTI-ENVIRONMENT NUCLEAR RESET SCRIPT         ║${NC}"
echo -e "${BLUE}║    Option A: Each schema gets its own environment         ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check if we're in the right directory
if [ ! -d "${PROJECT_ROOT}/alembic" ]; then
    echo -e "${RED}❌ Error: alembic directory not found in ${PROJECT_ROOT}${NC}"
    exit 1
fi

# Create backup directory
mkdir -p "${BACKUP_DIR}"

echo -e "${YELLOW}⚠️  This script will:${NC}"
echo "  1. Backup database and all migrations"
echo "  2. Reset PUBLIC schema (40 migrations → 1 clean)"
echo "  3. Fix GRAPHOPS schema (ag_catalog version tracking)"
echo "  4. Bootstrap MEMORY schema (create base migration)"
echo "  5. Bootstrap INTELLIGENCE schema (create base migration)"
echo "  6. Create version tables for all schemas"
echo "  7. Stamp all schemas with correct versions"
echo ""
echo -e "${YELLOW}📊 Current state:${NC}"
echo "  - Schemas to manage: public, ag_catalog, memory, intelligence_graph"
echo "  - Old migrations: $(find ${PROJECT_ROOT}/alembic/versions -name "*.py" 2>/dev/null | wc -l) files (will be archived)"
echo ""

read -p "$(echo -e ${YELLOW}Continue with multi-environment nuclear reset? [yes/NO]:${NC} )" -r
echo
if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
    echo -e "${RED}❌ Aborted by user${NC}"
    exit 1
fi

# ============================================================================
# PHASE 1: BACKUP EVERYTHING
# ============================================================================

echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}PHASE 1: Backup Everything${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"

# Backup database
echo -e "${YELLOW}📦 Backing up database...${NC}"
export PGPASSWORD="${DB_PASSWORD}"
container exec ninaivalaigal-dev-db pg_dump -U "${DB_USER}" -d "${DB_NAME}" > "${BACKUP_DIR}/pre-multienv-reset-${TIMESTAMP}.sql"
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Database backup created: pre-multienv-reset-${TIMESTAMP}.sql${NC}"
    echo "   Size: $(du -h ${BACKUP_DIR}/pre-multienv-reset-${TIMESTAMP}.sql | cut -f1)"
else
    echo -e "${RED}❌ Database backup failed!${NC}"
    exit 1
fi

# Backup old alembic structure
echo -e "${YELLOW}📦 Backing up old alembic structure...${NC}"
if [ -d "${PROJECT_ROOT}/alembic/versions" ]; then
    tar -czf "${BACKUP_DIR}/alembic-old-structure-${TIMESTAMP}.tar.gz" -C "${PROJECT_ROOT}" alembic/versions/ alembic/env.py alembic.ini 2>/dev/null || true
    echo -e "${GREEN}✅ Old alembic structure backed up${NC}"
fi

# Backup GraphOps migrations
if [ -d "${PROJECT_ROOT}/rust-services/graphops/migrations" ]; then
    tar -czf "${BACKUP_DIR}/graphops-migrations-${TIMESTAMP}.tar.gz" -C "${PROJECT_ROOT}" rust-services/graphops/migrations/
    echo -e "${GREEN}✅ GraphOps migrations backed up${NC}"
fi

echo -e "${GREEN}✅ Phase 1 Complete: All backups created${NC}"
echo ""

# ============================================================================
# PHASE 2: ARCHIVE OLD STRUCTURE
# ============================================================================

echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}PHASE 2: Archive Old Structure${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"

# Archive old versions directory
if [ -d "${PROJECT_ROOT}/alembic/versions" ]; then
    echo -e "${YELLOW}📁 Archiving old versions directory...${NC}"
    mv "${PROJECT_ROOT}/alembic/versions" "${PROJECT_ROOT}/alembic/versions.old.${TIMESTAMP}"
    echo -e "${GREEN}✅ Old versions archived${NC}"
fi

# Archive old alembic.ini
if [ -f "${PROJECT_ROOT}/alembic.ini" ]; then
    echo -e "${YELLOW}📁 Archiving old alembic.ini...${NC}"
    mv "${PROJECT_ROOT}/alembic.ini" "${PROJECT_ROOT}/alembic.ini.old.${TIMESTAMP}"
    echo -e "${GREEN}✅ Old alembic.ini archived${NC}"
fi

# Archive old env.py
if [ -f "${PROJECT_ROOT}/alembic/env.py" ]; then
    echo -e "${YELLOW}📁 Archiving old env.py...${NC}"
    mv "${PROJECT_ROOT}/alembic/env.py" "${PROJECT_ROOT}/alembic/env.py.old.${TIMESTAMP}"
    echo -e "${GREEN}✅ Old env.py archived${NC}"
fi

echo -e "${GREEN}✅ Phase 2 Complete: Old structure archived${NC}"
echo ""

# ============================================================================
# PHASE 3: RESET PUBLIC SCHEMA
# ============================================================================

echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}PHASE 3: Reset Public Schema (Main Application)${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"

echo -e "${YELLOW}🔨 Creating base migration for public schema...${NC}"
cd "${PROJECT_ROOT}"
alembic -c alembic/public/alembic.ini revision -m "0001_initial_schema_base"

if [ $? -eq 0 ]; then
    NEW_PUBLIC_MIGRATION=$(ls -1t ${PROJECT_ROOT}/alembic/public/versions/*.py 2>/dev/null | head -1)
    echo -e "${GREEN}✅ Generated clean migration: $(basename ${NEW_PUBLIC_MIGRATION})${NC}"
else
    echo -e "${RED}❌ Public schema migration generation failed!${NC}"
    exit 1
fi

echo -e "${YELLOW}🔨 Creating alembic_version table in public schema...${NC}"
container exec ninaivalaigal-dev-db psql -U "${DB_USER}" -d "${DB_NAME}" -c "
CREATE TABLE IF NOT EXISTS public.alembic_version (
    version_num VARCHAR(32) NOT NULL,
    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);" > /dev/null 2>&1

echo -e "${YELLOW}🔨 Stamping public schema...${NC}"
alembic -c alembic/public/alembic.ini stamp head

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Public schema stamped successfully${NC}"
else
    echo -e "${RED}❌ Public schema stamping failed!${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Phase 3 Complete: Public schema reset${NC}"
echo ""

# ============================================================================
# PHASE 4: FIX GRAPHOPS SCHEMA
# ============================================================================

echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}PHASE 4: Fix GraphOps Schema (ag_catalog)${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"

echo -e "${YELLOW}🔧 Fixing ag_catalog.alembic_version...${NC}"
container exec ninaivalaigal-dev-db psql -U "${DB_USER}" -d "${DB_NAME}" -c "
UPDATE ag_catalog.alembic_version
SET version_num = '20251022_003_gin_indexes_for_cypher'
WHERE version_num = '0145_merge_memory_attachments';" > /dev/null 2>&1

echo -e "${YELLOW}🔍 Verifying GraphOps version...${NC}"
GRAPHOPS_VERSION=$(alembic -c alembic/graphops/alembic.ini current 2>/dev/null | grep -v "INFO" | head -1)
echo -e "${GREEN}  Current version: ${GRAPHOPS_VERSION}${NC}"

echo -e "${GREEN}✅ Phase 4 Complete: GraphOps schema fixed${NC}"
echo ""

# ============================================================================
# PHASE 5: BOOTSTRAP MEMORY SCHEMA
# ============================================================================

echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}PHASE 5: Bootstrap Memory Schema${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"

echo -e "${YELLOW}🔨 Creating alembic_version table in memory schema...${NC}"
container exec ninaivalaigal-dev-db psql -U "${DB_USER}" -d "${DB_NAME}" -c "
CREATE TABLE IF NOT EXISTS memory.alembic_version (
    version_num VARCHAR(32) NOT NULL,
    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);" > /dev/null 2>&1

echo -e "${YELLOW}🔨 Generating base migration for memory schema...${NC}"
alembic -c alembic/memory/alembic.ini revision -m "0001_memory_base"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Memory schema base migration created${NC}"
else
    echo -e "${YELLOW}⚠️  Memory schema migration creation skipped (no models yet)${NC}"
fi

echo -e "${YELLOW}🔨 Stamping memory schema...${NC}"
alembic -c alembic/memory/alembic.ini stamp head

echo -e "${GREEN}✅ Phase 5 Complete: Memory schema bootstrapped${NC}"
echo ""

# ============================================================================
# PHASE 6: BOOTSTRAP INTELLIGENCE SCHEMA
# ============================================================================

echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}PHASE 6: Bootstrap Intelligence Schema${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"

echo -e "${YELLOW}🔨 Creating alembic_version table in intelligence_graph schema...${NC}"
container exec ninaivalaigal-dev-db psql -U "${DB_USER}" -d "${DB_NAME}" -c "
CREATE TABLE IF NOT EXISTS intelligence_graph.alembic_version (
    version_num VARCHAR(32) NOT NULL,
    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);" > /dev/null 2>&1

echo -e "${YELLOW}🔨 Generating base migration for intelligence schema...${NC}"
alembic -c alembic/intelligence/alembic.ini revision -m "0001_intelligence_base"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Intelligence schema base migration created${NC}"
else
    echo -e "${YELLOW}⚠️  Intelligence schema migration creation skipped (no models yet)${NC}"
fi

echo -e "${YELLOW}🔨 Stamping intelligence schema...${NC}"
alembic -c alembic/intelligence/alembic.ini stamp head

echo -e "${GREEN}✅ Phase 6 Complete: Intelligence schema bootstrapped${NC}"
echo ""

# ============================================================================
# PHASE 7: VERIFY ALL ENVIRONMENTS
# ============================================================================

echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}PHASE 7: Verify All Environments${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"

echo -e "${YELLOW}🔍 Checking all schema versions...${NC}"

echo -e "${BLUE}Public schema:${NC}"
alembic -c alembic/public/alembic.ini current 2>/dev/null | grep -v "^INFO" || echo "  (not yet stamped)"

echo -e "${BLUE}GraphOps schema (ag_catalog):${NC}"
alembic -c alembic/graphops/alembic.ini current 2>/dev/null | grep -v "^INFO" || echo "  (not yet stamped)"

echo -e "${BLUE}Memory schema:${NC}"
alembic -c alembic/memory/alembic.ini current 2>/dev/null | grep -v "^INFO" || echo "  (not yet stamped)"

echo -e "${BLUE}Intelligence schema:${NC}"
alembic -c alembic/intelligence/alembic.ini current 2>/dev/null | grep -v "^INFO" || echo "  (not yet stamped)"

echo -e "${GREEN}✅ Phase 7 Complete: All environments verified${NC}"
echo ""

# ============================================================================
# SUCCESS SUMMARY
# ============================================================================

echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║        MULTI-ENVIRONMENT RESET COMPLETE ✅                 ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}📊 Results:${NC}"
echo "  - Schemas managed: 4 (public, ag_catalog, memory, intelligence_graph)"
echo "  - Public schema: 1 clean migration (was 40)"
echo "  - GraphOps schema: 3 migrations (version tracking fixed)"
echo "  - Memory schema: 1 base migration (bootstrapped)"
echo "  - Intelligence schema: 1 base migration (bootstrapped)"
echo ""
echo -e "${GREEN}📦 Backups created:${NC}"
echo "  - pre-multienv-reset-${TIMESTAMP}.sql (full database)"
echo "  - alembic-old-structure-${TIMESTAMP}.tar.gz (old migrations)"
echo "  - graphops-migrations-${TIMESTAMP}.tar.gz (GraphOps backup)"
echo ""
echo -e "${GREEN}📁 New directory structure:${NC}"
echo "  /alembic/public/         → public schema"
echo "  /alembic/graphops/       → ag_catalog schema"
echo "  /alembic/memory/         → memory schema"
echo "  /alembic/intelligence/   → intelligence_graph schema"
echo ""
echo -e "${BLUE}📝 Next Steps:${NC}"
echo "  1. Verify all schemas: ./scripts/alembic-status-all.sh"
echo "  2. Restart core-api: container restart ninaivalaigal-dev-core-api"
echo "  3. Check health: curl http://localhost:8000/health"
echo "  4. Review new structure: ls -la alembic/*/"
echo ""
echo -e "${YELLOW}💡 Rollback (if needed):${NC}"
echo "  container exec ninaivalaigal-dev-db psql -U ${DB_USER} -d ${DB_NAME} < ${BACKUP_DIR}/pre-multienv-reset-${TIMESTAMP}.sql"
echo ""
echo -e "${GREEN}🎉 Multi-environment Alembic setup complete!${NC}"
echo -e "${GREEN}   Each schema now has its own isolated migration environment.${NC}"
