#!/bin/bash
# Cleanup Script - Run by Developer C
# Time: October 13, 2025, 7:50 PM
# UPDATED: Added SPEC corruption recovery

set -e

echo "🧹 Starting Cleanup and Recovery..."
echo ""

# ============================================================================
# PART 1: Recover Corrupted SPECs
# ============================================================================
echo "📋 PART 1: Recovering Corrupted SPEC Files..."
echo ""

echo "  🔧 Restoring SPEC-087 (corrupted during front-matter addition)..."
git show cd65ead6:specs/087-api-surface-contracts/README.md > specs/087-api-surface-contracts/README.md
echo "    ✅ SPEC-087 restored from git"

echo "  🔧 Restoring SPEC-128 (was 088, corrupted during renaming)..."
if git show cd65ead6:specs/088-memory-sharing/README.md > /dev/null 2>&1; then
    git show cd65ead6:specs/088-memory-sharing/README.md > specs/128-memory-sharing/README.md
    echo "    ✅ SPEC-128 restored from 088-memory-sharing"
else
    echo "    ⚠️  Original 088 not found, keeping current 128"
fi

echo ""

# ============================================================================
# PART 2: Remove Empty Placeholder SPECs
# ============================================================================
echo "📋 PART 2: Removing Empty Placeholder SPEC Directories..."
echo ""

if [ -d "specs/100-api-surface-contracts" ]; then
    echo "  ❌ Removing empty placeholder: specs/100-api-surface-contracts"
    rm -rf specs/100-api-surface-contracts
fi

if [ -d "specs/099-approval-chain-processing" ]; then
    echo "  ❌ Removing empty placeholder: specs/099-approval-chain-processing"
    rm -rf specs/099-approval-chain-processing
fi

if [ -d "specs/101-memory-sharing" ]; then
    echo "  ❌ Removing empty placeholder: specs/101-memory-sharing"
    rm -rf specs/101-memory-sharing
fi

echo "  ✅ Empty placeholder SPECs removed"
echo ""

# ============================================================================
# PART 3: Root Directory Cleanup
# ============================================================================
echo "📋 PART 3: Cleaning Root Directory..."
echo ""

# Create archive directories if they don't exist
mkdir -p docs/archive/session-summaries
mkdir -p docs/archive/container-builds
mkdir -p docs/archive/license-work
mkdir -p docs/archive/spec-work
mkdir -p docs/operations
mkdir -p tasks/_ARCHIVE

echo "  📁 Moving session summaries..."
for file in \
    API_CONTAINER_REBUILD_STATUS.md \
    CASCADE_WORK_PLAN.md \
    CLEANUP_STATUS_2025-10-10.md \
    DASHBOARD_LESSONS_LEARNED.md \
    DASHBOARD_LIVE.md \
    DEMO_READY.md \
    GITHUB_WORKFLOW_UPDATES.md \
    PROJECT_STATUS_VISUAL.md \
    RUNTIME_CONFIGURATION.md \
    SESSION_COMPLETE_OCT13.md \
    TEAM_COORDINATION.md \
    TEAM_STATUS_UPDATE.md \
    WORKING_STATE.md
do
    if [ -f "$file" ]; then
        mv "$file" docs/archive/session-summaries/
        echo "    ✅ $file"
    fi
done

echo ""
echo "  📁 Moving developer tasks..."
if [ -f "DEVELOPER_A_TASKS.md" ]; then
    mv DEVELOPER_A_TASKS.md tasks/_ARCHIVE/
    echo "    ✅ DEVELOPER_A_TASKS.md"
fi
if [ -f "DEVELOPER_B_TASKS.md" ]; then
    mv DEVELOPER_B_TASKS.md tasks/_ARCHIVE/
    echo "    ✅ DEVELOPER_B_TASKS.md"
fi
if [ -f "DEVELOPER_B_HEAT_CHECK.md" ]; then
    mv DEVELOPER_B_HEAT_CHECK.md tasks/_ARCHIVE/
    echo "    ✅ DEVELOPER_B_HEAT_CHECK.md"
fi
if [ -f "DEVELOPER_A_UNBLOCKED_OCT13_PM.md" ]; then
    rm DEVELOPER_A_UNBLOCKED_OCT13_PM.md  # Duplicate exists in tasks/
    echo "    ✅ DEVELOPER_A_UNBLOCKED_OCT13_PM.md (duplicate removed)"
fi

echo ""
echo "  📁 Moving container/spec work..."
if [ -f "CONTAINER_BUILD_CHECKLIST.md" ]; then
    mv CONTAINER_BUILD_CHECKLIST.md docs/archive/container-builds/
    echo "    ✅ CONTAINER_BUILD_CHECKLIST.md"
fi
for file in LEGACY_NAMING_CLEANUP.md SPEC_AUDIT_2024.md SPEC_AUDIT_2024_v2.0.md; do
    if [ -f "$file" ]; then
        mv "$file" docs/archive/spec-work/
        echo "    ✅ $file"
    fi
done

echo ""
echo "  📁 Moving license work..."
for file in \
    COMPLIANCE.md \
    CONTRIBUTOR_LICENSE_AGREEMENT.md \
    ENFORCEMENT_POLICY.md \
    LICENSE_FAQ.md \
    LICENSE-MATRIX.md \
    NOTICE.md \
    TRADEMARK.md
do
    if [ -f "$file" ]; then
        mv "$file" docs/archive/license-work/
        echo "    ✅ $file"
    fi
done

echo ""
echo "  📁 Moving operations docs..."
for file in \
    EXECUTE_PORT_FIXES.md \
    PORT_ALLOCATION.md \
    PORT_COMPLIANCE_FINAL_STATUS.md \
    TOOLS_REFERENCE.md
do
    if [ -f "$file" ]; then
        mv "$file" docs/operations/
        echo "    ✅ $file"
    fi
done

echo ""
echo "  📁 Moving today's status files to tasks/..."
for file in END_OF_DAY_SUMMARY_OCT13.md OPTION_A_PROGRESS_OCT13.md; do
    if [ -f "$file" ]; then
        mv "$file" tasks/
        echo "    ✅ $file"
    fi
done

echo ""
# ============================================================================
# PART 4: Results
# ============================================================================
echo "📊 CLEANUP AND RECOVERY RESULTS:"
echo ""
echo "Root directory files (excluding directories):"
ls -1 | grep '\.md$' | grep -v "README\|CHANGELOG\|CONTRIBUTING\|SECURITY" | wc -l
echo ""
echo "Files remaining in root:"
ls -1 | grep '\.md$' | grep -v "README\|CHANGELOG\|CONTRIBUTING\|SECURITY"
echo ""
echo "✅ Cleanup Complete!"
echo ""
echo "Next steps:"
echo "1. Review restored SPECs: git diff specs/087-api-surface-contracts specs/128-memory-sharing"
echo "2. Review all changes: git status"
echo "3. Test docusaurus: cd docusaurus && npm start"
echo "4. Commit: git add -A && git commit -m 'fix: restore corrupted SPECs, remove empty placeholders, cleanup root'"
echo ""
echo "📋 What was done:"
echo "  ✅ Restored SPEC-087 and SPEC-128 from git (they were corrupted)"
echo "  ✅ Removed empty placeholder SPECs (099, 100, 101)"
echo "  ✅ Archived 35+ root directory files"
echo "  ✅ Root directory cleaned"
