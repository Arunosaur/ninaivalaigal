# SPEC DIRECTORY CLEANUP PLAN

**Current State**: 77 SPEC directories with duplicates and inconsistencies  
**Target State**: 73 clean SPEC directories (000-072)  
**Issues Found**: Duplicate directories, inconsistent naming, orphaned files

## 🔍 **DUPLICATE DIRECTORIES IDENTIFIED**

### **SPEC-010 Duplicates**
- `010-observability-and-telemetry/` (4 items) ✅ KEEP
- `010-observability-telemetry/` (1 item) ❌ REMOVE

### **SPEC-037 Duplicates** 
- `037-terminal-cli-auto-context/` (1 item) ✅ KEEP
- `037-vs-code-integration/` (1 item) ❌ MERGE INTO 037

### **SPEC-040 Duplicates**
- `040-feedback-loop-ai-context/` (1 item) ✅ KEEP
- `040-feedback-loop-system/` (1 item) ❌ MERGE INTO 040

### **SPEC-041 Duplicates**
- `041-intelligent-related-memory/` (1 item) ✅ KEEP
- `041-memory-visibility-sharing/` (1 item) ❌ MERGE INTO 049

### **SPEC-042 Duplicates**
- `042-memory-health-orphaned-tokens/` (1 item) ✅ KEEP
- `042-memory-sync-users-teams/` (1 item) ❌ MERGE INTO 004

### **SPEC-043 Duplicates**
- `043-memory-access-control-acl/` (1 item) ✅ KEEP
- `043-offline-memory-capture/` (1 item) ❌ MERGE INTO 035

### **SPEC-044 Duplicates**
- `044-cross-device-session-continuity/` (1 item) ✅ KEEP
- `044-memory-drift-diff-detection/` (1 item) ❌ MERGE INTO 035

### **SPEC-045 Duplicates**
- `045-session-timeout-token-expiry/` (2 items) ✅ KEEP
- `045-memory-export-import-merge/` (1 item) ❌ MERGE INTO 035

## 📁 **ORPHANED FILES**
- `SPEC-063-agentic-core-execution-framework.md` (root level) ❌ MOVE TO 063 directory
- `_external/` directory ❌ REVIEW AND RELOCATE
- `templates/` directory ✅ KEEP (utility directory)

## 🎯 **CLEANUP ACTIONS**

### **Phase 1: Remove Duplicate Directories**
```bash
# Remove duplicate observability directory
rm -rf specs/010-observability-telemetry/

# Merge VS Code integration into terminal CLI
mkdir -p specs/037-terminal-cli-auto-context/vs-code-integration/
mv specs/037-vs-code-integration/* specs/037-terminal-cli-auto-context/vs-code-integration/
rmdir specs/037-vs-code-integration/

# Merge feedback system into AI context
mkdir -p specs/040-feedback-loop-ai-context/archived/
mv specs/040-feedback-loop-system/* specs/040-feedback-loop-ai-context/archived/
rmdir specs/040-feedback-loop-system/

# Merge visibility sharing into collaboration
mkdir -p specs/049-memory-sharing-collaboration/visibility-sharing/
mv specs/041-memory-visibility-sharing/* specs/049-memory-sharing-collaboration/visibility-sharing/
rmdir specs/041-memory-visibility-sharing/

# Merge sync users into team collaboration
mkdir -p specs/004-team-collaboration/memory-sync/
mv specs/042-memory-sync-users-teams/* specs/004-team-collaboration/memory-sync/
rmdir specs/042-memory-sync-users-teams/

# Merge offline capture into snapshot versioning
mkdir -p specs/035-memory-snapshot-versioning/offline-capture/
mv specs/043-offline-memory-capture/* specs/035-memory-snapshot-versioning/offline-capture/
rmdir specs/043-offline-memory-capture/

# Merge drift detection into snapshot versioning
mkdir -p specs/035-memory-snapshot-versioning/drift-detection/
mv specs/044-memory-drift-diff-detection/* specs/035-memory-snapshot-versioning/drift-detection/
rmdir specs/044-memory-drift-diff-detection/

# Merge export/import into snapshot versioning
mkdir -p specs/035-memory-snapshot-versioning/export-import/
mv specs/045-memory-export-import-merge/* specs/035-memory-snapshot-versioning/export-import/
rmdir specs/045-memory-export-import-merge/
```

### **Phase 2: Relocate Orphaned Files**
```bash
# Move orphaned SPEC file to proper directory
mv specs/SPEC-063-agentic-core-execution-framework.md specs/063-agentic-core-execution/

# Review and relocate _external directory
# (Need to examine contents first)
```

### **Phase 3: Standardize Directory Structure**
```bash
# Ensure each SPEC has consistent structure
for spec in specs/[0-9]*; do
  if [ ! -f "$spec/README.md" ]; then
    echo "Missing README.md in $spec"
  fi
done
```

## 📊 **EXPECTED RESULTS**

### **Before Cleanup**
- 77 SPEC directories (with duplicates)
- Inconsistent structure
- Orphaned files
- Confusing navigation

### **After Cleanup**
- 73 clean SPEC directories (000-072)
- Consistent structure (each has README.md)
- No duplicates or orphaned files
- Clear navigation and organization

## 🎯 **TARGET DIRECTORY STRUCTURE**

```
specs/
├── 000-template/README.md
├── 000-vision-and-scope/README.md
├── 001-core-memory-system/README.md
├── 002-multi-user-authentication/
│   ├── README.md
│   └── signup-system/           # Merged from 006-user-signup-system
├── 003-core-api-architecture/README.md
├── 004-team-collaboration/
│   ├── README.md
│   ├── organization-ownership/  # Merged from 008-team-organization
│   └── memory-sync/            # Merged from 042-memory-sync-users-teams
├── 005-admin-dashboard/
│   ├── README.md
│   └── universal-ai-integration/ # Merged from 005-universal-ai-integration
├── ...
├── 035-memory-snapshot-versioning/
│   ├── README.md
│   ├── offline-capture/        # Merged from 043-offline-memory-capture
│   ├── drift-detection/        # Merged from 044-memory-drift-diff-detection
│   └── export-import/          # Merged from 045-memory-export-import-merge
├── 037-terminal-cli-auto-context/
│   ├── README.md
│   └── vs-code-integration/    # Merged from 037-vs-code-integration
├── 040-feedback-loop-ai-context/
│   ├── README.md
│   └── archived/               # Merged from 040-feedback-loop-system
├── 049-memory-sharing-collaboration/
│   ├── README.md
│   └── visibility-sharing/     # Merged from 041-memory-visibility-sharing
├── ...
├── 072-apple-container-cli-integration/README.md
└── templates/                  # Utility directory
```

## 🚀 **IMPLEMENTATION PRIORITY**

1. **High Priority**: Remove obvious duplicates (010, 037, 040-045)
2. **Medium Priority**: Merge related content into proper locations
3. **Low Priority**: Standardize directory structure and documentation

This cleanup will create a clean, navigable SPEC system with no duplicates or confusion.
