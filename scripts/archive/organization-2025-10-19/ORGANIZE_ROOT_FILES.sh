#!/bin/bash
# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Medhasys LLC
#
# Organize root files - move everything except essentials to proper locations
# shellcheck disable=SC2010,SC2035,SC2126  # One-time organization script, style warnings acceptable

echo "🧹 ORGANIZING ROOT FILES"
echo "========================"
echo ""
# shellcheck disable=SC2010  # Complex pattern, needs review
echo "Total files before: $(ls -p | grep -v / | wc -l)"
echo ""

# Create organized directories
mkdir -p docs/reports
mkdir -p docs/guides
mkdir -p docs/status-updates
mkdir -p config/frontend
mkdir -p config/testing
mkdir -p test-outputs
mkdir -p .reports

# Move status reports and completion reports to docs/status-updates/
echo "📋 Moving status reports..."
mv *_STATUS*.md docs/status-updates/ 2>/dev/null
mv *_COMPLETE*.md docs/status-updates/ 2>/dev/null
mv *_REPORT*.md docs/status-updates/ 2>/dev/null
mv TONIGHT_SUMMARY.md docs/status-updates/ 2>/dev/null
mv sprint_demo_prep.md docs/status-updates/ 2>/dev/null
mv test_status.md docs/status-updates/ 2>/dev/null

# Move Developer A specific docs to docs/guides/
echo "📚 Moving developer guides..."
mv DEVELOPER_A*.md docs/guides/ 2>/dev/null
mv DEVELOPER_B*.md docs/guides/ 2>/dev/null

# Move project-specific reports to docs/reports/
echo "📊 Moving project reports..."
mv MICROSERVICES*.md docs/reports/ 2>/dev/null
mv MISSING_ROUTERS*.md docs/reports/ 2>/dev/null
mv WORKSPACE_ROOT*.md docs/reports/ 2>/dev/null
mv ROOT_FILE*.* docs/reports/ 2>/dev/null
mv ZOMBIE*.md docs/reports/ 2>/dev/null

# Move Taiga-related docs to docs/guides/
echo "📋 Moving Taiga docs..."
mv TAIGA*.md docs/guides/ 2>/dev/null
mv RUN_TAIGA*.md docs/guides/ 2>/dev/null

# Move quick start guides to docs/guides/
echo "📖 Moving guides..."
mv RECONNECT*.md docs/guides/ 2>/dev/null
mv SPEC-099*.md docs/guides/ 2>/dev/null
mv HYBRID*.md docs/guides/ 2>/dev/null

# Move frontend test files to config/frontend/
echo "🌐 Moving frontend files..."
mv frontend-*.js config/frontend/ 2>/dev/null

# Move config files to config/
echo "⚙️  Moving config files..."
mv *.config.json config/ 2>/dev/null
mv *.config.yaml config/ 2>/dev/null
mv settings.json config/ 2>/dev/null
mv redis.conf config/ 2>/dev/null

# Move test outputs to test-outputs/
echo "🧪 Moving test outputs..."
mv *_screenshot.png test-outputs/ 2>/dev/null
mv load_test_output.txt test-outputs/ 2>/dev/null
mv test-cluster-info.txt test-outputs/ 2>/dev/null
mv metrics_after.txt test-outputs/ 2>/dev/null
mv phase-2b-status.png test-outputs/ 2>/dev/null
mv test.db test-outputs/ 2>/dev/null

# Move reports to .reports/ (hidden)
echo "📈 Moving report files..."
mv bandit-report.json .reports/ 2>/dev/null
mv coverage.json .reports/ 2>/dev/null
mv coverage.xml .reports/ 2>/dev/null

# Move additional docker-compose files to containers/
echo "🐳 Moving container configs..."
mkdir -p containers/compose
mv docker-compose.*.yml containers/compose/ 2>/dev/null

# Move postman collection to config/testing/
echo "📮 Moving Postman collection..."
mv postman-*.json config/testing/ 2>/dev/null

# Move policy files to config/
echo "🔒 Moving policy files..."
mv rbac_policy_*.json config/ 2>/dev/null

# Move patch files to a patches directory
echo "🩹 Moving patch files..."
mkdir -p .patches
mv *.patch .patches/ 2>/dev/null

# Move mem0 binary/config to config/
echo "💾 Moving mem0 files..."
mv mem0 config/ 2>/dev/null
mv mem0.config.json config/ 2>/dev/null

echo ""
echo "✅ ORGANIZATION COMPLETE"
echo "========================"
echo ""
# shellcheck disable=SC2010  # Complex pattern, needs review
echo "Files remaining in root: $(ls -p | grep -v / | wc -l)"
echo ""
echo "What should be in root:"
# shellcheck disable=SC2010  # Complex pattern, needs review
ls -p | grep -v / | sort
