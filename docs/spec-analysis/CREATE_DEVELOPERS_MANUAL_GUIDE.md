# Manual Guide: Creating Developers F, G, H in Taiga

**Date**: January 2025
**Purpose**: Step-by-step guide to manually create Developers F, G, H in Taiga

---

## ⚠️ Why Manual Creation is Required

The Taiga REST API has limitations:
- ❌ POST `/api/v1/users` - Returns 405 "Method not supported"
- ❌ POST `/api/v1/auth/register` - Requires public registration to be enabled (disabled in your instance)
- ✅ Users must be created through the Django admin interface

---

## 📋 Step-by-Step Instructions

### Step 1: Access Taiga Admin Panel

1. **Open your browser** and navigate to:
   ```
   http://localhost:9000/admin/
   ```

2. **Login** with admin credentials:
   - Username: `admin` (or your admin username)
   - Password: (your admin password)

### Step 2: Navigate to Users Section

1. In the Django admin panel, find the **"Users"** section
2. Click on **"Users"** (or `http://localhost:9000/admin/users/user/`)

### Step 3: Create Developer F

1. Click **"Add user"** button (top right)
2. Fill in the form:

   **User Information**:
   - Username: `developer-f`
   - Full name: `Developer F`
   - Email address: `developer-f@example.com`

   **Permissions**:
   - ✅ Active (check this box - IMPORTANT)
   - ❌ Staff status (leave unchecked)
   - ❌ Superuser status (leave unchecked)

   **Password**:
   - Click "This form" under "Password"
   - Password: `changeme123` (temporary - user should change on first login)
   - Confirm password: `changeme123`

3. Click **"Save"** button

### Step 4: Create Developer G

Repeat Step 3 with:
- Username: `developer-g`
- Full name: `Developer G`
- Email address: `developer-g@example.com`
- Password: `changeme123`
- ✅ Active: checked

### Step 5: Create Developer H

Repeat Step 3 with:
- Username: `developer-h`
- Full name: `Developer H`
- Email address: `developer-h@example.com`
- Password: `changeme123`
- ✅ Active: checked

---

## ✅ Verification

After creating all three developers, verify they were created:

1. **Check User List**:
   - Go back to: `http://localhost:9000/admin/users/user/`
   - You should see all three developers listed
   - Verify they show as "Active"

2. **Verify via Script**:
   ```bash
   python3 scripts/create_developers_via_admin.py
   ```

   This will check if the users exist and show their status.

---

## 🔄 Next Steps (After Creation)

Once developers are created, you have two options:

### Option A: Automatic Assignment (Recommended)

Run the assignment script to assign SPEC-055 stories:
```bash
python3 scripts/assign_spec055_stories_to_developers.py
```

This will automatically assign:
- **Developer F**: US#525, US#528
- **Developer G**: US#526
- **Developer H**: US#527

### Option B: Manual Assignment via UI

1. Navigate to: `http://localhost:9000/project/ninaivalaigal/backlog`
2. Filter by tag: `SPEC-055`
3. Open each story and assign:
   - US#525 → Developer F
   - US#526 → Developer G
   - US#527 → Developer H
   - US#528 → Developer F

---

## 📋 Quick Reference Table

| Developer | Username | Email | Password |
|-----------|----------|-------|----------|
| Developer F | `developer-f` | `developer-f@example.com` | `changeme123` |
| Developer G | `developer-g` | `developer-g@example.com` | `changeme123` |
| Developer H | `developer-h` | `developer-h@example.com` | `changeme123` |

---

## 🎯 Summary

**Status**: Manual creation required via Django admin
**Location**: `http://localhost:9000/admin/users/user/`
**Time Required**: ~5 minutes
**After Creation**: Run assignment script or assign manually

---

**Note**: All passwords are temporary and should be changed by users on first login.
