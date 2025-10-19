#!/bin/bash
# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Medhasys LLC
#
# Clean up workspace root - move scripts to organized directories

echo "🧹 WORKSPACE ROOT CLEANUP"
echo "========================="
echo ""

# Create organized structure
mkdir -p scripts/taiga
mkdir -p scripts/developer-a
mkdir -p scripts/testing
mkdir -p scripts/deployment
mkdir -p scripts/utils

echo "✅ Created scripts directories"
echo ""

# Move Taiga-related scripts
echo "Moving Taiga scripts..."
mv add_taiga_comments.py scripts/taiga/ 2>/dev/null
mv check_taiga_status.py scripts/taiga/ 2>/dev/null
mv execute_taiga_update_now.py scripts/taiga/ 2>/dev/null
mv find_and_update_tasks.py scripts/taiga/ 2>/dev/null
mv run_taiga_update.py scripts/taiga/ 2>/dev/null
mv simple_taiga_check.py scripts/taiga/ 2>/dev/null
mv taiga_live_update.py scripts/taiga/ 2>/dev/null
mv update_all_taiga_tasks.py scripts/taiga/ 2>/dev/null
mv update_developer_a_tasks_CORRECT.py scripts/taiga/ 2>/dev/null
mv update_taiga_all_teams.py scripts/taiga/ 2>/dev/null
mv check_available_tasks.py scripts/taiga/ 2>/dev/null
mv run_developer_a_update.py scripts/taiga/ 2>/dev/null

mv *taiga*.sh scripts/taiga/ 2>/dev/null
echo "✅ Taiga scripts moved"

# Move Developer A scripts
echo "Moving Developer A scripts..."
mv check_developer_a_assignments.py scripts/developer-a/ 2>/dev/null
mv check_developer_a_status.py scripts/developer-a/ 2>/dev/null
mv check_developer_a_taiga_status.py scripts/developer-a/ 2>/dev/null
mv developer_a_task_check.py scripts/developer-a/ 2>/dev/null
mv quick_dev_a_check.py scripts/developer-a/ 2>/dev/null
mv simple_developer_a_check.py scripts/developer-a/ 2>/dev/null

mv dev_a*.sh scripts/developer-a/ 2>/dev/null
mv developer_a*.sh scripts/developer-a/ 2>/dev/null
echo "✅ Developer A scripts moved"

# Move testing scripts
echo "Moving testing scripts..."
mv test_*.py scripts/testing/ 2>/dev/null
echo "✅ Testing scripts moved"

# Move deployment scripts
echo "Moving deployment scripts..."
mv deploy*.sh scripts/deployment/ 2>/dev/null
mv cleanup_now.sh scripts/deployment/ 2>/dev/null
mv enable-pgvector.sh scripts/deployment/ 2>/dev/null
echo "✅ Deployment scripts moved"

# Move utility scripts
echo "Moving utility scripts..."
mv debug_*.py scripts/utils/ 2>/dev/null
mv fix_*.py scripts/utils/ 2>/dev/null
mv run_*.py scripts/utils/ 2>/dev/null
mv health-monitor*.py scripts/utils/ 2>/dev/null
mv reset_user_password.py scripts/utils/ 2>/dev/null
mv run_code_review.py scripts/utils/ 2>/dev/null
mv SPDX-header-inserter.py scripts/utils/ 2>/dev/null
mv eM.py scripts/utils/ 2>/dev/null

mv execute*.sh scripts/utils/ 2>/dev/null
mv TOMORROW_MORNING_COMMANDS.sh scripts/utils/ 2>/dev/null
mv EXECUTE_TAIGA_UPDATE_NOW.sh scripts/utils/ 2>/dev/null
echo "✅ Utility scripts moved"

echo ""
echo "📊 CLEANUP SUMMARY"
echo "=================="
echo "Taiga scripts:      $(ls -1 scripts/taiga/ 2>/dev/null | wc -l)"
echo "Developer A:        $(ls -1 scripts/developer-a/ 2>/dev/null | wc -l)"
echo "Testing scripts:    $(ls -1 scripts/testing/ 2>/dev/null | wc -l)"
echo "Deployment scripts: $(ls -1 scripts/deployment/ 2>/dev/null | wc -l)"
echo "Utility scripts:    $(ls -1 scripts/utils/ 2>/dev/null | wc -l)"
echo ""
echo "Remaining .py/.sh files in root:"
ls -1 *.py *.sh 2>/dev/null | wc -l
echo ""
echo "✅ CLEANUP COMPLETE!"
