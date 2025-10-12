#!/usr/bin/env bash
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
# Organize loose SPEC files into proper directories
# Validates content and merges/moves as appropriate

set -euo pipefail

SPECS_DIR="specs"
BACKUP_DIR="specs/.backup-$(date +%Y%m%d-%H%M%S)"

log() { echo "✓ $*"; }
warn() { echo "⚠️  $*"; }
error() { echo "❌ $*"; exit 1; }

# Create backup
create_backup() {
    log "Creating backup at $BACKUP_DIR"
    mkdir -p "$BACKUP_DIR"
    cp specs/SPEC-*.md "$BACKUP_DIR/" 2>/dev/null || true
}

# Check if directory README has substantial content
is_substantial() {
    local file="$1"
    if [ ! -f "$file" ]; then
        return 1
    fi

    local lines=$(wc -l < "$file")
    local words=$(wc -w < "$file")

    # Substantial if > 50 lines or > 300 words
    [ "$lines" -gt 50 ] || [ "$words" -gt 300 ]
}

# Process a single SPEC
process_spec() {
    local spec_num="$1"
    local loose_file="$2"
    local target_dir="$3"

    log "Processing SPEC-${spec_num}: $(basename "$loose_file")"

    # Check if target directory exists
    if [ ! -d "$target_dir" ]; then
        # Create directory based on loose file name
        local name=$(basename "$loose_file" .md | sed "s/SPEC-${spec_num}-//")
        target_dir="${SPECS_DIR}/${spec_num}-${name}"

        log "  Creating directory: $target_dir"
        mkdir -p "$target_dir"

        log "  Moving file to: $target_dir/README.md"
        mv "$loose_file" "$target_dir/README.md"
        return
    fi

    local dir_readme="$target_dir/README.md"

    # If directory README doesn't exist, just move the file
    if [ ! -f "$dir_readme" ]; then
        log "  No README in directory, moving file"
        mv "$loose_file" "$dir_readme"
        return
    fi

    # Compare content
    local loose_lines=$(wc -l < "$loose_file")
    local dir_lines=$(wc -l < "$dir_readme")
    local loose_size=$(stat -f%z "$loose_file" 2>/dev/null || stat -c%s "$loose_file")
    local dir_size=$(stat -f%z "$dir_readme" 2>/dev/null || stat -c%s "$dir_readme")

    log "  Loose file: $loose_lines lines, $loose_size bytes"
    log "  Dir README: $dir_lines lines, $dir_size bytes"

    # If loose file is substantially larger, it's the authoritative version
    if [ "$loose_lines" -gt $((dir_lines * 2)) ] || [ "$loose_size" -gt $((dir_size * 2)) ]; then
        warn "  Loose file is much larger - treating as authoritative"

        # Backup existing README if it has unique content
        if is_substantial "$dir_readme"; then
            local backup_name="${target_dir}/README.old-$(date +%Y%m%d).md"
            log "  Backing up existing README to: $(basename "$backup_name")"
            cp "$dir_readme" "$backup_name"
        fi

        log "  Replacing with loose file"
        mv "$loose_file" "$dir_readme"
    else
        # Directory README is substantial, keep it
        if is_substantial "$dir_readme"; then
            warn "  Directory README is substantial, archiving loose file"
            local archive_name="${target_dir}/README.loose-$(date +%Y%m%d).md"
            mv "$loose_file" "$archive_name"
            log "  Archived to: $(basename "$archive_name")"
        else
            # Dir README is stub, use loose file
            log "  Directory README is stub, replacing with loose file"
            mv "$loose_file" "$dir_readme"
        fi
    fi
}

# Handle duplicate SPEC numbers
handle_duplicates() {
    log "Checking for duplicate SPEC numbers..."

    # SPEC-084 has two files
    if [ -f "specs/SPEC-084-agentic-ui-testing-framework.md" ] && \
       [ -f "specs/SPEC-084-memory-sharing-architecture.md" ]; then
        warn "SPEC-084 has duplicate files!"
        log "  Keeping agentic-ui as 084"
        log "  Renumbering memory-sharing to 088"

        mkdir -p specs/084-agentic-ui-testing
        mv specs/SPEC-084-agentic-ui-testing-framework.md \
           specs/084-agentic-ui-testing/README.md

        mv specs/SPEC-084-memory-sharing-architecture.md \
           specs/SPEC-088-memory-sharing-architecture.md

        mkdir -p specs/088-memory-sharing
        mv specs/SPEC-088-memory-sharing-architecture.md \
           specs/088-memory-sharing/README.md
    fi

    # SPEC-085 has two files
    if [ -f "specs/SPEC-085-staff-management-system.md" ] && \
       [ -f "specs/SPEC-085-external-ai-memory-api-integration.md" ]; then
        warn "SPEC-085 has duplicate files!"
        log "  Keeping staff-management as 085 (implemented)"
        log "  Renumbering external-ai to 089"

        mkdir -p specs/085-staff-management
        mv specs/SPEC-085-staff-management-system.md \
           specs/085-staff-management/README.md

        mv specs/SPEC-085-external-ai-memory-api-integration.md \
           specs/SPEC-089-external-ai-memory-integration.md

        mkdir -p specs/089-external-ai-memory
        mv specs/SPEC-089-external-ai-memory-integration.md \
           specs/089-external-ai-memory/README.md
    fi
}

# Main processing
main() {
    log "SPEC File Organization Script"
    log "=============================="
    echo ""

    cd "$SPECS_DIR/.." || error "Cannot find specs directory"

    # Create backup first
    create_backup

    # Handle duplicates first
    handle_duplicates

    # Find all loose SPEC files
    local loose_files=(specs/SPEC-*.md)

    if [ ${#loose_files[@]} -eq 0 ]; then
        log "No loose SPEC files found!"
        exit 0
    fi

    log "Found ${#loose_files[@]} loose SPEC files to process"
    echo ""

    # Process each file
    for loose_file in "${loose_files[@]}"; do
        [ -f "$loose_file" ] || continue

        # Extract SPEC number
        local spec_num=$(basename "$loose_file" | grep -oE '^SPEC-[0-9]+' | sed 's/SPEC-//')

        # Find target directory
        local target_dir=$(find specs -maxdepth 1 -type d -name "${spec_num}-*" | head -1)

        process_spec "$spec_num" "$loose_file" "$target_dir"
        echo ""
    done

    log "All loose SPEC files processed!"
    log "Backup saved in: $BACKUP_DIR"
    echo ""
    log "Summary of changes:"
    log "  - Moved authoritative specs to directories"
    log "  - Archived stub READMEs where appropriate"
    log "  - Created new directories for orphaned specs"
    log "  - Renumbered duplicate SPEC numbers (084→088, 085→089)"
}

main "$@"
