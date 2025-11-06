# Complete Ninaivalaigal Data Model

**Date**: 2025-11-04
**Status**: ✅ Consolidated & Clean

---

## 🏗️ **Entity Relationship Diagram (Text)**

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│     User        │    │   Organization  │    │      Team       │
├─────────────────┤    ├─────────────────┤    ├─────────────────┤
│ id (PK)         │◄──►│ id (PK)         │◄──►│ id (PK)         │
│ username        │    │ name            │    │ name            │
│ email           │    │ description     │    │ description     │
│ name            │    │ domain          │    │ organization_id │
│ password_hash   │    │ settings        │    │ is_standalone   │
│ account_type    │    │ is_active       │    │ upgrade_eligible │
│ subscription_...│    │ created_at      │    │ created_by_user │
│ role            │    │ updated_at      │    │ team_invite_code│
│ created_via     │    └─────────────────┘    │ max_members     │
│ email_verified  │           │                   │ created_at      │
│ verification_...│           │                   │ updated_at      │
│ last_login      │           └───────────────────┤                │
│ is_active       │                               └─────────────────┘
│ created_at      │                                         │
│ updated_at      │                                         │
│ default_role    │                                         │
│ is_system_admin │                                         │
│ standalone_...  │                                         │
└─────────────────┘                                         │
         │                                                   │
         │                                                   │
         ▼                                                   ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ UserInvitation  │    │  TeamMembership │    │ TeamUpgradeHist │
├─────────────────┤    ├─────────────────┤    ├─────────────────┤
│ id (PK)         │    │ id (PK)         │    │ id (PK)         │
│ email           │    │ team_id (FK)    │    │ team_id (FK)    │
│ organization_id │◄──►│ user_id (FK)    │◄──►│ organization_id │
│ team_id (FK)    │    │ role            │    │ upgraded_by_...│
│ invited_by (FK) │    │ joined_at       │    │ upgrade_type    │
│ invitation_token│    │ invited_by_...  │    │ upgrade_data    │
│ role            │    │ status          │    │ upgraded_at     │
│ status          │    │ created_at      │    │ status          │
│ expires_at      │    │ updated_at      │    └─────────────────┘
│ accepted_at     │    └─────────────────┘
│ accepted_by (FK)│             │
│ invitation_msg  │             │
│ created_at      │             ▼
│ updated_at      │    ┌─────────────────┐
└─────────────────┘    │     Memory      │
         │             ├─────────────────┤
         │             │ id (PK)         │
         │             │ user_id (FK)    │
         ▼             │ context_id (FK) │
┌─────────────────┐    │ type            │
│   Context       │    │ source          │
├─────────────────┤    │ data            │
│ id (PK)         │    │ created_at      │
│ owner_id (FK)   │    │ updated_at      │
│ team_id (FK)    │    └─────────────────┘
│ organization_id │             │
│ name            │             │
│ context         │             ▼
│ type            │    ┌─────────────────┐
│ source          │    │ContextPermission│
│ data            │    ├─────────────────┤
│ created_at      │    │ id (PK)         │
│ updated_at      │    │ context_id (FK) │
│ is_active       │    │ user_id (FK)    │
│ is_public       │    │ team_id (FK)    │
│ permissions     │    │ organization_id │
└─────────────────┘    │ permission      │
         │             │ granted_by (FK) │
         │             │ expires_at      │
         ▼             │ created_at      │
┌─────────────────┐    │ updated_at      │
│TeamBilling      │    └─────────────────┘
├─────────────────┤
│ id (PK)         │
│ team_id (FK)    │
│ stripe_cust_id  │
│ subscription_id │
│ plan_type       │
│ status          │
│ current_period_ │
│ trial_end       │
│ cancel_at_period│
│ created_at      │
│ updated_at      │
└─────────────────┘
```

---

## 📋 **Core Models Overview**

### **1. User Model** - `users` table
**Purpose**: Central user authentication and profile management

**Key Fields**:
- `id`, `username`, `email`, `name`, `password_hash`
- `account_type` (individual/team_member/organization_admin)
- `subscription_tier` (free/team/enterprise)
- `role` (user/admin/super_admin)
- `standalone_team_id` (for SPEC-066 standalone teams)

**Relationships**:
- `team_memberships` → TeamMembership
- `owned_contexts` → Context
- `standalone_team` → Team

---

### **2. Organization Model** - `organizations` table
**Purpose**: Multi-tenant organization management

**Key Fields**:
- `id`, `name`, `description`, `domain`, `settings`
- `size`, `industry`, `is_active`

**Relationships**:
- `teams` → Team (org has many teams)
- `contexts` → Context (org contexts)
- `permissions` → ContextPermission

---

### **3. Team Model** - `teams` table
**Purpose**: Collaborative workspace management

**Key Fields**:
- `id`, `name`, `description`, `organization_id`
- **Standalone Team Fields** (SPEC-066):
  - `is_standalone`, `upgrade_eligible`
  - `created_by_user_id`, `team_invite_code`
  - `max_members`

**Relationships**:
- `members` → TeamMembership
- `invitations` → UserInvitation
- `organization` → Organization (optional)

---

### **4. UserInvitation Model** - `user_invitations` table ⭐ **CONSOLIDATED**
**Purpose**: Unified invitation system for both orgs and teams

**Key Fields**:
- `id`, `email`, `invitation_token`, `role`
- **Flexible Targeting**:
  - `organization_id` (for org invitations)
  - `team_id` (for team invitations)
- **Lifecycle Tracking**:
  - `invited_by`, `accepted_by`, `status`
  - `expires_at`, `accepted_at`

**Relationships**:
- `organization` → Organization (if org invite)
- `team` → Team (if team invite)
- `inviter` → User
- `accepted_by_user` → User

---

### **5. TeamMembership Model** - `team_memberships` table ⭐ **CONSOLIDATED**
**Purpose**: Team membership with invitation tracking

**Key Fields**:
- `id`, `team_id`, `user_id`, `role`, `status`
- **Invitation Tracking**: `invited_by_user_id`
- **Unique Constraint**: (team_id, user_id)

**Roles**: admin, contributor, viewer
**Status**: active, inactive, removed

**Relationships**:
- `team` → Team
- `user` → User
- `invited_by` → User

---

### **6. Context Model** - `contexts` table
**Purpose**: Memory organization and sharing containers

**Key Fields**:
- `id`, `name`, `context`, `type`, `source`, `data`
- **Flexible Ownership**:
  - `owner_id` (user-owned)
  - `team_id` (team-owned)
  - `organization_id` (org-owned)
- **Access Control**: `is_public`, `permissions`

**Relationships**:
- `owner` → User
- `team` → Team
- `organization` → Organization
- `permissions` → ContextPermission

---

### **7. ContextPermission Model** - `context_permissions` table
**Purpose**: Granular access control for contexts

**Key Fields**:
- `id`, `context_id`, `permission`, `granted_by`
- **Flexible Grant Target**:
  - `user_id` (direct user permission)
  - `team_id` (team permission)
  - `organization_id` (org permission)
- **Temporal Control**: `expires_at`

**Permissions**: owner, admin, write, read

**Relationships**:
- `context` → Context
- `user`/`team`/`organization` → Grant target
- `granted_by_user` → User (who granted)

---

### **8. Memory Model** - `memories` table
**Purpose**: Individual memory storage within contexts

**Key Fields**:
- `id`, `user_id`, `context_id`, `type`, `source`, `data`
- **Metadata**: `tags`, `metadata`

**Relationships**:
- `user` → User
- `context` → Context

---

### **9. TeamBilling Model** - `team_billing` table
**Purpose**: Team subscription and billing management

**Key Fields**:
- `id`, `team_id`, `stripe_customer_id`, `subscription_id`
- **Plan Details**: `plan_type`, `status`
- **Billing Period**: `current_period_start/end`, `trial_end`
- **Limits**: `members_limit`, `contexts_limit`, `storage_limit_gb`

**Relationships**:
- `team` → Team

---

### **10. TeamUpgradeHistory Model** - `team_upgrade_history` table
**Purpose**: Audit trail for team upgrades

**Key Fields**:
- `id`, `team_id`, `organization_id`, `upgraded_by_user_id`
- **Upgrade Details**: `upgrade_type`, `upgrade_data`, `status`

**Relationships**:
- `team` → Team
- `organization` → Organization
- `upgraded_by` → User

---

## 🔗 **Key Relationship Patterns**

### **Multi-Tenancy Pattern**:
```
Organization (1) ←→ (N) Team (1) ←→ (N) TeamMembership (N) ←→ (1) User
```

### **Context Sharing Pattern**:
```
Context (1) ←→ (N) ContextPermission
Context (1) ←→ (N) Memory
Context ←→ (owner) User
Context ←→ (team) Team
Context ←→ (organization) Organization
```

### **Invitation Flow Pattern**:
```
User (inviter) → UserInvitation → User (invitee)
                         ↓
                    TeamMembership
```

---

## 🎯 **Data Model Strengths**

### **✅ Consolidated & Clean**:
- Single source of truth for invitations (UserInvitation)
- Single source of truth for memberships (TeamMembership)
- No duplicate models

### **✅ Flexible Ownership**:
- Contexts can be owned by users, teams, or organizations
- Permissions can be granted to users, teams, or organizations
- Supports both hierarchical and flat structures

### **✅ Multi-Tenancy Ready**:
- Organization-level isolation
- Team-based collaboration
- Cross-organization teams
- Standalone teams (SPEC-066)

### **✅ Audit & Compliance**:
- Complete invitation lifecycle tracking
- Permission grant tracking
- Upgrade history
- Timestamps on all entities

### **✅ Billing Integration**:
- Stripe integration ready
- Plan-based usage limits
- Trial period support
- Graceful cancellation handling

---

## 📊 **Model Statistics**

- **Total Models**: 10 core models
- **Consolidated Models**: 2 (UserInvitation, TeamMembership)
- **Removed Duplicates**: 2 (TeamInvitation, TeamMember)
- **Relationship Types**: 30+ relationships
- **Index Coverage**: All foreign keys and unique constraints indexed

This consolidated data model provides a robust, scalable foundation for the entire Ninaivalaigal platform!
