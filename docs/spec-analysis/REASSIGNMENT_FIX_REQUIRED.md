# Complete SPEC Stories - Reassignment Fix Required

**Date**: January 2025
**Issue**: Stories were assigned to wrong user (admin/ID 5 instead of Developer C/ID 8)

---

## 🔍 Problem Identified

When we created the Complete SPEC stories, they were assigned to:
- **User ID 5**: "admin" (wrong user)

But they should be assigned to:
- **User ID 8**: "developer-c" / "Developer C" (correct user)

---

## ✅ Current Status

- ✅ **107 Complete SPEC stories created**
- ✅ **All in Done status**
- ✅ **All assigned to User ID 5 (admin)** ← **NEEDS FIX**
- ❌ **Developer C filter shows only 17 stories** (the ones already correctly assigned)

---

## 🔧 Solution

### Option 1: Manual Reassignment via Taiga UI (Recommended)

1. Go to Taiga project backlog
2. Filter by "assigned_to" = admin (or filter by the stories)
3. Select all Complete SPEC stories (they have "SPEC-XXX: Title (Complete)" format)
4. Bulk assign to "Developer C"
5. Verify by filtering by "Developer C" - should show all 107 stories

### Option 2: Via API (Requires Developer C to be Project Member)

If Developer C (ID 8) is already a project member:

```python
# Reassign each story
for story in complete_spec_stories:
    story_id = story.get('id')
    # Get story version
    story_detail = requests.get(f'{API_ENDPOINT}/userstories/{story_id}', headers=headers)
    version = story_detail.json().get('version', 1)

    # Reassign
    patch_data = {
        'assigned_to': 8,  # Developer C
        'version': version
    }
    requests.patch(f'{API_ENDPOINT}/userstories/{story_id}', headers=headers, json=patch_data)
```

**Note**: The API requires Developer C to be a project member. If not, add them via:
- Project Settings > Members > Add Member > "developer-c"

### Option 3: Fix the Script for Future Use

The script `scripts/create_complete_specs_stories.py` has been updated to use:
- `DEVELOPER_C_USERNAME = "developer-c"` (with hyphen, not underscore)

This should now correctly find Developer C (ID 8) instead of admin (ID 5).

---

## 📊 Expected Result

After reassignment:
- Filter by "Developer C" should show **107 Complete SPEC stories**
- All stories should be in "Done" status
- All stories should be assigned to Developer C (ID 8)

---

## 🎯 Quick Fix Steps

1. **In Taiga UI**:
   - Go to backlog
   - Remove "Developer C" filter
   - Search for "Complete" or filter by status "Done"
   - Select all Complete SPEC stories
   - Bulk reassign to "Developer C"

2. **Verify**:
   - Filter by "Developer C"
   - Should see all 107 stories

---

**Status**: ⚠️ Requires manual or API reassignment
**Stories Created**: ✅ 107
**Assignment**: ❌ Needs correction (admin → Developer C)
