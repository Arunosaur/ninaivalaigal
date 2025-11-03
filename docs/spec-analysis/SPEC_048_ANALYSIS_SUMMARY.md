# SPEC-048 Analysis Summary: Memory Intent Classifier vs Memory Health Monitoring

**Date**: January 2025
**Status**: ⚠️ SPEC_INDEX.md Mismatch - Directory is Correct
**Critical Issue**: SPEC_INDEX lists wrong title, code labels also incorrect

---

## 🎯 Executive Summary

**SPEC-048 Identity**: Mismatch between SPEC_INDEX.md, directory, and code labels
- **SPEC_INDEX.md**: Lists as "Memory Health Monitoring | Complete | Phase 2B" ⚠️ INCORRECT
- **Directory**: Shows "Memory Intent Classifier" (Planned) ✅ CORRECT
- **Actual "Memory Health Monitoring"**: Implemented but mislabeled as "SPEC-042" in code ⚠️ INCORRECT LABEL
- **Memory Intent Classifier**: Not implemented (Planned)

---

## ✅ Verification Results

### SPEC_INDEX.md Status

**Location**: Line 100
**Entry** (Before Correction): `| 048 | Memory Health Monitoring | Complete | Phase 2B |`

**Status**: ⚠️ **INCORRECT**
- Title does not match directory
- "Memory Health Monitoring" exists but is mislabeled in code as "SPEC-042"
- Should be "Memory Intent Classifier | Planned"

**Entry** (After Correction): `| 048 | Memory Intent Classifier | Planned | Phase 3 |`

### Directory Status

**Directory**: `specs/048-memory-intent-classifier/`
- ✅ Directory exists
- ✅ README.md exists
- **Title**: Memory Intent Classifier
- **Status**: Planned (not implemented)

### Implementation Status

**Memory Intent Classifier**: ❌ Not Implemented
- No implementation files found
- No classification pipeline
- No ML/heuristic system
- Status: Planned

**Memory Health Monitoring** (Incorrectly Listed): ✅ Implemented (but mislabeled)
- `server/memory_health_engine.py` (552+ lines) - Mislabeled as "SPEC-042"
- `server/memory_health_api.py` (428+ lines) - Mislabeled as "SPEC-042"
- `server/memory/health_monitor.py` (575+ lines) - Labeled as "SPEC-020"
- Total: 1,552+ lines
- Status: Complete (fully implemented)
- **Issue**: Code labels say "SPEC-042" but SPEC-042 is "Auth-Aware Test Harness"

---

## 📊 Coverage Breakdown

### Memory Intent Classifier (What SPEC-048 Should Be)

| Feature | Status | Notes |
|---------|--------|-------|
| Memory classification pipeline | ❌ Not Implemented | Planned |
| Repetition detection | ❌ Not Implemented | Planned |
| Audio/narrative signal detection | ❌ Not Implemented | Planned |
| CLI feedback suggestions | ❌ Not Implemented | Planned |
| Auto-tagging | ❌ Not Implemented | Planned |

**Coverage**: ❌ 0% - No implementation found

---

## 🔗 Overlap Analysis

### Related SPECs

| SPEC | Title | Status | Relationship |
|------|-------|--------|--------------|
| 046 | Procedural Macro System | Planned | ✅ Related - Classifier would identify procedural macros |
| 047 | Narrative Memory Macros | Planned | ✅ Related - Classifier would identify narrative macros |
| 042 | Auth-Aware Test Harness | In Progress | ⚠️ **Code Label Issue** - Memory health code mislabeled as SPEC-042 |
| 098 | Memory Health & Orphaned Tokens | Planned | ✅ Related - May be where memory health monitoring belongs |
| 020 | Memory Provider Architecture | Complete | ✅ Different - Provider health (different from memory health) |

**Overlap Assessment**:
- **SPEC-046**: ✅ Related - Classifier would identify procedural macros
- **SPEC-047**: ✅ Related - Classifier would identify narrative macros
- **SPEC-042**: ⚠️ **Mislabeled** - Memory health code incorrectly labeled as SPEC-042
- **SPEC-098**: ✅ Related - Memory Health & Orphaned Tokens (may be where health monitoring belongs)
- **SPEC-020**: ✅ Different - Provider health monitoring (different scope)

**Critical Issue**: Memory health implementation is mislabeled as SPEC-042 in code files. SPEC-042 is actually "Auth-Aware Test Harness".

---

## ⚠️ Resolution Required

### SPEC_INDEX.md Correction Needed

**Current Entry** (Line 100 - After Correction):
```
| 048 | Memory Intent Classifier | Planned | Phase 3 |
```

**Previous Entry** (Before Correction):
```
| 048 | Memory Health Monitoring | Complete | Phase 2B |
```

**Rationale**:
- Directory correctly shows "Memory Intent Classifier"
- Memory Health Monitoring exists but is mislabeled in code
- SPEC-048 has no implementation (Planned)

### Code Label Correction Needed

**Files with Incorrect Labels**:
- `server/memory_health_engine.py` - Labeled as "SPEC-042" (should be SPEC-048 or SPEC-098)
- `server/memory_health_api.py` - Labeled as "SPEC-042" (should be SPEC-048 or SPEC-098)

**Issue**: SPEC-042 is actually "Auth-Aware Test Harness" (different feature)

**Recommendation**: Update code labels to correct SPEC number (likely SPEC-048 or SPEC-098)

---

## ✅ Recommendations

### Immediate Actions

1. **Fix SPEC_INDEX.md** ⚠️ CRITICAL
   - ✅ Updated SPEC-048 entry from "Memory Health Monitoring | Complete" to "Memory Intent Classifier | Planned"
   - ✅ Changed phase from "Phase 2B" to "Phase 3"

2. **Fix Code Labels** (Recommended)
   - Update `memory_health_engine.py` and `memory_health_api.py` labels
   - Change from "SPEC-042" to correct SPEC number (verify if SPEC-048 or SPEC-098)
   - SPEC-042 is "Auth-Aware Test Harness" (different feature)

3. **Verify SPEC-098 Relationship** (Recommended)
   - Check if SPEC-098 "Memory Health & Orphaned Tokens" is where health monitoring belongs
   - If yes, update SPEC-098 status to Complete
   - Update code labels to reference SPEC-098

**Action Required**: ✅ SPEC_INDEX.md corrected. Code labels need fixing.

---

## 🎯 Final Status

**SPEC-048** should be **"Memory Intent Classifier"**:
- ✅ SPEC_INDEX.md: Corrected to "Memory Intent Classifier | Planned"
- ✅ Directory: Correctly shows "Memory Intent Classifier" (Planned)
- ❌ Implementation: Not implemented (Planned)
- ⚠️ **Memory Health Monitoring**: Exists but mislabeled in code (should be fixed to correct SPEC number)

**Action Required**: ✅ SPEC_INDEX.md corrected. ⚠️ Code labels need fixing.

---

**Analysis Completed**: January 2025
**Status**: ✅ SPEC_INDEX.md Corrected - Directory is Correct - ⚠️ Code Labels Need Fixing
**Recommendation**: Fix code labels for memory health implementation (currently mislabeled as SPEC-042)
