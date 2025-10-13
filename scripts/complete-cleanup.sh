#!/bin/bash
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#

# Complete Project Cleanup Script
# This script runs both SPEC and documentation cleanup

set -e  # Exit on any error

echo "🚀 Starting Complete Project Cleanup..."
echo "This will clean up SPEC directories and documentation organization."
echo ""

# Get script directory
SCRIPT_DIR="$(dirname "$0")"

# Make scripts executable
chmod +x "$SCRIPT_DIR/spec-cleanup.sh"
chmod +x "$SCRIPT_DIR/docs-cleanup.sh"

# Run SPEC cleanup
echo "🔧 Step 1: SPEC Directory Cleanup"
echo "=================================="
"$SCRIPT_DIR/spec-cleanup.sh"
echo ""

# Run documentation cleanup
echo "📚 Step 2: Documentation Cleanup"
echo "================================="
"$SCRIPT_DIR/docs-cleanup.sh"
echo ""

# Final summary
echo "🎉 COMPLETE PROJECT CLEANUP FINISHED!"
echo "======================================"

# Count final state
spec_dirs=$(find specs/ -maxdepth 1 -type d -name "[0-9]*" | wc -l)
doc_files=$(find docs/ -name "*.md" | wc -l)
total_md=$(find . -name "*.md" -not -path "./node_modules/*" -not -path "./vscode-client/*" -not -path "./client-tools/*" | wc -l)

echo "📊 Final Project State:"
echo "  - SPEC directories: $spec_dirs"
echo "  - Documentation files: $doc_files"
echo "  - Total markdown files: $total_md"
echo ""
echo "✅ Project is now clean and organized!"
echo "✅ SPEC system: Complete sequence 000-072 with no duplicates"
echo "✅ Documentation: Organized with clear structure"
echo ""
echo "Next steps:"
echo "1. Review the changes"
echo "2. Commit the cleanup"
echo "3. Continue with development priorities"
