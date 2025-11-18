# Developer F, G, H Setup Instructions

**Date**: January 2025
**Purpose**: Instructions for creating Developers F, G, H in Taiga and assigning SPEC-055 stories

---

## ✅ Stories Created

**4 SPEC-055 stories have been created** in the ninaivalaigal project:

- **US#525**: SPEC-055: Verify MCP Server Modularization (unassigned)
- **US#526**: SPEC-055: Database.py Legacy Cleanup Verification (unassigned)
- **US#527**: SPEC-055: Module Documentation & README Completion (unassigned)
- **US#528**: SPEC-055: Final Modularization Verification & Testing (unassigned)

---

## 👥 Step 1: Create Developers in Taiga UI

### Method 1: Via Taiga Admin Panel (Recommended)

1. **Navigate to Admin Panel**:
   - Go to: `http://localhost:9000/admin/`
   - Login as admin user

2. **Create Users**:
   - Navigate to: `Users` → `Add user`
   - Create the following users:

   **Developer F**:
   - Username: `developer-f`
   - Full name: `Developer F`
   - Email: `developer-f@example.com`
   - Active: ✅ (check box)
   - Superuser: ❌ (unchecked)

   **Developer G**:
   - Username: `developer-g`
   - Full name: `Developer G`
   - Email: `developer-g@example.com`
   - Active: ✅ (check box)
   - Superuser: ❌ (unchecked)

   **Developer H**:
   - Username: `developer-h`
   - Full name: `Developer H`
   - Email: `developer-h@example.com`
   - Active: ✅ (check box)
   - Superuser: ❌ (unchecked)

3. **Set Initial Passwords**:
   - Set temporary passwords (users should change on first login)
   - Recommend: `changeme123`

### Method 2: Via Taiga Registration (If Enabled)

If user registration is enabled:
1. Have each developer register at: `http://localhost:9000/register`
2. Username should match: `developer-f`, `developer-g`, `developer-h`
3. Admin then needs to activate the accounts

---

## 📋 Step 2: Add Developers to ninaivalaigal Project

1. **Navigate to Project**:
   - Go to: `http://localhost:9000/project/ninaivalaigal/settings/members`

2. **Add Members**:
   - Click "Add member"
   - Search for and add:
     - Developer F
     - Developer G
     - Developer H

3. **Set Roles** (as appropriate):
   - Developer role or Contributor role

---

## 🔄 Step 3: Assign Stories to Developers

### Option A: Automated Assignment (Recommended)

Run the assignment script after developers are created:

```bash
python3 scripts/assign_spec055_stories_to_developers.py
```

This will automatically assign:
- **Developer F**: US#525, US#528
- **Developer G**: US#526
- **Developer H**: US#527

### Option B: Manual Assignment via Taiga UI

1. **Navigate to Backlog**:
   - Go to: `http://localhost:9000/project/ninaivalaigal/backlog`

2. **Filter by SPEC-055**:
   - Use tag filter: `SPEC-055`

3. **Assign Each Story**:
   - Open each story
   - Click "Edit"
   - Select assignee:
     - US#525 → Developer F
     - US#526 → Developer G
     - US#527 → Developer H
     - US#528 → Developer F
   - Save

---

## ✅ Verification

After setup, verify:

1. **Developers Exist**:
   ```bash
   python3 -c "
   import requests, os
   # ... check user existence
   "
   ```

2. **Stories Assigned**:
   - Check Taiga backlog: `http://localhost:9000/project/ninaivalaigal/backlog`
   - Filter by tag: `SPEC-055`
   - Verify all 4 stories are assigned

3. **Project Membership**:
   - Verify developers are members of ninaivalaigal project
   - Check: `http://localhost:9000/project/ninaivalaigal/settings/members`

---

## 📋 Story Assignment Summary

| Story | US# | Subject | Assignee |
|-------|-----|---------|----------|
| 1 | 525 | Verify MCP Server Modularization | Developer F |
| 2 | 526 | Database.py Legacy Cleanup Verification | Developer G |
| 3 | 527 | Module Documentation & README Completion | Developer H |
| 4 | 528 | Final Modularization Verification & Testing | Developer F |

---

**Status**: ✅ Stories Created
**Next Action**: Create developers in Taiga UI, then run assignment script




