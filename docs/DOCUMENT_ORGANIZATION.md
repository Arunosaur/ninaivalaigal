# Document Organization Guide

This document defines where different types of documents should be placed in the repository to maintain clarity and organization.

## 📁 Directory Structure

### `governance/` - Project Governance & Completion Reports
**Purpose**: Project-level governance, completion reports, status summaries, and SPEC audits.

**Use for:**
- ✅ Completion reports for user stories (US#XXX_COMPLETION.md)
- ✅ Implementation status reports
- ✅ SPEC audit reports
- ✅ Governance automation reports
- ✅ Developer work summaries
- ✅ Test result summaries
- ✅ Refactoring completion reports
- ✅ Monthly/quarterly status reports

**Do NOT use for:**
- ❌ Technical documentation (use `docs/`)
- ❌ Task assignments (use `tasks/`)
- ❌ SPEC analysis (use `docs/spec-analysis/`)
- ❌ Code guides (use `docs/guides/`)

**Structure:**
```
governance/
├── README.md                    # Governance overview
└── reports/                     # All completion and status reports
    ├── US117_COMPLETION.md      # User story completion reports
    ├── SPEC_027_028_REFACTORING_COMPLETE.md
    └── SPEC_STATUS_MONTHLY_2025-11.md
```

---

### `docs/` - Technical Documentation
**Purpose**: Technical documentation, guides, architecture docs, and how-to guides.

**Use for:**
- ✅ Architecture documentation
- ✅ API documentation
- ✅ Development guides
- ✅ Testing guides
- ✅ Security documentation
- ✅ Deployment guides
- ✅ SPEC analysis (in `docs/spec-analysis/`)
- ✅ Technical decision documents
- ✅ Troubleshooting guides

**Do NOT use for:**
- ❌ Completion reports (use `governance/reports/`)
- ❌ Task assignments (use `tasks/`)
- ❌ Status updates (use `governance/reports/`)

**Structure:**
```
docs/
├── README.md                    # Documentation index
├── guides/                      # How-to guides
├── architecture/                # Architecture documentation
├── security/                    # Security documentation
├── spec-analysis/               # SPEC analysis documents
├── testing/                     # Testing documentation
└── operations/                  # Operations and runbooks
```

---

### `tasks/` - Task Management & Assignments
**Purpose**: Task assignments, developer tasks, and task-related documentation.

**Use for:**
- ✅ Active task assignments
- ✅ Completed task summaries
- ✅ Developer task documentation
- ✅ Task-specific reports (not completion reports)
- ✅ Task planning documents

**Do NOT use for:**
- ❌ Completion reports for US stories (use `governance/reports/`)
- ❌ SPEC completion reports (use `governance/reports/`)
- ❌ Technical documentation (use `docs/`)

**Structure:**
```
tasks/
├── README.md                    # Task management overview
├── active/                      # Active task assignments
├── completed/                   # Completed task summaries
├── archive/                     # Archived tasks
└── reports/                     # Task-specific reports
```

---

### `reports/` - Root Level Reports
**Purpose**: High-level project reports and summaries.

**Use for:**
- ✅ Executive summaries
- ✅ Quarterly/annual reports
- ✅ Major milestone reports

**Note**: Most reports should go in `governance/reports/`. Only use root `reports/` for very high-level summaries.

---

### `specs/` - SPEC Documentation
**Purpose**: SPEC-specific documentation within each SPEC directory.

**Use for:**
- ✅ SPEC README files
- ✅ SPEC-specific analysis
- ✅ SPEC deprecation notices

**Structure:**
```
specs/
└── XXX-spec-name/
    ├── README.md                # SPEC documentation
    └── DEPRECATION_NOTE.md     # If deprecated
```

---

## 📋 Document Naming Conventions

### Completion Reports
- **Format**: `US{ID}_COMPLETION.md` or `US{ID}_COMPLETION_SUMMARY.md`
- **Location**: `governance/reports/`
- **Example**: `governance/reports/US117_COMPLETION.md`

### Status Reports
- **Format**: `{TOPIC}_STATUS.md` or `{TOPIC}_IMPLEMENTATION_STATUS.md`
- **Location**: `governance/reports/`
- **Example**: `governance/reports/US159_IMPLEMENTATION_STATUS.md`

### SPEC Analysis
- **Format**: `SPEC_{ID}_ANALYSIS.md` or `SPEC_{ID}_COMPREHENSIVE_ANALYSIS.md`
- **Location**: `docs/spec-analysis/`
- **Example**: `docs/spec-analysis/SPEC_027_ANALYSIS_SUMMARY.md`

### Technical Guides
- **Format**: `{TOPIC}_GUIDE.md` or `HOW_TO_{ACTION}.md`
- **Location**: `docs/guides/` or `docs/`
- **Example**: `docs/guides/TENANCY_GUARD_USAGE.md`

---

## 🚫 Common Mistakes

### ❌ Wrong: Completion Report in Root
```
/US117_COMPLETION.md
```
**Should be**: `governance/reports/US117_COMPLETION.md`

### ❌ Wrong: Completion Report in docs/
```
/docs/US117_COMPLETION.md
```
**Should be**: `governance/reports/US117_COMPLETION.md`

### ❌ Wrong: SPEC Analysis in governance/
```
/governance/reports/SPEC_027_ANALYSIS.md
```
**Should be**: `docs/spec-analysis/SPEC_027_ANALYSIS_SUMMARY.md`

### ❌ Wrong: Technical Guide in tasks/
```
/tasks/TENANCY_GUARD_USAGE.md
```
**Should be**: `docs/security/TENANCY_GUARD_USAGE.md`

---

## ✅ Validation

Use the pre-commit hook to validate document placement:
```bash
# Run validation manually
python scripts/validate_document_placement.py
```

---

## 📝 Quick Reference

| Document Type | Location | Example |
|--------------|----------|---------|
| US Completion Report | `governance/reports/` | `US117_COMPLETION.md` |
| SPEC Completion Report | `governance/reports/` | `SPEC_027_028_REFACTORING_COMPLETE.md` |
| SPEC Analysis | `docs/spec-analysis/` | `SPEC_027_ANALYSIS_SUMMARY.md` |
| Technical Guide | `docs/guides/` or `docs/` | `TENANCY_GUARD_USAGE.md` |
| Architecture Doc | `docs/architecture/` | `FRONTEND_ARCHITECTURE_DECISION.md` |
| Task Assignment | `tasks/active/` | `DEVELOPER_A_TASKS.md` |
| Task Completion | `tasks/completed/` | `US101_COMPLETE.md` |
| Security Doc | `docs/security/` | `TENANCY_GUARD_USAGE.md` |

---

**Last Updated**: November 2, 2025
