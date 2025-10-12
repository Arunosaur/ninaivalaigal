#!/bin/bash
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
# mem0 client wrapper script
# Makes it easier to run the Python client

# Use absolute path to avoid issues with symlinks
cd /Users/asrajag/Workspace/mem0
python3 client/mem0 "$@"
