# Quick Guide: Creating Developers F, G, H in Taiga

**Date**: January 2025
**Issue**: Developers F, G, H disappeared or were never created
**Solution**: Manual creation via Django admin

---

## ⚠️ Important Note

**Taiga API does NOT support programmatic user creation**. Users must be created manually through the Django admin interface.

---

## 🚀 Quick Steps

### 1. Open Django Admin Panel

Navigate to: **http://localhost:9000/admin/users/user/**

Login with your admin credentials.

### 2. Create Developer F

1. Click **"Add user"** (top right)
2. Fill in:
   - **Username**: `developer-f`
   - **Full name**: `Developer F`
   - **Email address**: `developer-f@example.com`
   - **Password**: `changeme123` (temporary)
   - **Confirm password**: `changeme123`
   - ✅ **Active** (CHECK THIS BOX - Required!)
   - ❌ Staff status (leave unchecked)
   - ❌ Superuser status (leave unchecked)
3. Click **"Save"**

### 3. Create Developer G

Repeat with:
- **Username**: `developer-g`
- **Full name**: `Developer G`
- **Email**: `developer-g@example.com`
- **Password**: `changeme123`
- ✅ **Active**: checked

### 4. Create Developer H

Repeat with:
- **Username**: `developer-h`
- **Full name**: `Developer H`
- **Email**: `developer-h@example.com`
- **Password**: `changeme123`
- ✅ **Active**: checked

---

## ✅ Verification

After creating all three, verify they exist:

```bash
python3 scripts/create_developers_fgh_guide.py
```

This script will check and report the status of all three developers.

---

## 📋 Quick Reference

| Developer | Username | Email | Password | Active |
|-----------|----------|-------|----------|--------|
| Developer F | `developer-f` | `developer-f@example.com` | `changeme123` | ✅ Yes |
| Developer G | `developer-g` | `developer-g@example.com` | `changeme123` | ✅ Yes |
| Developer H | `developer-h` | `developer-h@example.com` | `changeme123` | ✅ Yes |

---

## 🔍 Why They Might Have Disappeared

Possible reasons:
1. **Not marked as Active** - Inactive users may not appear in some lists
2. **Deleted accidentally** - May have been removed
3. **Never created** - May not have been saved properly

**Solution**: Recreate them following the steps above, ensuring **Active** is checked.

---

## 🎯 Next Steps After Creation

1. **Verify existence**: Run `python3 scripts/create_developers_fgh_guide.py`
2. **Add to project**: Ensure they're members of the `ninaivalaigal` project
3. **Assign stories**: Assign relevant stories to these developers as needed

---

**Note**: All passwords are temporary and should be changed by users on first login.




