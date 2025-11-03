# 🌐 External Teams Guide

## ✅ **External Teams Are Fully Supported!**

External teams allow **individual users** to form teams **without needing an organization**. Perfect for:
- 🔓 **Open source projects**
- 👥 **Freelancer collaborations**
- 📚 **Study groups**
- 🏘️ **Community projects**
- 🎨 **Creative collaborations**

---

## **What Are External Teams?**

### **Three Types of Teams**

| Type | Description | Example Use Cases |
|------|-------------|-------------------|
| **Internal** | Teams within an organization | Company departments, project teams |
| **External** | Independent teams (no org) | Open source contributors, freelancers |
| **Shared** | Cross-organization teams | Partner collaborations, joint ventures |

### **External Team Characteristics**

- ✅ **No organization required** - Any individual user can create them
- ✅ **Independent governance** - Not tied to corporate structure
- ✅ **Flexible membership** - Invite anyone, regardless of organization
- ✅ **Full feature access** - Same capabilities as internal teams
- ✅ **Clear differentiation** - Flagged as `governance_type: "external"`

---

## **How to Create External Teams**

### **Option 1: Dedicated External Team Endpoint (Recommended)**

```bash
# Create external team
curl -X POST http://localhost:13390/teams/external \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "OpenMem Contributors",
    "description": "Core contributors to the OpenMem open source project",
    "purpose": "open-source",
    "is_public": true
  }'
```

**Response:**
```json
{
  "id": "uuid-here",
  "name": "OpenMem Contributors",
  "organization_id": null,
  "description": "Core contributors to the OpenMem open source project",
  "governance_type": "external",
  "origin": "native",
  "status": "active",
  "member_count": 1,
  "is_external": true,
  "created_at": "2025-10-28T20:00:00Z",
  "updated_at": "2025-10-28T20:00:00Z"
}
```

### **Option 2: General Team Creation Endpoint**

```bash
# Create team without organization
curl -X POST http://localhost:13390/teams \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Freelance Design Team",
    "description": "Collaborative design projects",
    "organization_id": null,
    "governance_type": "external"
  }'
```

---

## **API Endpoints**

### **POST /teams/external** (Dedicated for External Teams)

**Request Body:**
```json
{
  "name": "string (required, 1-255 chars)",
  "description": "string (optional)",
  "purpose": "string (optional, e.g., open-source, freelance, study-group)",
  "is_public": "boolean (optional, default: false)"
}
```

**Metadata Stored:**
- `purpose` → Saved in `provenance_metadata`
- `is_public` → Controls team visibility

**Auto-Set Fields:**
- `organization_id` → `null`
- `governance_type` → `"external"`
- `origin` → `"native"`
- `status` → `"active"`
- `lead_user_id` → Creator's user ID
- Creator is added as `"owner"` role

---

### **POST /teams** (General Team Creation)

**Request Body:**
```json
{
  "name": "string (required)",
  "description": "string (optional)",
  "organization_id": "uuid | null",
  "governance_type": "internal | external | shared (default: internal)"
}
```

**Behavior:**
- If `organization_id` is `null` and `governance_type` is `"internal"` → Auto-converted to `"external"`
- If `organization_id` is provided → Uses specified `governance_type`

---

### **GET /teams** (List Your Teams)

Returns all teams where you are a member, including external teams.

**Response** includes `is_external` flag:
```json
{
  "id": "uuid",
  "name": "Team Name",
  "governance_type": "external",
  "is_external": true,
  ...
}
```

---

### **GET /teams/{team_id}** (Get Team Details)

Returns full team information including governance metadata.

---

### **PATCH /teams/{team_id}** (Update Team)

Admins and owners can update team name and description.

---

### **DELETE /teams/{team_id}** (Delete Team)

Only owners can delete teams.

---

### **Team Member Management**

All standard team member endpoints work for external teams:
- `GET /teams/{team_id}/members` - List members
- `POST /teams/{team_id}/members` - Add member
- `PATCH /teams/{team_id}/members/{user_id}` - Update member role
- `DELETE /teams/{team_id}/members/{user_id}` - Remove member

---

## **Example Use Cases**

### **1. Open Source Project Team**

```bash
# Create team
curl -X POST http://localhost:13390/teams/external \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Redis Contributors",
    "description": "Core maintainers and contributors to Redis",
    "purpose": "open-source",
    "is_public": true
  }'

# Invite contributors
curl -X POST http://localhost:13390/teams/{team_id}/members \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "contributor-uuid",
    "role": "member"
  }'
```

### **2. Freelance Collaboration**

```bash
# Create team for project-based collaboration
curl -X POST http://localhost:13390/teams/external \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Website Redesign Project",
    "description": "Freelance team for client website redesign",
    "purpose": "freelance",
    "is_public": false
  }'
```

### **3. Study Group**

```bash
# Create study group team
curl -X POST http://localhost:13390/teams/external \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "ML Study Group Fall 2025",
    "description": "Machine Learning study group",
    "purpose": "study-group",
    "is_public": false
  }'
```

---

## **Database Schema**

### **Team Fields**

```sql
-- Key fields for external teams
organization_id         | uuid           | NULL for external teams
governance_type         | varchar(50)    | 'external' for independent teams
origin                  | varchar(50)    | 'native', 'partner', 'acquired'
status                  | varchar(50)    | 'active', 'inactive', 'sunset'
lead_user_id           | uuid           | Team lead/creator
provenance_metadata    | json           | Additional metadata (purpose, etc.)
```

### **Database Constraints**

```sql
-- External teams must have NULL organization_id
CHECK (organization_id IS NOT NULL OR
       origin IN ('native', 'partner'))

-- Valid governance types
CHECK (governance_type IN ('internal', 'external', 'shared'))
```

---

## **Internal vs External Teams Comparison**

| Feature | Internal Teams | External Teams |
|---------|---------------|----------------|
| **Organization** | Required | Not allowed (NULL) |
| **Creator** | Org member | Any individual user |
| **Governance** | Corporate structure | Independent |
| **Membership** | Usually org-restricted | Open to anyone |
| **Billing** | Org-level | Team-level |
| **Purpose** | Business operations | Collaboration, community |
| **Examples** | Sales team, Engineering | Open source, Freelance |

---

## **UI Integration (To Be Implemented)**

### **Dashboard - Create Team Button**

For **individual users** (non-org):
- Show "Create Team" button
- Modal with team name, description, purpose
- Auto-creates as external team

For **organization users**:
- Show "Create Team" button
- Choose: "Internal Team" or "External Team"
- Internal = within org
- External = independent (for side projects)

### **Team List Page**

Display teams with badges:
- 🏢 **Internal** - Blue badge
- 🌐 **External** - Green badge
- 🤝 **Shared** - Purple badge

### **Team Details Page**

Show governance type and metadata:
```
Team: OpenMem Contributors
Type: External Team (Open Source)
Members: 12
Organization: None (Independent)
```

---

## **Current Implementation Status**

### ✅ **Completed**

1. **Database Schema** - All fields exist in database
2. **SQLAlchemy Models** - Updated with governance fields
3. **API Endpoints** - All team endpoints support external teams
4. **Dedicated Endpoint** - `POST /teams/external` for easy creation
5. **Documentation** - Comprehensive guide (this file)

### 🚧 **To Be Implemented**

1. **Frontend UI** - Add "Create Team" button to Dashboard
2. **Team Creation Modal** - Form for creating external teams
3. **Team List UI** - Display external teams with badges
4. **Invitation Flow** - UI for inviting members to external teams

---

## **Testing External Teams**

### **1. Login as Individual User**

```bash
# Use existing individual account (krishna@example.com)
TOKEN="eyJhbGc..."
```

### **2. Create External Team**

```bash
curl -X POST http://localhost:13390/teams/external \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test External Team",
    "description": "Testing external team functionality",
    "purpose": "testing"
  }'
```

### **3. List Your Teams**

```bash
curl -X GET http://localhost:13390/teams \
  -H "Authorization: Bearer $TOKEN"
```

Should show your external team with `is_external: true`

### **4. Invite a Team Member**

```bash
# First, get another user's ID or create one
curl -X POST http://localhost:13390/teams/{team_id}/members \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "other-user-uuid",
    "role": "member"
  }'
```

---

## **FAQ**

### **Q: Can organization members create external teams?**
**A:** Yes! Organization members can create external teams for side projects or community work independent of their organization.

### **Q: Can external teams be upgraded to organizations?**
**A:** Future feature. Teams can be "promoted" to organizations when they grow.

### **Q: Do external teams have different limits?**
**A:** Currently no. Future: different rate limits based on team type.

### **Q: Can I convert an internal team to external?**
**A:** Not directly. Would need to migrate members to a new external team.

### **Q: How do I differentiate in the UI?**
**A:** Use the `is_external` boolean field and `governance_type` string:
```typescript
if (team.is_external) {
  // Show "External Team" badge
}
```

---

## **Summary**

✅ **External teams are fully functional in the API**
✅ **Any individual user can create them**
✅ **Perfect for open source, freelance, study groups**
✅ **Same features as internal teams**
✅ **Clearly differentiated with governance_type field**

**Next step**: Implement the frontend UI to make it easy for users to create and manage external teams! 🚀
