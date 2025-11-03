# 👥 How to Add Team Members

## ✅ **Teams Page is Now Available!**

A complete Teams UI has been added to make it easy to create teams and manage members.

---

## **Access the Teams Page**

1. **Login** to your account: http://localhost:8101/login
2. **Click "👥 Teams"** in the navigation bar
3. You'll see your teams page!

---

## **Create Your First Team**

### **Step 1: Click "+ Create Team"** button

### **Step 2: Fill in team details**
- **Team Name**: (e.g., "Engineering Team")
- **Description**: (optional description)
- **External Team checkbox**: Check if you want to create an external team (no organization)

### **Step 3: Click "Create Team"**

Your team is created and you're automatically added as the **owner**!

---

## **How to Add Team Members**

### **Method 1: Via UI (Using User ID)**

1. **Select your team** from the left sidebar
2. **Click "+ Add Member"** button
3. **Enter User ID** (UUID format)
4. **Select Role**: Member, Admin, or Viewer
5. **Click "Add Member"**

### **Where to Get User IDs?**

**Option A: From Database**
```bash
container exec ninaivalaigal-dev-db psql -U nina -d ninaivalaigal_dev -c "SELECT id, email, name FROM ag_catalog.users;"
```

**Option B: Create Another User**
- Go to http://localhost:8101/signup
- Sign up a second user
- Get their ID from the database using the query above

---

### **Method 2: Via API (Recommended for Bulk)**

```bash
# Get your JWT token first (from Settings page or localStorage)
TOKEN="your-jwt-token-here"

# Get team ID (from UI or API)
TEAM_ID="your-team-uuid"

# Get user ID to add
USER_ID="user-uuid-to-add"

# Add member to team
curl -X POST http://localhost:13390/teams/${TEAM_ID}/members \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "'${USER_ID}'",
    "role": "member"
  }'
```

---

## **Team Roles Explained**

| Role | Permissions |
|------|-------------|
| **Owner** | Full control, can delete team, cannot be removed |
| **Admin** | Can add/remove members, update team settings |
| **Member** | Can view team and collaborate |
| **Viewer** | Read-only access to team |

---

## **Complete Example Workflow**

### **Step 1: Create Test Users**

```bash
# Create User 1 (will be team owner)
curl -X POST http://localhost:13390/auth/signup/individual \
  -H "Content-Type: application/json" \
  -d '{
    "email": "alice@example.com",
    "password": "SecurePass123!",  # pragma: allowlist secret
    "full_name": "Alice Smith"
  }'

# Create User 2 (will be team member)
curl -X POST http://localhost:13390/auth/signup/individual \
  -H "Content-Type: application/json" \
  -d '{
    "email": "bob@example.com",
    "password": "SecurePass123!",  # pragma: allowlist secret
    "full_name": "Bob Jones"
  }'
```

### **Step 2: Get User IDs**

```bash
container exec ninaivalaigal-dev-db psql -U nina -d ninaivalaigal_dev -c \
  "SELECT id, email, name FROM ag_catalog.users WHERE email IN ('alice@example.com', 'bob@example.com');"
```

Output:
```
                  id                  |       email        |    name
--------------------------------------+--------------------+-------------
 abc123...                            | alice@example.com  | Alice Smith
 def456...                            | bob@example.com    | Bob Jones
```

### **Step 3: Login as Alice (Team Owner)**

1. Go to http://localhost:8101/login
2. Email: `alice@example.com`
3. Password: `SecurePass123!`  <!-- pragma: allowlist secret -->

### **Step 4: Create Team (Via UI)**

1. Click **"👥 Teams"** in navigation
2. Click **"+ Create Team"**
3. Name: "Engineering Team"
4. Description: "Core engineering team"
5. Click **"Create Team"**

### **Step 5: Add Bob as Member (Via UI)**

1. **Select "Engineering Team"** from sidebar
2. Click **"+ Add Member"**
3. **User ID**: Paste Bob's UUID (def456... from Step 2)
4. **Role**: Select "Member"
5. Click **"Add Member"**

**Success!** Bob is now a member of the Engineering Team!

### **Step 6: Verify**

1. You should see Bob listed in the team members
2. Bob can now login and see the team in his Teams page

---

## **UI Features**

### **Teams List (Left Sidebar)**
- Shows all your teams
- Displays member count
- Badge for external teams (🌐 External)

### **Team Details (Right Panel)**
- Team name and description
- Governance type badge
- Member list with roles
- Add member button
- Remove member option (for non-owners)

### **Create Team Modal**
- Team name (required)
- Description (optional)
- External team checkbox (for teams without organization)

### **Add Member Modal**
- User ID input (UUID format)
- Role selector (Member/Admin/Viewer)
- Helper text for finding user IDs

---

## **Quick Database Queries**

### **Find All Users**
```sql
SELECT id, email, name, account_type
FROM ag_catalog.users
ORDER BY created_at DESC;
```

### **Find All Teams**
```sql
SELECT id, name, governance_type, organization_id
FROM ag_catalog.teams;
```

### **Find Team Members**
```sql
SELECT
  tm.id,
  u.name as user_name,
  u.email as user_email,
  tm.role,
  t.name as team_name
FROM public.team_members tm
JOIN ag_catalog.users u ON tm.user_id = u.id
JOIN ag_catalog.teams t ON tm.team_id = t.id;
```

### **Find Your User ID**
```sql
SELECT id, email, name
FROM ag_catalog.users
WHERE email = 'your-email@example.com';
```

---

## **Troubleshooting**

### **"User not found"**
- Make sure the User ID (UUID) is correct
- Check that the user exists in the database
- UUIDs are case-sensitive

### **"Admin access required"**
- Only owners and admins can add members
- Check your role in the team

### **"User is already a team member"**
- The user is already in the team
- Check the member list

### **Can't see Teams in navigation**
- Make sure you're logged in
- Refresh the page
- Check browser console for errors

---

## **API Endpoints Available**

All these endpoints work via the UI, but you can also use them directly:

- **GET** `/teams` - List your teams
- **POST** `/teams` - Create team
- **POST** `/teams/external` - Create external team
- **GET** `/teams/{id}` - Get team details
- **PATCH** `/teams/{id}` - Update team
- **DELETE** `/teams/{id}` - Delete team (owner only)
- **GET** `/teams/{id}/members` - List team members
- **POST** `/teams/{id}/members` - Add member
- **PATCH** `/teams/{id}/members/{userId}` - Update member role
- **DELETE** `/teams/{id}/members/{userId}` - Remove member

---

## **Future Enhancements**

Coming soon:
- 🔍 Search users by email in UI
- ✉️ Email invitations
- 🔗 Invitation links
- 👤 User profile pages with visible IDs
- 📋 Copy user ID to clipboard
- 🎯 Auto-complete for user selection

---

## **Summary**

✅ **Teams UI is fully functional**
✅ **Create teams easily with "+ Create Team" button**
✅ **Add members using User ID**
✅ **Manage roles and permissions**
✅ **Support for both internal and external teams**

**You can now manage teams and team members directly from the UI!** 🎉
