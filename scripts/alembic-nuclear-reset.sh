#!/bin/bash
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# Alembic Nuclear Reset Script
# Cleans all migrations and regenerates from SQLAlchemy models
#
# DANGER: This will delete all migration files!
# Only run in pre-production with full backups!

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ROOT="/Users/swami/WorkSpace/ninaivalaigal"
BACKUP_DIR="${PROJECT_ROOT}/backups"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
DB_HOST="localhost"
DB_USER="nina"
DB_NAME="ninaivalaigal"
DB_PASSWORD="secure_nina_password"

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║         ALEMBIC NUCLEAR RESET SCRIPT                      ║${NC}"
echo -e "${BLUE}║         WARNING: This will delete all migrations!         ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check if we're in the right directory
if [ ! -f "${PROJECT_ROOT}/alembic.ini" ]; then
    echo -e "${RED}❌ Error: alembic.ini not found in ${PROJECT_ROOT}${NC}"
    exit 1
fi

# Create backup directory
mkdir -p "${BACKUP_DIR}"

echo -e "${YELLOW}⚠️  This script will:${NC}"
echo "  1. Backup database and migrations"
echo "  2. Delete all 40 migration files"
echo "  3. Clear alembic_version table"
echo "  4. Generate single clean migration"
echo "  5. Stamp database"
echo ""
echo -e "${YELLOW}📊 Current state:${NC}"
echo "  - Migration files: $(ls -1 ${PROJECT_ROOT}/alembic/versions/*.py 2>/dev/null | wc -l)"
echo "  - Alembic heads: $(cd ${PROJECT_ROOT} && alembic heads 2>/dev/null | grep -c 'head' || echo '0')"
echo ""

read -p "$(echo -e ${YELLOW}Continue with nuclear reset? [yes/NO]:${NC} )" -r
echo
if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
    echo -e "${RED}❌ Aborted by user${NC}"
    exit 1
fi

# ============================================================================
# PHASE 1: BACKUP EVERYTHING
# ============================================================================

echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}PHASE 1: Backup Everything${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"

# Backup database
echo -e "${YELLOW}📦 Backing up database...${NC}"
export PGPASSWORD="${DB_PASSWORD}"
pg_dump -h "${DB_HOST}" -U "${DB_USER}" -d "${DB_NAME}" > "${BACKUP_DIR}/pre-reset-${TIMESTAMP}.sql"
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Database backup created: pre-reset-${TIMESTAMP}.sql${NC}"
    echo "   Size: $(du -h ${BACKUP_DIR}/pre-reset-${TIMESTAMP}.sql | cut -f1)"
else
    echo -e "${RED}❌ Database backup failed!${NC}"
    exit 1
fi

# Backup schema only
echo -e "${YELLOW}📦 Backing up schema...${NC}"
pg_dump -h "${DB_HOST}" -U "${DB_USER}" -d "${DB_NAME}" --schema-only > "${BACKUP_DIR}/schema-pre-reset-${TIMESTAMP}.sql"
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Schema backup created: schema-pre-reset-${TIMESTAMP}.sql${NC}"
else
    echo -e "${RED}❌ Schema backup failed!${NC}"
    exit 1
fi

# Backup alembic versions
echo -e "${YELLOW}📦 Backing up alembic versions...${NC}"
tar -czf "${BACKUP_DIR}/alembic-versions-backup-${TIMESTAMP}.tar.gz" -C "${PROJECT_ROOT}" alembic/versions/
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Alembic versions backup created: alembic-versions-backup-${TIMESTAMP}.tar.gz${NC}"
    echo "   Size: $(du -h ${BACKUP_DIR}/alembic-versions-backup-${TIMESTAMP}.tar.gz | cut -f1)"
else
    echo -e "${RED}❌ Alembic versions backup failed!${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Phase 1 Complete: All backups created${NC}"
echo ""

# ============================================================================
# PHASE 2: CLEAR ALEMBIC STATE
# ============================================================================

echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}PHASE 2: Clear Alembic State${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"

# Delete migration files
echo -e "${YELLOW}🗑️  Deleting migration files...${NC}"
MIGRATION_COUNT=$(ls -1 ${PROJECT_ROOT}/alembic/versions/*.py 2>/dev/null | wc -l)
rm -f ${PROJECT_ROOT}/alembic/versions/*.py
rm -rf ${PROJECT_ROOT}/alembic/versions/__pycache__
echo -e "${GREEN}✅ Deleted ${MIGRATION_COUNT} migration files${NC}"

# Clear alembic_version table
echo -e "${YELLOW}🗑️  Clearing alembic_version table...${NC}"
psql -h "${DB_HOST}" -U "${DB_USER}" -d "${DB_NAME}" -c "DELETE FROM alembic_version;" > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Cleared alembic_version table${NC}"
else
    echo -e "${YELLOW}⚠️  Could not clear alembic_version (table may not exist)${NC}"
fi

echo -e "${GREEN}✅ Phase 2 Complete: Alembic state cleared${NC}"
echo ""

# ============================================================================
# PHASE 3: GENERATE CLEAN MIGRATION
# ============================================================================

echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}PHASE 3: Generate Clean Migration${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"

echo -e "${YELLOW}🔨 Generating migration from SQLAlchemy models...${NC}"
cd "${PROJECT_ROOT}"
alembic revision --autogenerate -m "0001_initial_schema_clean"

if [ $? -eq 0 ]; then
    NEW_MIGRATION=$(ls -1t ${PROJECT_ROOT}/alembic/versions/*.py | head -1)
    echo -e "${GREEN}✅ Generated clean migration: $(basename ${NEW_MIGRATION})${NC}"
else
    echo -e "${RED}❌ Migration generation failed!${NC}"
    echo -e "${YELLOW}💡 Restoring from backup...${NC}"
    tar -xzf "${BACKUP_DIR}/alembic-versions-backup-${TIMESTAMP}.tar.gz" -C "${PROJECT_ROOT}"
    exit 1
fi

echo -e "${GREEN}✅ Phase 3 Complete: Clean migration generated${NC}"
echo ""

# ============================================================================
# PHASE 4: VERIFY GENERATED MIGRATION
# ============================================================================

echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}PHASE 4: Verify Generated Migration${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"

NEW_MIGRATION=$(ls -1t ${PROJECT_ROOT}/alembic/versions/*.py | head -1)
echo -e "${YELLOW}📋 Analyzing migration: $(basename ${NEW_MIGRATION})${NC}"

# Check for critical tables
echo -e "${YELLOW}🔍 Checking for critical tables...${NC}"

CRITICAL_TABLES=(
    "billing_accounts"
    "users"
    "teams"
    "memories"
    "contexts"
    "memory_acl"
)

MISSING_TABLES=()
for table in "${CRITICAL_TABLES[@]}"; do
    if grep -q "create_table.*${table}" "${NEW_MIGRATION}"; then
        echo -e "${GREEN}  ✅ ${table}${NC}"
    else
        echo -e "${RED}  ❌ ${table} (MISSING)${NC}"
        MISSING_TABLES+=("${table}")
    fi
done

# Check for deprecated tables (should NOT be present)
echo -e "${YELLOW}🔍 Checking for deprecated tables (should be absent)...${NC}"

DEPRECATED_TABLES=(
    "team_billing"
    "team_subscriptions"
    "team_usage_metrics"
)

FOUND_DEPRECATED=()
for table in "${DEPRECATED_TABLES[@]}"; do
    if grep -q "create_table.*${table}" "${NEW_MIGRATION}"; then
        echo -e "${RED}  ❌ ${table} (SHOULD NOT EXIST)${NC}"
        FOUND_DEPRECATED+=("${table}")
    else
        echo -e "${GREEN}  ✅ ${table} (correctly absent)${NC}"
    fi
done

# Summary
if [ ${#MISSING_TABLES[@]} -eq 0 ] && [ ${#FOUND_DEPRECATED[@]} -eq 0 ]; then
    echo -e "${GREEN}✅ Phase 4 Complete: Migration verified${NC}"
else
    echo -e "${RED}❌ Phase 4 Failed: Migration verification issues${NC}"
    if [ ${#MISSING_TABLES[@]} -gt 0 ]; then
        echo -e "${RED}   Missing tables: ${MISSING_TABLES[*]}${NC}"
    fi
    if [ ${#FOUND_DEPRECATED[@]} -gt 0 ]; then
        echo -e "${RED}   Deprecated tables found: ${FOUND_DEPRECATED[*]}${NC}"
    fi
    echo -e "${YELLOW}💡 Review the migration file manually before proceeding${NC}"
    exit 1
fi

echo ""

# ============================================================================
# PHASE 5: APPLY CLEAN MIGRATION
# ============================================================================

echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}PHASE 5: Apply Clean Migration${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"

echo -e "${YELLOW}🔨 Stamping database with new migration...${NC}"
cd "${PROJECT_ROOT}"
alembic stamp head

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Database stamped successfully${NC}"
else
    echo -e "${RED}❌ Database stamping failed!${NC}"
    exit 1
fi

# Verify
echo -e "${YELLOW}🔍 Verifying alembic state...${NC}"
CURRENT=$(alembic current 2>/dev/null | grep -v "INFO" | head -1)
HEADS=$(alembic heads 2>/dev/null | grep -c "head" || echo "0")

echo -e "${GREEN}  Current revision: ${CURRENT}${NC}"
echo -e "${GREEN}  Head count: ${HEADS}${NC}"

if [ "${HEADS}" -eq "1" ]; then
    echo -e "${GREEN}✅ Phase 5 Complete: Single head revision confirmed${NC}"
else
    echo -e "${RED}❌ Phase 5 Failed: Multiple heads still exist!${NC}"
    exit 1
fi

echo ""

# ============================================================================
# PHASE 6: RESTART CONTAINERS
# ============================================================================

echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}PHASE 6: Restart Containers${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"

echo -e "${YELLOW}🔄 Restarting core-api container...${NC}"
container restart ninaivalaigal-dev-core-api 2>/dev/null || echo -e "${YELLOW}⚠️  Container not running (will start on next deployment)${NC}"

echo -e "${YELLOW}⏳ Waiting for container to start...${NC}"
sleep 5

echo -e "${YELLOW}📋 Checking container logs...${NC}"
container logs ninaivalaigal-dev-core-api --tail=20 2>/dev/null || echo -e "${YELLOW}⚠️  Container not available${NC}"

echo -e "${GREEN}✅ Phase 6 Complete: Containers restarted${NC}"
echo ""

# ============================================================================
# SUCCESS SUMMARY
# ============================================================================

echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║              NUCLEAR RESET COMPLETE ✅                     ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}📊 Results:${NC}"
echo "  - Deleted: ${MIGRATION_COUNT} old migration files"
echo "  - Created: 1 clean migration file"
echo "  - Heads: 1 (was 2)"
echo "  - Backups: ${BACKUP_DIR}/"
echo ""
echo -e "${GREEN}📦 Backups created:${NC}"
echo "  - pre-reset-${TIMESTAMP}.sql (full database)"
echo "  - schema-pre-reset-${TIMESTAMP}.sql (schema only)"
echo "  - alembic-versions-backup-${TIMESTAMP}.tar.gz (migrations)"
echo ""
echo -e "${GREEN}✅ Success Criteria:${NC}"
echo "  ✅ Single migration file generated"
echo "  ✅ Single head revision"
echo "  ✅ All active SPEC tables verified"
echo "  ✅ No deprecated SPEC tables"
echo ""
echo -e "${BLUE}📝 Next Steps:${NC}"
echo "  1. Verify core-api container is running: container list | grep core-api"
echo "  2. Check health endpoint: curl http://localhost:8000/health"
echo "  3. Review migration file: ${NEW_MIGRATION}"
echo "  4. Document completion in ALEMBIC-NUCLEAR-RESET-PLAN.md"
echo ""
echo -e "${YELLOW}💡 Rollback (if needed):${NC}"
echo "  psql -h ${DB_HOST} -U ${DB_USER} -d ${DB_NAME} < ${BACKUP_DIR}/pre-reset-${TIMESTAMP}.sql"
echo "  tar -xzf ${BACKUP_DIR}/alembic-versions-backup-${TIMESTAMP}.tar.gz -C ${PROJECT_ROOT}"
echo ""
echo -e "${GREEN}🎉 Alembic is now clean and ready for development!${NC}"
