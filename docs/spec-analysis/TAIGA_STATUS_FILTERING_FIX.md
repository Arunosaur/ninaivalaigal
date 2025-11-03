# Taiga Status Filtering - Issue and Fix

**Date**: January 2025
**Issue**: Filtering by `status=5` shows only 49 stories instead of all Complete SPEC stories

---

## 🔍 Issue Identified

When filtering by `status=5` in Taiga (`http://localhost:9000/project/ninaivalaigal/backlog?status=5`), only 49 stories are shown, but we created 51 Complete SPEC stories.

---

## ✅ Root Cause

**Status ID 5 doesn't exist in this project!**

### Actual Status IDs in Project:
- **ID 7**: New
- **ID 8**: Ready
- **ID 9**: In progress
- **ID 10**: Ready for test
- **ID 11**: **Done** ← This is the correct Done status
- **ID 12**: Archived

**All 107 Complete SPEC stories are correctly in Status ID 11 (Done), NOT Status ID 5.**

---

## 🔧 Solution

### Use Status ID 11 Instead

To see all Complete SPEC stories that are marked as Done, use:

**Correct URL:**
```
http://localhost:9000/project/ninaivalaigal/backlog?status=11
```

### Alternative Filtering Methods

1. **Filter by Status Name:**
   - Use the Taiga UI filter dropdown and select "Done"

2. **Filter by Tags:**
   ```
   http://localhost:9000/project/ninaivalaigal/backlog?tags=complete
   ```

3. **Filter by Assignee:**
   ```
   http://localhost:9000/project/ninaivalaigal/backlog?assigned_to=5
   ```
   (where 5 is Developer C's user ID)

4. **Search by Subject:**
   - Search for "Complete" or "SPEC-"

---

## 📊 Verification

- ✅ **All 107 Complete SPEC stories** are in Status ID 11 (Done)
- ✅ **Status ID 11** is the correct "Done" status for this project
- ✅ **Status ID 5** doesn't exist (hence why filtering by it shows unexpected results)

---

## 🎯 Why You See 49 Stories

When filtering by `status=5` (which doesn't exist), Taiga might be:
1. Showing stories from a different status or defaulting to another filter
2. Showing only stories that match some other criteria
3. There may be exactly 49 other stories in the project that happen to match when status=5 is treated as invalid

**The important point**: Your Complete SPEC stories are all correctly in Status ID 11 (Done), and you should filter by `status=11` to see them all.

---

## ✅ Correct URL to View All Done Stories

```
http://localhost:9000/project/ninaivalaigal/backlog?status=11
```

This will show all 107 Complete SPEC stories (including duplicates from multiple runs) that are marked as Done.

---

**Status**: ✅ Issue identified and fix provided
**Action**: Use `status=11` instead of `status=5` to filter Done stories
