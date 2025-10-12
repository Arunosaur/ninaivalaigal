#!/usr/bin/env bash
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
# Get paths for current feature branch without creating anything
# Used by commands that need to find existing feature files

set -e

# Source common functions
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=scripts/common.sh
source "$SCRIPT_DIR/common.sh"

# Get all paths
eval "$(get_feature_paths)"

# Check if on feature branch
check_feature_branch "$CURRENT_BRANCH" || exit 1

# Output paths (don't create anything)
echo "REPO_ROOT: $REPO_ROOT"
echo "BRANCH: $CURRENT_BRANCH"
echo "FEATURE_DIR: $FEATURE_DIR"
echo "FEATURE_SPEC: $FEATURE_SPEC"
echo "IMPL_PLAN: $IMPL_PLAN"
echo "TASKS: $TASKS"
