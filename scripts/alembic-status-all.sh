#!/bin/bash
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# Alembic Multi-Environment Status Check
# Shows current migration status for all schemas

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

PROJECT_ROOT="/Users/swami/WorkSpace/ninaivalaigal"

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║         ALEMBIC MULTI-ENVIRONMENT STATUS                  ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

cd "${PROJECT_ROOT}"

# Public Schema
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}PUBLIC SCHEMA (Main Application)${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}Config:${NC} alembic/public/alembic.ini"
echo -e "${YELLOW}Target:${NC} public schema"
echo -e "${YELLOW}Migrations:${NC} $(ls -1 alembic/public/versions/*.py 2>/dev/null | wc -l) files"
echo ""
echo -e "${YELLOW}Current version:${NC}"
/Users/swami/WorkSpace/ninaivalaigal/taiga/.venv/bin/alembic -c alembic/public/alembic.ini current 2>/dev/null | grep -v "^INFO" || echo "  (not yet stamped)"
echo ""
echo -e "${YELLOW}Heads:${NC}"
/Users/swami/WorkSpace/ninaivalaigal/taiga/.venv/bin/alembic -c alembic/public/alembic.ini heads 2>/dev/null | grep -v "^INFO" || echo "  (no heads)"
echo ""

# GraphOps Schema
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}GRAPHOPS SCHEMA (ag_catalog)${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}Config:${NC} alembic/graphops/alembic.ini"
echo -e "${YELLOW}Target:${NC} ag_catalog schema"
echo -e "${YELLOW}Migrations:${NC} $(ls -1 alembic/graphops/versions/*.py 2>/dev/null | wc -l) files"
echo ""
echo -e "${YELLOW}Current version:${NC}"
/Users/swami/WorkSpace/ninaivalaigal/taiga/.venv/bin/alembic -c alembic/graphops/alembic.ini current 2>/dev/null | grep -v "^INFO" || echo "  (not yet stamped)"
echo ""
echo -e "${YELLOW}Heads:${NC}"
/Users/swami/WorkSpace/ninaivalaigal/taiga/.venv/bin/alembic -c alembic/graphops/alembic.ini heads 2>/dev/null | grep -v "^INFO" || echo "  (no heads)"
echo ""

# Memory Schema
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}MEMORY SCHEMA${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}Config:${NC} alembic/memory/alembic.ini"
echo -e "${YELLOW}Target:${NC} memory schema"
echo -e "${YELLOW}Migrations:${NC} $(ls -1 alembic/memory/versions/*.py 2>/dev/null | wc -l) files"
echo ""
echo -e "${YELLOW}Current version:${NC}"
/Users/swami/WorkSpace/ninaivalaigal/taiga/.venv/bin/alembic -c "alembic/memory/alembic.ini" current 2>/dev/null || echo "  (not yet stamped)"
echo ""
echo -e "${YELLOW}Heads:${NC}"
/Users/swami/WorkSpace/ninaivalaigal/taiga/.venv/bin/alembic -c "alembic/memory/alembic.ini" heads 2>/dev/null | grep -v "^INFO" || echo "  (no heads)"
echo ""

# Intelligence Schema
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}INTELLIGENCE SCHEMA (intelligence_graph)${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}Config:${NC} alembic/intelligence/alembic.ini"
echo -e "${YELLOW}Target:${NC} intelligence_graph schema"
echo -e "${YELLOW}Migrations:${NC} $(ls -1 alembic/intelligence/versions/*.py 2>/dev/null | wc -l) files"
echo ""
echo -e "${YELLOW}Current version:${NC}"
/Users/swami/WorkSpace/ninaivalaigal/taiga/.venv/bin/alembic -c alembic/intelligence/alembic.ini current 2>/dev/null | grep -v "^INFO" || echo "  (not yet stamped)"
echo ""
echo -e "${YELLOW}Heads:${NC}"
/Users/swami/WorkSpace/ninaivalaigal/taiga/.venv/bin/alembic -c alembic/intelligence/alembic.ini heads 2>/dev/null | grep -v "^INFO" || echo "  (no heads)"
echo ""

echo -e "${GREEN}✅ Status check complete${NC}"
