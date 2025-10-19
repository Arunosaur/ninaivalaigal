#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Medhasys LLC
#
echo "👨‍💻 DEVELOPER A - CHECKING MY TASK ASSIGNMENTS"
echo "=============================================="
echo "Date: $(date)"
echo ""

chmod +x /Users/swami/WorkSpace/ninaivalaigal/developer_a_task_check.py

if command -v python3 &> /dev/null; then
    echo "✅ Python 3 available, running task check..."
    echo ""
    python3 /Users/swami/WorkSpace/ninaivalaigal/developer_a_task_check.py
else
    echo "❌ Python 3 not found"
    exit 1
fi

echo ""
echo "=============================================="
echo "Ready to work on assigned tasks! 🚀"
