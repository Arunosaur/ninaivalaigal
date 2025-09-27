#!/bin/bash

# SPEC Directory Cleanup Script
# This script consolidates duplicate SPEC directories and organizes content

set -e  # Exit on any error

echo "🧹 Starting SPEC Directory Cleanup..."

# Change to project root
cd "$(dirname "$0")/.."

# Phase 1: Remove duplicate directories and merge content

echo "📁 Phase 1: Removing duplicate directories..."

# SPEC-010: Remove duplicate observability directory
if [ -d "specs/010-observability-telemetry" ]; then
    echo "  Removing duplicate 010-observability-telemetry/"
    rm -rf specs/010-observability-telemetry/
fi

# SPEC-037: Merge VS Code integration into terminal CLI
if [ -d "specs/037-vs-code-integration" ]; then
    echo "  Merging VS Code integration into 037-terminal-cli-auto-context/"
    mkdir -p specs/037-terminal-cli-auto-context/vs-code-integration/
    if [ "$(ls -A specs/037-vs-code-integration/)" ]; then
        mv specs/037-vs-code-integration/* specs/037-terminal-cli-auto-context/vs-code-integration/
    fi
    rmdir specs/037-vs-code-integration/
fi

# SPEC-040: Merge feedback system into AI context
if [ -d "specs/040-feedback-loop-system" ]; then
    echo "  Merging feedback system into 040-feedback-loop-ai-context/"
    mkdir -p specs/040-feedback-loop-ai-context/archived/
    if [ "$(ls -A specs/040-feedback-loop-system/)" ]; then
        mv specs/040-feedback-loop-system/* specs/040-feedback-loop-ai-context/archived/
    fi
    rmdir specs/040-feedback-loop-system/
fi

# SPEC-041: Merge visibility sharing into collaboration
if [ -d "specs/041-memory-visibility-sharing" ]; then
    echo "  Merging visibility sharing into 049-memory-sharing-collaboration/"
    mkdir -p specs/049-memory-sharing-collaboration/visibility-sharing/
    if [ "$(ls -A specs/041-memory-visibility-sharing/)" ]; then
        mv specs/041-memory-visibility-sharing/* specs/049-memory-sharing-collaboration/visibility-sharing/
    fi
    rmdir specs/041-memory-visibility-sharing/
fi

# SPEC-042: Merge sync users into team collaboration
if [ -d "specs/042-memory-sync-users-teams" ]; then
    echo "  Merging sync users into 004-team-collaboration/"
    mkdir -p specs/004-team-collaboration/memory-sync/
    if [ "$(ls -A specs/042-memory-sync-users-teams/)" ]; then
        mv specs/042-memory-sync-users-teams/* specs/004-team-collaboration/memory-sync/
    fi
    rmdir specs/042-memory-sync-users-teams/
fi

# SPEC-043: Merge offline capture into snapshot versioning
if [ -d "specs/043-offline-memory-capture" ]; then
    echo "  Merging offline capture into 035-memory-snapshot-versioning/"
    mkdir -p specs/035-memory-snapshot-versioning/offline-capture/
    if [ "$(ls -A specs/043-offline-memory-capture/)" ]; then
        mv specs/043-offline-memory-capture/* specs/035-memory-snapshot-versioning/offline-capture/
    fi
    rmdir specs/043-offline-memory-capture/
fi

# SPEC-044: Merge drift detection into snapshot versioning
if [ -d "specs/044-memory-drift-diff-detection" ]; then
    echo "  Merging drift detection into 035-memory-snapshot-versioning/"
    mkdir -p specs/035-memory-snapshot-versioning/drift-detection/
    if [ "$(ls -A specs/044-memory-drift-diff-detection/)" ]; then
        mv specs/044-memory-drift-diff-detection/* specs/035-memory-snapshot-versioning/drift-detection/
    fi
    rmdir specs/044-memory-drift-diff-detection/
fi

# SPEC-045: Merge export/import into snapshot versioning
if [ -d "specs/045-memory-export-import-merge" ]; then
    echo "  Merging export/import into 035-memory-snapshot-versioning/"
    mkdir -p specs/035-memory-snapshot-versioning/export-import/
    if [ "$(ls -A specs/045-memory-export-import-merge/)" ]; then
        mv specs/045-memory-export-import-merge/* specs/035-memory-snapshot-versioning/export-import/
    fi
    rmdir specs/045-memory-export-import-merge/
fi

echo "📄 Phase 2: Relocating orphaned files..."

# Move orphaned SPEC file to proper directory
if [ -f "specs/SPEC-063-agentic-core-execution-framework.md" ]; then
    echo "  Moving orphaned SPEC-063 file to proper directory"
    mv specs/SPEC-063-agentic-core-execution-framework.md specs/063-agentic-core-execution/
fi

echo "✅ Phase 3: Verification..."

# Count remaining SPEC directories
spec_count=$(find specs/ -maxdepth 1 -type d -name "[0-9]*" | wc -l)
echo "  SPEC directories remaining: $spec_count"

# List any remaining duplicates
echo "  Checking for remaining duplicates..."
duplicates=$(find specs/ -maxdepth 1 -type d -name "[0-9]*" | sed 's/.*\/\([0-9]\{3\}\).*/\1/' | sort | uniq -d)
if [ -n "$duplicates" ]; then
    echo "  ⚠️  Remaining duplicates found: $duplicates"
else
    echo "  ✅ No duplicates found"
fi

echo "🎉 SPEC Directory Cleanup Complete!"
echo "📊 Summary:"
echo "  - Removed duplicate directories"
echo "  - Merged related content"
echo "  - Relocated orphaned files"
echo "  - Total SPEC directories: $spec_count"
