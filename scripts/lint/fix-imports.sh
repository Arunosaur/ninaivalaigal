#!/usr/bin/env bash
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
echo "🛠️ Running autoflake + isort on all Python files..."
autoflake --remove-unused-variables --in-place --recursive server tests scripts utils
isort server tests scripts utils
echo "✅ Import cleanup complete."
