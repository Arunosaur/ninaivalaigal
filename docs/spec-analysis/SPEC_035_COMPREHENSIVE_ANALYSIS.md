# SPEC-035 Comprehensive Analysis: E2E Simulation Framework vs Memory Snapshot Versioning

**Date**: January 2025
**Status**: ⚠️ Critical Mismatch Detected

---

## 🚨 Critical Finding: SPEC_INDEX.md Mismatch

### Discrepancy Identified

**SPEC_INDEX.md** (Line 86) states:
```
| 035 | E2E Simulation Framework | Planned | Phase 3 |
```

**Actual Directory** (`specs/035-memory-snapshot-versioning/README.md`) states:
```
# SPEC-035: Memory Snapshot & Versioning
Status: 📋 PLANNED
```

**Conclusion**: Another mismatch between SPEC_INDEX.md and the actual SPEC directory.

---

## 🔍 Investigation Results

### SPEC-035 Directory Contents

**Directory**: `specs/035-memory-snapshot-versioning/`
**Title**: Memory Snapshot & Versioning
**Status**: Planned
**Subdirectories**:
1. `drift-detection/` - References SPEC-044 (Memory Drift & Diff Detection)
2. `export-import/` - References SPEC-045 (Memory Export + Import + Merge)
3. `offline-capture/` - References SPEC-043 (Offline Memory Capture)

### E2E Simulation Framework Status

**SPEC_INDEX.md**: Lists SPEC-035 as "E2E Simulation Framework"
**Related**: SPEC-112 is listed as "E2E Tests with Playwright" (Complete, Phase 3)
**Location**: No dedicated SPEC-035 E2E simulation directory found

### Memory Snapshot/Versioning Implementation

**Status**: Partial Implementation Found
- `server/memory_drift_engine.py` - Memory drift detection (references SPEC-044)
- `server/memory_drift_api.py` - API for drift detection and snapshots
- SPEC-044 is listed as "Memory Drift Detection" (Complete, Phase 2B)

---

## 📊 Analysis: What Should SPEC-035 Be?

### Option 1: SPEC-035 = Memory Snapshot & Versioning

**Evidence For**:
- Directory name: `035-memory-snapshot-versioning`
- README title: "Memory Snapshot & Versioning"
- Subdirectories reference related concepts (drift, export/import, offline)

**Evidence Against**:
- SPEC_INDEX.md says "E2E Simulation Framework"
- Subdirectories reference SPEC-043, SPEC-044, SPEC-045 (which have different meanings in SPEC_INDEX.md)
- Memory drift detection already exists (SPEC-044 Complete)

**Recommendation**: SPEC-035 should be corrected to "Memory Snapshot & Versioning" OR needs to be split/reorganized

---

### Option 2: SPEC-035 = E2E Simulation Framework

**Evidence For**:
- SPEC_INDEX.md says "E2E Simulation Framework"
- Could be separate from SPEC-112 (E2E Tests with Playwright)

**Evidence Against**:
- No directory exists for E2E Simulation Framework
- SPEC-112 already covers E2E testing
- Could be duplicate or overlap

**Recommendation**: If SPEC-035 is E2E Simulation, it needs a new directory OR should be merged with SPEC-112

---

## 🔗 Complex Overlap Analysis

### Subdirectory Conflicts

**SPEC-035 subdirectories reference**:
1. **SPEC-043** (drift-detection references it, but SPEC_INDEX.md says SPEC-043 = "Memory ACL System" - Complete)
2. **SPEC-044** (drift-detection references it, SPEC_INDEX.md says SPEC-044 = "Memory Drift Detection" - Complete) ✅ MATCHES
3. **SPEC-045** (export-import references it, but SPEC_INDEX.md says SPEC-045 = "Intelligent Session Management" - Complete)

**Conclusion**: Subdirectory references are misaligned with SPEC_INDEX.md numbering.

### Implementation Status

**Memory Drift Detection**: ✅ Implemented
- `server/memory_drift_engine.py` (references SPEC-044)
- `server/memory_drift_api.py` (has snapshot functionality)
- SPEC-044 is Complete per SPEC_INDEX.md

**Memory Snapshot/Versioning**: 🔄 Partial
- Snapshot functionality exists in drift API
- No dedicated versioning system found

**E2E Simulation Framework**: ❌ Not Found
- No implementation files
- SPEC-112 covers E2E testing

---

## ✅ Recommended Resolution

### Immediate Actions

1. **Fix SPEC_INDEX.md Mismatch** ⚠️ CRITICAL
   - Decision: Is SPEC-035 Memory Snapshot OR E2E Simulation?
   - If Memory Snapshot: Update SPEC_INDEX.md
   - If E2E Simulation: Create new directory or merge with SPEC-112

2. **Resolve Subdirectory Conflicts**
   - Subdirectories reference wrong SPEC numbers
   - Either update references OR reorganize structure

3. **Clarify Relationship with SPEC-044**
   - SPEC-044 (Memory Drift Detection) is Complete
   - SPEC-035 subdirectory references SPEC-044
   - Need to clarify: Is SPEC-035 extension or duplicate?

### Long-term Actions

1. **Create Detailed Specification**
   - If Memory Snapshot: Expand README with requirements
   - If E2E Simulation: Create new specification

2. **Create Taiga Stories** (Once scope clarified)
   - Break down into implementable stories
   - Assign priorities
   - Estimate effort

---

## 📋 SPEC-035 Analysis (Assuming Memory Snapshot)

### Implementation Status

**Status**: Partial (30-40% Complete)
- ✅ Memory drift detection exists (SPEC-044)
- ✅ Snapshot API endpoints exist
- ❌ Versioning system not found
- ❌ Full snapshot/restore workflow missing
- ❌ Export/import functionality incomplete

### Overlap Analysis

**SPEC-044**: Memory Drift Detection - ✅ Complete
- Overlaps with SPEC-035 subdirectory (drift-detection)
- Already implemented

**SPEC-112**: E2E Tests with Playwright - ✅ Complete
- If SPEC-035 is E2E Simulation, this overlaps
- Already implemented

---

## 🎯 Decision Required

**SPEC-035 Identity Crisis**: The SPEC_INDEX.md and directory don't match, and subdirectories reference misaligned SPEC numbers.

**Options**:
1. **SPEC-035 = Memory Snapshot & Versioning** (match directory)
   - Update SPEC_INDEX.md
   - Fix subdirectory SPEC number references
   - Clarify relationship with SPEC-044

2. **SPEC-035 = E2E Simulation Framework** (match SPEC_INDEX.md)
   - Create new directory OR rename existing
   - Clarify relationship with SPEC-112
   - Resolve subdirectory organization

3. **SPEC-035 Should Be Split/Reorganized**
   - Memory Snapshot: Part of SPEC-044 or separate
   - E2E Simulation: Part of SPEC-112 or separate
   - Subdirectories: Move to correct SPEC numbers

**Recommendation**: Choose Option 1 - Update SPEC_INDEX.md to match directory. E2E simulation is covered by SPEC-112. Memory snapshot versioning can extend SPEC-044.

---

**Analysis Completed**: January 2025
**Status**: ⚠️ Mismatch identified - requires resolution
**Action Required**: Decision on SPEC-035 scope before proceeding




