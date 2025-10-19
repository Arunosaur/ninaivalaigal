#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Medhasys LLC
#
echo "🚀 Running Task Availability Check"
echo "=================================="

chmod +x /Users/swami/WorkSpace/ninaivalaigal/check_available_tasks.py

# Try to run with python3
if command -v python3 &> /dev/null; then
    echo "✅ Python 3 found, executing task check..."
    python3 /Users/swami/WorkSpace/ninaivalaigal/check_available_tasks.py
else
    echo "❌ Python 3 not found"
    exit 1
fi
