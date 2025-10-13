#!/bin/bash
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
set -e

NAME=$1
START_SCRIPT=$2

if ! container list | grep -q "$NAME"; then
  echo "[$NAME] not found — recreating..."
  bash "$START_SCRIPT"
else
  echo "[$NAME] restarting..."
  container restart "$NAME"
fi
