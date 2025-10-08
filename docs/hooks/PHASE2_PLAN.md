# Phase 2 Pre-Commit Hook Restoration - Plan

**Date:** October 8, 2025  
**Status:** In Progress  
**Goal:** Fix all non-critical flake8 warnings in server/

---

## 📊 Current State (Post Phase 1)

### Total Warnings: ~500 (more than estimated 400)

| Priority | Error Code | Count | Description | Difficulty |
|----------|------------|-------|-------------|------------|
| 🔥 HIGH | F401 | 187 | Unused imports | ⚡ Easy (automated) |
| 🔥 HIGH | E501 | 147 | Line too long | 🔧 Medium (review) |
| 🔥 HIGH | E402 | 66 | Import not at top | 🔧 Medium (structural) |
| 🟡 MED | F841 | 37 | Unused variables | ⚡ Easy (automated) |
| 🟡 MED | E712 | 21 | Comparison to True | ⚡ Easy (automated) |
| 🟡 MED | F541 | 17 | f-string no placeholders | ⚡ Easy (automated) |
| 🟢 LOW | F811 | 9 | Redefinition | 🔧 Medium (review) |
| 🟢 LOW | E722 | 9 | Bare except | 🔧 Medium (review) |
| 🟢 LOW | E741 | 5 | Ambiguous var name | ⚡ Easy (rename) |
| 🟢 LOW | F403 | 4 | Star imports | 🔧 Medium (refactor) |
| 🟢 LOW | E731 | 1 | Lambda assignment | ⚡ Easy (def) |

**Note:** Docstring warnings (D103, D101, etc.) are excluded for Phase 2 due to volume.

---

## 🎯 Phase 2 Strategy

### Wave 1: Quick Wins (Automated Fixes)
**Target:** ~280 warnings in 30-60 minutes

1. **F401 - Unused Imports (187)** ⚡
   - Use autoflake to remove
   - Verify with isort
   - Quick validation

2. **E712 - Comparison to True (21)** ⚡
   - Find: `== True` → `is True` or remove
   - Find: `== False` → `is False` or `not`
   - Automated with sed/regex

3. **F541 - f-string Placeholders (17)** ⚡
   - Find: `f"text"` → `"text"`
   - Simple string conversion
   - Automated with sed/regex

4. **E741 - Ambiguous Variable Names (5)** ⚡
   - Rename `l` to `line` or `items`
   - Quick manual fix
   - 5-10 minutes

5. **E731 - Lambda Assignment (1)** ⚡
   - Convert to def function
   - 2 minutes

### Wave 2: Structural Fixes (Manual Review)
**Target:** ~66 warnings in 1-2 hours

6. **E402 - Imports Not at Top (66)** 🔧
   - Move imports to top
   - Handle conditional imports carefully
   - May need try/except patterns

### Wave 3: Code Quality (Review Required)
**Target:** ~147 warnings in 2-3 hours

7. **E501 - Line Too Long (147)** 🔧
   - Break long lines intelligently
   - Preserve readability
   - Use black's line breaking rules

### Wave 4: Cleanup (Manual Review)
**Target:** ~59 warnings in 1-2 hours

8. **F841 - Unused Variables (37)** 🔧
   - Remove or use variables
   - Check if intentionally unused
   - May need `_ = var` pattern

9. **F811 - Redefinitions (9)** 🔧
   - Rename conflicting names
   - Review import conflicts
   - Careful review needed

10. **E722 - Bare Except (9)** 🔧
    - Add specific exception types
    - Use `Exception` if generic needed
    - Important for error handling

11. **F403 - Star Imports (4)** 🔧
    - Replace `from x import *` with explicit
    - List all used imports
    - Good code hygiene

---

## 🚀 Execution Plan

### Session 1: Quick Wins (Current)
- ✅ Create Phase 2 plan
- 🔄 Fix F401 (unused imports) - 187 warnings
- 🔄 Fix E712 (comparison to True) - 21 warnings
- 🔄 Fix F541 (f-string placeholders) - 17 warnings
- 🔄 Fix E741 (ambiguous names) - 5 warnings
- 🔄 Fix E731 (lambda) - 1 warning

**Expected Result:** ~230 warnings fixed in 30-60 minutes

### Session 2: Structural Fixes
- Fix E402 (imports not at top) - 66 warnings
- Validate no regressions

**Expected Result:** ~66 warnings fixed in 1-2 hours

### Session 3: Code Quality
- Fix E501 (line too long) - 147 warnings
- Ensure readability maintained

**Expected Result:** ~147 warnings fixed in 2-3 hours

### Session 4: Final Cleanup
- Fix F841 (unused variables) - 37 warnings
- Fix F811 (redefinitions) - 9 warnings
- Fix E722 (bare except) - 9 warnings
- Fix F403 (star imports) - 4 warnings

**Expected Result:** ~59 warnings fixed in 1-2 hours

---

## 📈 Success Criteria

### Phase 2 Complete When:
- ✅ All F401 unused imports removed
- ✅ All E712 comparisons fixed
- ✅ All F541 f-strings corrected
- ✅ All E741 variable names clear
- ✅ All E731 lambdas converted
- ✅ All E402 imports at top (or documented exceptions)
- ✅ All E501 lines within 100 chars (or documented exceptions)
- ✅ All F841 unused variables removed/used
- ✅ All F811 redefinitions resolved
- ✅ All E722 bare excepts specified
- ✅ All F403 star imports replaced

### Target: <50 total warnings remaining (90% reduction)

---

## 🔍 Validation Commands

```bash
# Check Wave 1 progress
flake8 server/ --select=F401,E712,F541,E741,E731 --exclude="*_backup.py"

# Check Wave 2 progress  
flake8 server/ --select=E402 --exclude="*_backup.py"

# Check Wave 3 progress
flake8 server/ --select=E501 --exclude="*_backup.py"

# Check Wave 4 progress
flake8 server/ --select=F841,F811,E722,F403 --exclude="*_backup.py"

# Full Phase 2 validation
flake8 server/ --exclude="*_backup.py,test_lifecycle.py" --statistics
```

---

## 🎯 Let's Begin!

Starting with Wave 1: Quick Wins - Automated fixes for easy wins!
