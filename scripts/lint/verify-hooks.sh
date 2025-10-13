#!/usr/bin/env bash
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
echo "🔍 Verifying hook coverage by directory..."
for dir in server tests scripts utils; do
  echo "📁 Checking $dir..."
  flake8 $dir --count --select=E9,F63,F7,F82 --show-source --statistics
  echo ""
done
