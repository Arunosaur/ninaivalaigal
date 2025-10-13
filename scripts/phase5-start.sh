#!/bin/bash
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
# Phase-5 Kickoff Script: Frontend Split Initialization
# Run this on Monday, October 13, 2025 to begin Phase-5 execution
set -euo pipefail

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🚀 PHASE-5 KICKOFF: Frontend Split"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Step 1: Environment Verification
echo "📋 Step 1/7: Environment Verification"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check conda environment
if [[ "$CONDA_DEFAULT_ENV" != "nina" ]]; then
    echo -e "${RED}❌ Wrong conda environment: $CONDA_DEFAULT_ENV${NC}"
    echo "   Run: conda activate nina"
    exit 1
fi
echo -e "${GREEN}✅ Conda environment: nina${NC}"

# Check Node.js version
NODE_VERSION=$(node --version | cut -d'v' -f2 | cut -d'.' -f1)
if [[ "$NODE_VERSION" -lt 18 ]]; then
    echo -e "${RED}❌ Node.js version too old: $(node --version)${NC}"
    echo "   Required: v18+"
    exit 1
fi
echo -e "${GREEN}✅ Node.js: $(node --version)${NC}"

# Check Python version
PYTHON_VERSION=$(python --version | cut -d' ' -f2 | cut -d'.' -f1,2)
if [[ "$PYTHON_VERSION" != "3.11" ]]; then
    echo -e "${YELLOW}⚠️  Python version: $(python --version) (expected 3.11)${NC}"
fi
echo -e "${GREEN}✅ Python: $(python --version)${NC}"

echo ""

# Step 2: Git Status Check
echo "📋 Step 2/7: Git Status Check"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Ensure we're on main
CURRENT_BRANCH=$(git branch --show-current)
if [[ "$CURRENT_BRANCH" != "main" ]]; then
    echo -e "${YELLOW}⚠️  Not on main branch: $CURRENT_BRANCH${NC}"
    echo -n "Switch to main? (y/n): "
    read -r SWITCH
    if [[ "$SWITCH" == "y" ]]; then
        git checkout main
    else
        echo -e "${RED}❌ Must be on main branch for Phase-5 kickoff${NC}"
        exit 1
    fi
fi
echo -e "${GREEN}✅ On main branch${NC}"

# Pull latest
echo "Pulling latest from origin..."
git pull origin main
echo -e "${GREEN}✅ Up to date with origin/main${NC}"

# Verify baseline tag
CURRENT_TAG=$(git describe --tags --exact-match 2>/dev/null || echo "none")
if [[ "$CURRENT_TAG" == "v5.0-frontend-split-audit-final" ]]; then
    echo -e "${GREEN}✅ On baseline tag: $CURRENT_TAG${NC}"
else
    LATEST_TAG=$(git describe --tags --abbrev=0)
    echo -e "${YELLOW}⚠️  Not on baseline tag (latest: $LATEST_TAG)${NC}"
fi

# Check for uncommitted changes
if [[ -n $(git status --porcelain) ]]; then
    echo -e "${RED}❌ Uncommitted changes detected${NC}"
    git status --short
    exit 1
fi
echo -e "${GREEN}✅ Clean working directory${NC}"

echo ""

# Step 3: Container Stack Verification
echo "📋 Step 3/7: Container Stack Verification"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check required containers
REQUIRED_CONTAINERS=(
    "ninaivalaigal-dev-db"
    "ninaivalaigal-dev-pgbouncer"
    "ninaivalaigal-dev-redis"
    "ninaivalaigal-dev-api"
)

ALL_RUNNING=true
for container_name in "${REQUIRED_CONTAINERS[@]}"; do
    if container list | grep -q "$container_name.*running"; then
        echo -e "${GREEN}✅ $container_name running${NC}"
    else
        echo -e "${RED}❌ $container_name NOT running${NC}"
        ALL_RUNNING=false
    fi
done

if [[ "$ALL_RUNNING" == false ]]; then
    echo ""
    echo -e "${YELLOW}Starting container stack...${NC}"
    ./scripts/ninaivalaigal-dev-stack-start.sh
    echo -e "${GREEN}✅ Container stack started${NC}"
fi

echo ""

# Step 4: Smoke Tests
echo "📋 Step 4/7: Smoke Tests Verification"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

echo "Running smoke tests..."
if pytest tests/smoke/test_critical_infrastructure.py -v --tb=short; then
    echo -e "${GREEN}✅ Smoke tests PASSED${NC}"
else
    echo -e "${RED}❌ Smoke tests FAILED${NC}"
    echo "   Fix smoke tests before continuing Phase-5"
    exit 1
fi

echo ""

# Step 5: Turborepo Workspace Initialization
echo "📋 Step 5/7: Turborepo Workspace Initialization"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check if workspaces already exist
if [[ -d "frontend-shared" ]]; then
    echo -e "${YELLOW}⚠️  frontend-shared/ already exists${NC}"
else
    echo "Creating workspace directories..."
    mkdir -p frontend-shared frontend-nextjs-customer frontend-nextjs-admin
    echo -e "${GREEN}✅ Workspace directories created${NC}"
fi

# Create placeholder README files
for workspace in frontend-shared frontend-nextjs-customer frontend-nextjs-admin; do
    if [[ ! -f "$workspace/README.md" ]]; then
        cat > "$workspace/README.md" << EOF
# $(echo $workspace | tr '[:lower:]' '[:upper:]' | tr '-' ' ')

**Status:** 🚧 Initialized (Phase-5 Kickoff)
**Created:** $(date +%Y-%m-%d)

## Overview
Placeholder workspace created by \`phase5-start.sh\`.

## SPEC References
- See \`specs/121-frontend-shared-library/\` for frontend-shared
- See \`specs/122-customer-frontend-rollout/\` for customer app
- See \`specs/123-admin-frontend-rollout/\` for admin app

## Development
\`\`\`bash
# Install dependencies
npm install

# Run development server
npm run dev
\`\`\`

## Next Steps
Refer to SPEC documentation for implementation details.
EOF
        echo -e "${GREEN}✅ Created $workspace/README.md${NC}"
    fi
done

echo ""

# Step 6: Pre-commit Hook Verification
echo "📋 Step 6/7: Pre-commit Hook Verification"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [[ -f ".git/hooks/pre-commit" ]]; then
    echo -e "${GREEN}✅ Pre-commit hook installed${NC}"
else
    echo -e "${YELLOW}⚠️  Installing pre-commit hooks...${NC}"
    pre-commit install
    echo -e "${GREEN}✅ Pre-commit hooks installed${NC}"
fi

if [[ -f ".git/hooks/pre-push" ]]; then
    echo -e "${GREEN}✅ Pre-push hook installed${NC}"
else
    echo -e "${RED}❌ Pre-push hook missing${NC}"
    echo "   Check .git/hooks/pre-push"
fi

echo ""

# Step 7: Create Initial Feature Branches
echo "📋 Step 7/7: Feature Branch Setup"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

echo ""
echo "Create feature branches for Phase-5 work?"
echo "  1. feature/121-frontend-shared-init"
echo "  2. feature/122-customer-app-baseline"
echo "  3. feature/124-turborepo-cicd"
echo ""
echo -n "Create branches? (y/n): "
read -r CREATE_BRANCHES

if [[ "$CREATE_BRANCHES" == "y" ]]; then
    BRANCHES=(
        "feature/121-frontend-shared-init"
        "feature/122-customer-app-baseline"
        "feature/124-turborepo-cicd"
    )

    for branch in "${BRANCHES[@]}"; do
        if git rev-parse --verify "$branch" >/dev/null 2>&1; then
            echo -e "${YELLOW}⚠️  Branch $branch already exists${NC}"
        else
            git branch "$branch"
            git push -u origin "$branch"
            echo -e "${GREEN}✅ Created and pushed $branch${NC}"
        fi
    done
else
    echo -e "${BLUE}ℹ️  Skipping branch creation${NC}"
fi

echo ""

# Final Summary
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ PHASE-5 KICKOFF COMPLETE"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo -e "${GREEN}🎯 Environment Status:${NC}"
echo "  • Conda: nina"
echo "  • Git: main branch (clean)"
echo "  • Tag: $(git describe --tags --abbrev=0)"
echo "  • Containers: All running"
echo "  • Smoke tests: PASSED"
echo ""
echo -e "${BLUE}📂 Workspaces Created:${NC}"
echo "  • frontend-shared/"
echo "  • frontend-nextjs-customer/"
echo "  • frontend-nextjs-admin/"
echo ""
echo -e "${YELLOW}📋 Next Steps:${NC}"
echo "  1. Review SPEC-121, SPEC-122, SPEC-124"
echo "  2. Checkout feature branch: git checkout feature/XXX"
echo "  3. Begin implementation"
echo "  4. Daily: git rebase origin/main"
echo "  5. Open draft PRs for visibility"
echo ""
echo -e "${BLUE}📚 Key Resources:${NC}"
echo "  • SPECs: specs/SPEC_INDEX.md"
echo "  • Phase Plan: specs/PHASE_SUMMARIES/PHASE_5_KICKOFF.md"
echo "  • Onboarding: docs/DEVELOPER_ONBOARDING.md"
echo "  • Baseline: specs/PHASE_SUMMARIES/FRONTEND_SPLIT_GAP_ANALYSIS.md"
echo ""
echo -e "${GREEN}🚀 Phase-5 execution begins NOW!${NC}"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
