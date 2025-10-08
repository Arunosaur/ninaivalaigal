# SPEC File Organization - Complete

**Date:** 2025-10-08
**Status:** ✅ COMPLETED
**Script:** `scripts/organize-spec-files.sh`

## What Was Done

### 1. Fixed Duplicate SPEC Numbers

**SPEC-084 Conflict (2 different specs, same number):**
- ✅ Kept `agentic-ui-testing-framework` as SPEC-084
- ✅ Renumbered `memory-sharing-architecture` to SPEC-088
- Created: `specs/084-agentic-ui-testing/README.md`
- Created: `specs/088-memory-sharing/README.md`

**SPEC-085 Conflict (2 different specs, same number):**
- ✅ Kept `staff-management-system` as SPEC-085 (implemented in codebase)
- ✅ Renumbered `external-ai-memory-api-integration` to SPEC-089
- Created: `specs/085-staff-management/README.md`
- Created: `specs/089-external-ai-memory/README.md`

### 2. Replaced Stub READMEs with Authoritative Content

Loose files were **much larger** and contained the real specs:

| SPEC | Action | Loose File | Dir README | Decision |
|------|--------|------------|------------|----------|
| 021 | Replaced | 129 lines | 63 lines | Loose file is 2x larger |
| 041 | Replaced | 226 lines | 20 lines | Loose file is 11x larger |
| 042 | Replaced | 265 lines | 39 lines | Loose file is 6x larger |
| 067 | Replaced | 646 lines | 27 lines | Loose file is 24x larger |

**Old stub READMEs backed up as:** `README.old-20251008.md`

### 3. Archived Alternative Versions

These had **substantial** content in both files:

| SPEC | Action | Reason |
|------|--------|--------|
| 022 | Archived loose file | Dir README had 71 lines, substantial content |
| 063 | Archived loose file | Dir README had 55 lines, substantial content |

**Archived files:** `README.loose-20251008.md`

### 4. Created New Directories for Orphaned Files

These specs had **no directory**, so we created them:

- ✅ `specs/083-product-surface-split-and-naming/README.md`
- ✅ `specs/086-multi-runtime-port-allocation/README.md`
- ✅ `specs/087-api-surface-contracts/README.md`
- ✅ `specs/999-regression-prevention-and-stability/README.md`

## Final State

### Clean Structure
- ✅ **0 loose SPEC-*.md files** in `specs/` root
- ✅ **All SPECs in dedicated directories**
- ✅ **No duplicate SPEC numbers**

### New SPEC Numbers Assigned
- **SPEC-088**: Memory Sharing Architecture (was 084)
- **SPEC-089**: External AI Memory Integration (was 085)

### Backups Created
All original files backed up to: `specs/.backup-20251008-120238/`

## Files Affected

**Total files processed:** 14
**Directories created:** 6
**Files moved:** 10
**Files archived:** 2
**Old versions backed up:** 4

## Verification

Run these commands to verify:

```bash
# Should return nothing (no loose files)
ls specs/SPEC-*.md

# Should show new directories
ls -d specs/{083,086,087,088,089,999}-*

# Should show archived versions
find specs -name "README.*.md"
```

## Next Steps

1. ✅ **Review Archived Files** (optional)
   - Check `README.loose-20251008.md` files
   - Check `README.old-20251008.md` files
   - Merge any unique content if needed

2. ✅ **Update SPEC Audit**
   - Update `SPEC_AUDIT_2024_v2.0.md`
   - Note SPEC number changes: 084→088, 085→089
   - Update file path references

3. ✅ **Update Code References**
   - Search for references to old SPEC-084/085 numbers
   - Update to new 088/089 numbers where appropriate

4. ✅ **Commit Changes**
   ```bash
   git add specs/
   git commit -m "refactor(specs): organize loose SPEC files into directories

   - Fixed duplicate SPEC numbers (084→088, 085→089)
   - Replaced stub READMEs with authoritative content
   - Created directories for orphaned specs
   - All specs now in standardized directory structure

   Changes:
   - SPEC-021,041,042,067: Replaced stub READMEs
   - SPEC-022,063: Archived loose versions
   - SPEC-083,086,087,999: Created new directories
   - SPEC-088: Renumbered from 084 (memory-sharing)
   - SPEC-089: Renumbered from 085 (external-ai)

   Backups: specs/.backup-20251008-120238/"
   ```

## Benefits Achieved

1. ✅ **Consistent Organization:** All SPECs follow same structure
2. ✅ **No Confusion:** Single source of truth per SPEC
3. ✅ **No Duplicates:** Each SPEC number is unique
4. ✅ **Easy Discovery:** Standard location for all artifacts
5. ✅ **Version History:** Backups preserved for reference

---

**Result:** Clean, organized SPEC directory structure ready for continued development! 🎉
