#!/bin/bash

# Documentation Cleanup Script
# This script consolidates redundant documentation and organizes files

set -e  # Exit on any error

echo "📚 Starting Documentation Cleanup..."

# Change to project root
cd "$(dirname "$0")/.."

# Create archive directory for historical documents
echo "📁 Creating archive directory..."
mkdir -p docs/archive/

# Phase 1: Move redundant implementation reports to archive
echo "🗂️  Phase 1: Archiving redundant implementation reports..."

# Archive multiple SPEC implementation files (keep IMPLEMENTATION_REPORTS_2024.md)
for file in docs/SPEC_*_COMPLETE_IMPLEMENTATION.md docs/SPEC_*_IMPLEMENTATION_SUMMARY.md; do
    if [ -f "$file" ] && [ "$(basename "$file")" != "IMPLEMENTATION_REPORTS_2024.md" ]; then
        echo "  Archiving $(basename "$file")"
        mv "$file" docs/archive/
    fi
done

# Archive testing results (keep essential ones)
for file in docs/*_TESTING_RESULTS.md; do
    if [ -f "$file" ]; then
        echo "  Archiving $(basename "$file")"
        mv "$file" docs/archive/
    fi
done

# Archive strategic analysis documents
strategic_docs=(
    "COMPREHENSIVE_STRATEGIC_ANALYSIS_2024.md"
    "COMPREHENSIVE_GRAPH_INTEGRATION_OPPORTUNITIES.md"
    "COMPREHENSIVE_TESTING_STRATEGY.md"
    "Q4_2025_IMPLEMENTATION_STATUS.md"
    "PHASE_1_2_COMPLETION_REPORT.md"
    "PHASE_3_MODULARIZATION_PROGRESS.md"
)

for doc in "${strategic_docs[@]}"; do
    if [ -f "docs/$doc" ]; then
        echo "  Archiving $doc"
        mv "docs/$doc" docs/archive/
    fi
done

# Phase 2: Archive temporary and patch documentation
echo "🔧 Phase 2: Archiving temporary documentation..."

# Archive README patches and followups
for file in docs/README_*PATCH*.md docs/README_FOLLOWUP*.md docs/PR_*.md; do
    if [ -f "$file" ]; then
        echo "  Archiving $(basename "$file")"
        mv "$file" docs/archive/
    fi
done

# Archive multipart and security patches
for file in docs/MULTIPART_*.md docs/*_PATCH_*.md; do
    if [ -f "$file" ]; then
        echo "  Archiving $(basename "$file")"
        mv "$file" docs/archive/
    fi
done

# Phase 3: Organize remaining documentation
echo "📋 Phase 3: Organizing remaining documentation..."

# Create organized subdirectories
mkdir -p docs/architecture/
mkdir -p docs/deployment/
mkdir -p docs/testing/

# Move architecture documents
arch_docs=(
    "GRAPH_SERVICE_ARCHITECTURE.md"
    "CONTAINER_DEPENDENCY_PROTOCOL.md"
)

for doc in "${arch_docs[@]}"; do
    if [ -f "docs/$doc" ]; then
        echo "  Moving $doc to architecture/"
        mv "docs/$doc" docs/architecture/
    fi
done

# Move deployment documents
deploy_docs=(
    "ARGOCD_TESTING_RESULTS.md"
    "CONTAINER_RELIABILITY_RESOLUTION_COMPLETE.md"
    "PRODUCTION_RELIABILITY_FIX_SUMMARY.md"
)

for doc in "${deploy_docs[@]}"; do
    if [ -f "docs/$doc" ]; then
        echo "  Moving $doc to deployment/"
        mv "docs/$doc" docs/deployment/
    fi
done

# Move testing documents
test_docs=(
    "COMPREHENSIVE_TESTING_INFRASTRUCTURE.md"
    "EXTERNAL_REVIEW_RESULTS.md"
)

for doc in "${test_docs[@]}"; do
    if [ -f "docs/$doc" ]; then
        echo "  Moving $doc to testing/"
        mv "docs/$doc" docs/testing/
    fi
done

# Phase 4: Create README files for new directories
echo "📖 Phase 4: Creating directory README files..."

# Architecture README
cat > docs/architecture/README.md << 'EOF'
# Architecture Documentation

This directory contains architectural documentation for the Nina Intelligence Platform.

## Documents

- `GRAPH_SERVICE_ARCHITECTURE.md` - Graph database service architecture
- `CONTAINER_DEPENDENCY_PROTOCOL.md` - Container dependency management

## Related Documentation

- Main architecture overview: `../NINA_INTELLIGENCE_STACK_COMPLETE.md`
- SPEC documentation: `../../specs/`
EOF

# Deployment README
cat > docs/deployment/README.md << 'EOF'
# Deployment Documentation

This directory contains deployment and operational documentation.

## Documents

- `ARGOCD_TESTING_RESULTS.md` - ArgoCD deployment testing
- `CONTAINER_RELIABILITY_RESOLUTION_COMPLETE.md` - Container reliability fixes
- `PRODUCTION_RELIABILITY_FIX_SUMMARY.md` - Production reliability improvements

## Related Documentation

- Deployment guides: `../../deploy/README.md`
- ArgoCD configuration: `../../argocd/README.md`
EOF

# Testing README
cat > docs/testing/README.md << 'EOF'
# Testing Documentation

This directory contains testing infrastructure and results documentation.

## Documents

- `COMPREHENSIVE_TESTING_INFRASTRUCTURE.md` - Testing framework overview
- `EXTERNAL_REVIEW_RESULTS.md` - External code review results

## Related Documentation

- Test coverage: `../../coverage/README.md`
- SPEC testing: `../../specs/052-comprehensive-test-coverage/`
EOF

# Archive README
cat > docs/archive/README.md << 'EOF'
# Archived Documentation

This directory contains historical documentation that is no longer actively maintained but preserved for reference.

## Contents

- Implementation reports from various development phases
- Testing results from specific features
- Strategic analysis documents
- Temporary patches and fixes
- PR-specific documentation

## Note

These documents are archived for historical reference. For current documentation, see the main `docs/` directory and active SPEC documentation in `specs/`.
EOF

# Phase 5: Final verification
echo "✅ Phase 5: Verification..."

# Count remaining docs
doc_count=$(find docs/ -maxdepth 1 -name "*.md" | wc -l)
archive_count=$(find docs/archive/ -name "*.md" | wc -l)
total_count=$(find docs/ -name "*.md" | wc -l)

echo "🎉 Documentation Cleanup Complete!"
echo "📊 Summary:"
echo "  - Main docs directory: $doc_count files"
echo "  - Archived documents: $archive_count files"
echo "  - Total documentation: $total_count files"
echo "  - Organized into: architecture/, deployment/, testing/, archive/"
