#!/usr/bin/env bash
echo "🛠️ Running autoflake + isort on all Python files..."
autoflake --remove-unused-variables --in-place --recursive server tests scripts utils
isort server tests scripts utils
echo "✅ Import cleanup complete."
