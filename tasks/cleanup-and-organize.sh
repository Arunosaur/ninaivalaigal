#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Medhasys LLC
#
# Organize tasks folder after Taiga migration
# - Keep active sprint docs as reference
# - Archive old status reports
# - Create clear README

set -euo pipefail

TASKS_DIR="/Users/swami/WorkSpace/ninaivalaigal/tasks"
ARCHIVE_DIR="$TASKS_DIR/archive"
DOCS_DIR="$TASKS_DIR/docs"

echo "📁 Organizing tasks folder..."
echo ""

# Create docs directory for reference documentation
mkdir -p "$DOCS_DIR"

echo "1️⃣  Moving implementation guides to docs/ (these are reference, not tasks)..."

# Keep these as reference documentation
mv -v "$TASKS_DIR/active/DEVELOPER_A_RUST_MIGRATION.md" "$DOCS_DIR/" 2>/dev/null || true
mv -v "$TASKS_DIR/active/DEVELOPER_B_TESTING_DOCS.md" "$DOCS_DIR/" 2>/dev/null || true
mv -v "$TASKS_DIR/active/DEVELOPER_C_PYTHON_SERVICES.md" "$DOCS_DIR/" 2>/dev/null || true
mv -v "$TASKS_DIR/active/SPRINT_OVERVIEW.md" "$DOCS_DIR/" 2>/dev/null || true

echo ""
echo "2️⃣  Archiving old status reports..."

# Archive old status/analysis files
mv -v "$TASKS_DIR/active/DEVELOPER_B_CORRECTED_ANALYSIS.md" "$ARCHIVE_DIR/" 2>/dev/null || true
mv -v "$TASKS_DIR/active/DEVELOPER_B_DATABASE_FIX.md" "$ARCHIVE_DIR/" 2>/dev/null || true
mv -v "$TASKS_DIR/active/FINAL_CORRECTED_SUMMARY.md" "$ARCHIVE_DIR/" 2>/dev/null || true
mv -v "$TASKS_DIR/active/TEAM_STATUS_OCT16.md" "$ARCHIVE_DIR/" 2>/dev/null || true

echo ""
echo "3️⃣  Creating new README for tasks/..."

cat > "$TASKS_DIR/README.md" << 'EOF'
# Tasks Management

**Status**: Migrated to Taiga 🎉

---

## 🌐 Task Tracking

All active tasks are now tracked in **Taiga**:

- **URL**: http://localhost:9000/project/ninaivalaigal
- **Project**: ninaivalaigal
- **Sprint**: Day 2 (Oct 17, 2025)

### Developer Logins
```
developer-a / developer123  (Rust + Go specialist)
developer-b / developer123  (Testing + Docs)
developer-c / developer123  (Python services)
```

---

## 📂 Directory Structure

```
tasks/
├── README.md                    # This file
├── TAIGA_WORKFLOW.md            # How to use Taiga
├── docs/                        # Reference documentation
│   ├── DEVELOPER_A_RUST_MIGRATION.md      # Rust implementation guide
│   ├── DEVELOPER_B_TESTING_DOCS.md        # Testing guide
│   ├── DEVELOPER_C_PYTHON_SERVICES.md     # Python services guide
│   └── SPRINT_OVERVIEW.md                 # 2-week sprint plan
├── archive/                     # Historical documents
│   └── ... (old status reports, completed work)
└── completed/                   # Completed sprint work
    └── YYYYMMDD/ (organized by date)
```

---

## 📋 Current Sprint Tasks (Day 2)

### Developer A (3 tasks)
- #28: Memory Service - Add Redis Caching
- #29: Memory Service - Performance Benchmarks
- #30: Graph/AI Service - Architecture & Setup

### Developer C (4 tasks)
- #31: Core API - User Profile Endpoints
- #32: Core API - Team Management Endpoints
- #33: Core API - Docker Compose Integration
- #34: Business Service - Code Extraction

### Developer B (4 tasks)
- #35: Core API - Documentation
- #39: Core API - Test New Endpoints
- #40: Business Service - Test Preparation
- #41: Memory Service - Integration Testing

**View in Taiga**: http://localhost:9000/project/ninaivalaigal/kanban

---

## 🎯 How to Use

### For Developers
1. Login to Taiga
2. View "My Work" to see your assigned tasks
3. Move tasks through: Ready → In Progress → Done
4. Update task comments with progress
5. Refer to implementation guides in `docs/` folder

### For Managers
1. View project board in Taiga
2. Check task assignments and progress
3. Use docs/ folder for sprint planning reference
4. Archive completed sprint reports to archive/

---

## 📚 Documentation

**Implementation Guides** (in `docs/`):
- Detailed step-by-step guides for each developer
- Week 1-2 sprint breakdown
- Technical specifications
- Code examples and templates

**These are REFERENCE docs, not tasks!**

---

## ✅ Migration Complete

- ✅ Day 2 tasks created in Taiga (Tasks #28-41)
- ✅ Developer accounts created
- ✅ Tasks assigned to developers
- ✅ Implementation guides preserved as reference
- ✅ Old reports archived

**All task tracking now in Taiga!** 🎉
EOF

echo ""
echo "4️⃣  Creating docs/README.md..."

cat > "$DOCS_DIR/README.md" << 'EOF'
# Implementation Reference Documentation

These are **reference guides** for developers, not task lists.

## 📚 Available Guides

### Sprint Planning
- **SPRINT_OVERVIEW.md** - 2-week sprint plan (Oct 16-25)
  - Team assignments
  - Timeline
  - Success criteria
  - Architecture overview

### Developer Guides
- **DEVELOPER_A_RUST_MIGRATION.md**
  - Memory Service (Rust) - Week 1
  - Graph/AI Service (Rust) - Week 2
  - Day-by-day implementation steps
  - Code examples and templates

- **DEVELOPER_B_TESTING_DOCS.md**
  - Testing strategy
  - Documentation standards
  - Test coverage requirements
  - Week 1-2 testing plan

- **DEVELOPER_C_PYTHON_SERVICES.md**
  - Core API extraction
  - Business Service extraction
  - Admin/Vendor Service extraction
  - Docker containerization

## 🎯 How to Use

1. **Taiga** = Where tasks live (what to do)
2. **These docs** = How to implement (detailed instructions)

**Example**:
- Taiga task: "Memory Service - Add Redis Caching"
- This doc: Step-by-step code examples for Redis integration

## ⚠️ Note

These guides were created BEFORE Taiga migration.
Some content may reference old task structures.

**For current tasks, always check Taiga first!**

http://localhost:9000/project/ninaivalaigal
EOF

echo ""
echo "5️⃣  Updating active/README_TEAM_DOCS.md..."

if [ -f "$TASKS_DIR/active/README_TEAM_DOCS.md" ]; then
    mv "$TASKS_DIR/active/README_TEAM_DOCS.md" "$ARCHIVE_DIR/" 2>/dev/null || true
fi

echo ""
echo "6️⃣  Creating MIGRATION_COMPLETE.md status file..."

cat > "$TASKS_DIR/MIGRATION_COMPLETE.md" << 'EOF'
# Task Migration to Taiga - COMPLETE ✅

**Date**: Oct 16, 2025 7:10 PM
**Status**: All active tasks migrated to Taiga

---

## 📊 Migration Summary

### What Was Migrated
- ✅ Day 2 sprint tasks (11 tasks)
- ✅ Developer assignments
- ✅ Task descriptions and acceptance criteria
- ✅ Tags and priorities

### What Was Preserved
- ✅ Implementation guides → `tasks/docs/`
- ✅ Sprint overview → `tasks/docs/`
- ✅ Historical reports → `tasks/archive/`

### What Was Cleaned Up
- Old status reports → archived
- Duplicate/obsolete docs → archived
- Reorganized folder structure

---

## 🌐 Taiga Access

**Project URL**: http://localhost:9000/project/ninaivalaigal

**Developer Accounts**:
- developer-a / developer123 (Rust + Go)
- developer-b / developer123 (Testing + Docs)
- developer-c / developer123 (Python Services)

**Admin**: admin / admin123

---

## 📋 Task Breakdown

### Taiga Tasks (Active)
| Developer | Tasks | Refs |
|-----------|-------|------|
| Developer A | 3 | #28-30 |
| Developer C | 4 | #31-34 |
| Developer B | 4 | #35, #39-41 |
| **Total** | **11** | **Day 2 Sprint** |

### Reference Docs (Not Tasks)
- DEVELOPER_A_RUST_MIGRATION.md
- DEVELOPER_B_TESTING_DOCS.md
- DEVELOPER_C_PYTHON_SERVICES.md
- SPRINT_OVERVIEW.md

---

## ✅ Verification

**Test Taiga Access**:
```bash
# Login as Developer A
curl -X POST http://localhost:9000/api/v1/auth \
  -H "Content-Type: application/json" \
  -d '{"username":"developer-a","password":"developer123","type":"normal"}' | jq .
```

**View Assigned Tasks**:
```bash
# Get Developer A's tasks
TOKEN="<auth_token>"
curl "http://localhost:9000/api/v1/userstories?project=1&assigned_to=6" \
  -H "Authorization: Bearer $TOKEN" | jq '.[] | {ref, subject}'
```

---

## 🎯 Next Steps

1. ✅ Developers login to Taiga
2. ✅ View assigned tasks
3. ✅ Move tasks to "In Progress"
4. ✅ Refer to docs/ for implementation details
5. ✅ Update task status as work progresses

---

**All task tracking now centralized in Taiga!** 🎉
EOF

echo ""
echo "============================================================"
echo "✅ Tasks folder organized!"
echo "============================================================"
echo ""
echo "📂 New Structure:"
echo "   tasks/"
echo "   ├── README.md              (Updated with Taiga info)"
echo "   ├── TAIGA_WORKFLOW.md      (Taiga usage guide)"
echo "   ├── MIGRATION_COMPLETE.md  (This migration report)"
echo "   ├── docs/                  (Reference documentation)"
echo "   │   ├── README.md"
echo "   │   ├── SPRINT_OVERVIEW.md"
echo "   │   ├── DEVELOPER_A_RUST_MIGRATION.md"
echo "   │   ├── DEVELOPER_B_TESTING_DOCS.md"
echo "   │   └── DEVELOPER_C_PYTHON_SERVICES.md"
echo "   ├── archive/               (Historical documents)"
echo "   └── completed/             (Completed work by date)"
echo ""
echo "🌐 All tasks now in Taiga:"
echo "   http://localhost:9000/project/ninaivalaigal"
echo ""
echo "📝 Implementation guides preserved in tasks/docs/"
echo "   (These are reference docs, not tasks)"
echo ""
echo "✅ Cleanup complete!"
