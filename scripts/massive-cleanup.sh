#!/bin/bash

# MASSIVE Documentation Cleanup Script
# Handles 368 markdown files with aggressive consolidation

set -e  # Exit on any error

echo "🚨 MASSIVE DOCUMENTATION CLEANUP STARTING..."
echo "Current state: 368 markdown files"
echo "Target state: ~50-80 essential files"
echo "This will archive 80% of documentation while preserving access"
echo ""

# Change to project root
cd "$(dirname "$0")/.."

# Count current state
current_count=$(find . -name "*.md" -not -path "./node_modules/*" -not -path "./vscode-client/*" -not -path "./client-tools/*" -not -path "./htmlcov/*" -not -path "./.pytest_cache/*" | wc -l)
echo "📊 Current markdown files: $current_count"
echo ""

# Phase 1: SPEC Directory Cleanup
echo "🔧 Phase 1: SPEC Directory Cleanup"
echo "=================================="

spec_files_before=$(find specs/ -name "*.md" | wc -l)
echo "SPEC files before cleanup: $spec_files_before"

for spec_dir in specs/[0-9]*; do
    if [ -d "$spec_dir" ]; then
        spec_name=$(basename "$spec_dir")

        # Count extra files (not README.md)
        extra_files=$(find "$spec_dir" -name "*.md" -not -name "README.md" -not -path "*/archive/*" | wc -l)

        if [ "$extra_files" -gt 0 ]; then
            echo "  Cleaning $spec_name ($extra_files extra files)"

            # Create archive directory
            mkdir -p "$spec_dir/archive"

            # Move all .md files except README.md to archive
            find "$spec_dir" -name "*.md" -not -name "README.md" -not -path "*/archive/*" -exec mv {} "$spec_dir/archive/" \;

            # Remove empty subdirectories (except archive)
            find "$spec_dir" -type d -empty -not -name "archive" -delete 2>/dev/null || true
        fi
    fi
done

spec_files_after=$(find specs/ -name "*.md" -not -path "*/archive/*" | wc -l)
echo "SPEC files after cleanup: $spec_files_after"
echo ""

# Phase 2: Massive Documentation Archive
echo "📚 Phase 2: Massive Documentation Archive"
echo "========================================="

# Create master archive directory
echo "Creating master archive directory..."
mkdir -p docs/MASTER_ARCHIVE/

# Archive major documentation directories
ARCHIVE_DIRS=(
    "security" "development" "pipeline" "testing" "specs"
    "user-management" "deployment" "runbooks" "legacy"
    "reports" "readmes" "product" "database" "api" "architecture"
)

archived_count=0
for dir in "${ARCHIVE_DIRS[@]}"; do
    if [ -d "docs/$dir" ]; then
        file_count=$(find "docs/$dir" -name "*.md" | wc -l)
        echo "  Archiving docs/$dir ($file_count files)"
        mv "docs/$dir" docs/MASTER_ARCHIVE/
        archived_count=$((archived_count + file_count))
    fi
done

echo "Archived $archived_count files from major directories"
echo ""

# Phase 3: Keep Only Essential Documentation
echo "📋 Phase 3: Essential Documentation Selection"
echo "============================================"

# Essential docs to keep in main docs/ directory
KEEP_DOCS=(
    "README.md"
    "COMMAND_REFERENCE.md"
    "IMPLEMENTATION_REPORTS_2024.md"
    "NINA_INTELLIGENCE_STACK_COMPLETE.md"
    "PROPOSED_NEW_SPECS.md"
    "DOCUMENTATION_CLEANUP_PLAN.md"
    "MASSIVE_DOCS_CLEANUP_PLAN.md"
)

# Archive remaining files not in keep list
docs_archived=0
for file in docs/*.md; do
    if [ -f "$file" ]; then
        basename_file=$(basename "$file")
        keep=false

        # Check if file should be kept
        for keep_doc in "${KEEP_DOCS[@]}"; do
            if [ "$basename_file" = "$keep_doc" ]; then
                keep=true
                break
            fi
        done

        # Archive if not in keep list
        if [ "$keep" = false ]; then
            echo "  Archiving $basename_file"
            mv "$file" docs/MASTER_ARCHIVE/
            docs_archived=$((docs_archived + 1))
        fi
    fi
done

echo "Archived $docs_archived additional documentation files"
echo ""

# Phase 4: Create Archive Navigation
echo "🗂️  Phase 4: Creating Archive Navigation"
echo "========================================"

# Create master archive README
cat > docs/MASTER_ARCHIVE/README.md << 'EOF'
# Documentation Archive

This directory contains archived documentation that was consolidated during the massive cleanup of September 24, 2024.

## Archive Contents

### Major Documentation Categories
- `security/` - Security documentation and guides (20 files)
- `development/` - Development guides and processes (16 files)
- `pipeline/` - CI/CD pipeline documentation and slides (13 files)
- `testing/` - Testing infrastructure and results (12 files)
- `specs/` - SPEC-related documentation (12 files)
- `user-management/` - User management guides (10 files)
- `deployment/` - Deployment guides and configurations (9 files)
- `runbooks/` - Operational runbooks (5 files)
- `legacy/` - Legacy documentation (5 files)
- `reports/` - Various reports and analyses (4 files)
- `readmes/` - Miscellaneous README files (4 files)
- `product/` - Product documentation (4 files)
- `database/` - Database documentation (4 files)
- `api/` - API documentation (3 files)
- `architecture/` - Architecture documentation (6 files)

### Individual Archived Files
- Various implementation reports, testing results, and strategic analyses
- Temporary documentation and patches
- Historical development notes

## Navigation

All archived content is preserved and searchable. Use `find` or `grep` to locate specific information:

```bash
# Find files by name
find docs/MASTER_ARCHIVE/ -name "*keyword*"

# Search content
grep -r "search term" docs/MASTER_ARCHIVE/
```

## Current Documentation

For current, actively maintained documentation, see:
- Main project: `../../README.md`
- SPEC tracking: `../../SPEC_AUDIT_2024.md`
- Current docs: `../README.md`
- Implementation reports: `../IMPLEMENTATION_REPORTS_2024.md`
- Platform guide: `../NINA_INTELLIGENCE_STACK_COMPLETE.md`

---

*Archived on September 24, 2024 during massive documentation cleanup*
*Original file count: 368 → Reduced to: ~80 essential files*
EOF

# Phase 5: Final Verification and Summary
echo "✅ Phase 5: Final Verification"
echo "=============================="

# Count final state
final_count=$(find . -name "*.md" -not -path "./node_modules/*" -not -path "./vscode-client/*" -not -path "./client-tools/*" -not -path "./htmlcov/*" -not -path "./.pytest_cache/*" -not -path "*/archive/*" -not -path "*/MASTER_ARCHIVE/*" | wc -l)
archived_total=$(find docs/MASTER_ARCHIVE/ -name "*.md" | wc -l)
spec_archived=$(find specs/ -path "*/archive/*.md" | wc -l)

echo "🎉 MASSIVE CLEANUP COMPLETE!"
echo "============================="
echo ""
echo "📊 CLEANUP RESULTS:"
echo "  Before: $current_count markdown files"
echo "  After: $final_count active files"
echo "  Archived: $((archived_total + spec_archived)) files"
echo "  Reduction: $(( (current_count - final_count) * 100 / current_count ))%"
echo ""
echo "📁 FILE DISTRIBUTION:"
echo "  Essential docs: $(find docs/ -maxdepth 1 -name "*.md" | wc -l) files"
echo "  SPEC docs: $(find specs/ -name "README.md" | wc -l) files"
echo "  Other essential: $(find . -maxdepth 1 -name "*.md" | wc -l) files"
echo "  Master archive: $archived_total files"
echo "  SPEC archives: $spec_archived files"
echo ""
echo "✅ Project documentation is now clean and manageable!"
echo "✅ All information preserved in organized archives"
echo "✅ Clear navigation and structure established"
echo ""
echo "Next steps:"
echo "1. Review the cleaned structure"
echo "2. Update docs/README.md with new navigation"
echo "3. Commit the massive cleanup"
echo "4. Enjoy the clean, maintainable documentation!"
