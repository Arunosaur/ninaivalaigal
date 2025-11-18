# SPEC-080 Mismatch Resolution: Offline Mode vs Trust Score System

**Date**: January 2025
**Status**: ⚠️ **MISMATCH IDENTIFIED - NEEDS RESOLUTION**

---

## 🔍 Issue Identified

### Critical Mismatch

**SPEC_INDEX.md Entry**: `| 080 | Offline Mode | Planned | Phase 4 |`
**Directory**: `specs/080-trust-score-system/` ("Trust Score System for Memories")
**Directory README**: "Trust Score System" (trust and reliability scoring)
**Taiga Story**: US#562 "SPEC-080: Offline Mode" - Done

**Assessment**: Title does NOT match directory - Critical mismatch

---

## ✅ Correction: SPEC-043 vs SPEC-080 Analysis

**IMPORTANT**: These are NOT duplicates - they serve completely different purposes:

### SPEC-043: Memory Access Control (ACL) Per Token
- **Status**: ✅ **COMPLETE** (1,249 lines, 10+ API endpoints)
- **Category**: Security / Access Control
- **Purpose**: Controls **WHO** can access memories
- **Key Features**: Token-based permissions, RBAC, visibility levels, sharing controls, audit logging
- **Question**: "Can User A read Memory X based on their role and permissions?"
- **Answer**: Allow/Deny

### SPEC-080: Trust Score System for Memories
- **Status**: 📋 **PLANNED** (directory exists, not implemented)
- **Category**: Memory Intelligence / Quality Control
- **Purpose**: Evaluates **HOW RELIABLE** memories are
- **Key Features**: Multi-factor trust scoring (0-100), source credibility, temporal decay, cross-validation, fact-checking
- **Question**: "How trustworthy is this memory? Should I rely on it for decision-making?"
- **Answer**: Trust Score (0-100)

### Key Differences

| Aspect | SPEC-043 (ACL) | SPEC-080 (Trust Score) |
|--------|---------------|------------------------|
| **Question** | "Can I access this?" | "Should I trust this?" |
| **Focus** | Authorization | Quality/Reliability |
| **Output** | Allow/Deny | Trust Score (0-100) |
| **Factors** | Roles, Permissions, Ownership | Source credibility, Accuracy, Validation |
| **Status** | ✅ Complete | 📋 Planned |
| **Integration** | RBAC, Auth system | ML, Fact-checking, Feedback |

**Relationship**: They are **complementary, not duplicates**:
- SPEC-043 determines if you **CAN** see a memory
- SPEC-080 tells you if you **SHOULD** trust it

---

## 🔍 Actual Issue: SPEC_INDEX.md vs Directory Mismatch

### The Real Problem

**SPEC_INDEX.md**: Lists SPEC-080 as "Offline Mode"
**Directory**: `specs/080-trust-score-system/` contains "Trust Score System"
**Question**: Which one is correct for SPEC-080?

### Evidence

1. **Directory Content**: `specs/080-trust-score-system/README.md`
   - Title: "SPEC-080: Trust Score System for Memories"
   - Status: 📋 PLANNED
   - Purpose: Trust and reliability scoring
   - Category: Memory Intelligence / Quality Control

2. **SPEC_INDEX.md Entry**:
   - `| 080 | Offline Mode | Planned | Phase 4 |`
   - Different purpose: Offline functionality

3. **Taiga Story US#562**:
   - Subject: "SPEC-080: Offline Mode"
   - Status: Done
   - Matches SPEC_INDEX.md, not directory

4. **Offline Mode Reference**:
   - SPEC-141 (Mobile App Support) references "SPEC-080: Offline Mode" as dependency
   - But no `specs/080-offline-mode/` directory exists

### Potential Scenarios

**Scenario A**: SPEC_INDEX.md is wrong, directory is correct
- SPEC-080 should be "Trust Score System"
- "Offline Mode" needs a different SPEC number (or doesn't exist as separate SPEC)
- Update SPEC_INDEX.md and Taiga story US#562

**Scenario B**: Directory is wrong, SPEC_INDEX.md is correct
- SPEC-080 should be "Offline Mode"
- Trust Score System needs a different SPEC number
- Rename directory or move Trust Score System

**Scenario C**: Both exist but SPEC-080 is mislabeled
- Trust Score System should be a different number (e.g., 142)
- SPEC-080 is correctly "Offline Mode" but directory missing
- Create `specs/080-offline-mode/` directory

---

## 📋 Recommendations

### Option 1: Update SPEC_INDEX.md to Match Directory (Recommended if Trust Score is SPEC-080)

1. **Update SPEC_INDEX.md**:
   - Change: `| 080 | Offline Mode | Planned | Phase 4 |`
   - To: `| 080 | Trust Score System | Planned | Phase 4 |`

2. **Update Taiga Story US#562**:
   - Change subject from "SPEC-080: Offline Mode" to "SPEC-080: Trust Score System"
   - Update description to reflect Trust Score System
   - Status should remain "Planned" (not "Done")

3. **Resolve "Offline Mode"**:
   - If needed, create new SPEC for "Offline Mode" (e.g., SPEC-142)
   - Or clarify if offline functionality is covered elsewhere (SPEC-141 mobile apps may handle it)

### Option 2: Update Directory to Match SPEC_INDEX.md (Recommended if Offline Mode is SPEC-080)

1. **Rename/Move Directory**:
   - Move `specs/080-trust-score-system/` to new SPEC number (e.g., `specs/142-trust-score-system/`)
   - Create `specs/080-offline-mode/` directory
   - Create README.md for Offline Mode specification

2. **Update SPEC_INDEX.md**:
   - Keep: `| 080 | Offline Mode | Planned | Phase 4 |`
   - Add: `| 142 | Trust Score System | Planned | Phase 4 |` (or appropriate number)

3. **Update Taiga Story US#562**:
   - Keep subject as "SPEC-080: Offline Mode"
   - Update status to "Ready" or "Planned" (not "Done")
   - Add description for Offline Mode

---

## 🎯 Next Steps

**Action Required**: Determine correct identity of SPEC-080

1. **Verify Intent**: Was SPEC-080 originally intended as:
   - Offline Mode (per SPEC_INDEX.md)?
   - Trust Score System (per directory)?

2. **Check References**:
   - SPEC-141 references "SPEC-080: Offline Mode"
   - Need to verify if this is a hard dependency

3. **Resolve Mismatch**:
   - Update SPEC_INDEX.md to match correct identity
   - Update or create directory accordingly
   - Update Taiga story US#562
   - Update any cross-references

---

**Status**: ⚠️ **MISMATCH IDENTIFIED - AWAITING DECISION**




