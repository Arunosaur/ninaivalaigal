# Spec 006: User Signup and Organization Registration System

## Overview

Design a comprehensive signup system that supports three distinct user types:
1. **Individual Users** - Personal memory management without teams
2. **Team Users** - Users who join existing organizations/teams
3. **Organization Creators** - Users who create organizations and manage teams

## Problem Statement

Current system requires manual user ID assignment via environment variables. Need self-service registration that supports:
- Individual developers using mem0 for personal AI context
- Teams wanting shared knowledge bases
- Organizations needing hierarchical memory management

## User Journey Analysis

### Individual User Journey
```
Sign Up → Personal Account → Personal Contexts → Personal Memories
   ↓
Optional: Create Organization Later
```

### Team Member Journey
```
Receive Invite → Sign Up → Join Organization → Access Team Contexts
   ↓
Personal Contexts + Team Contexts + Org Contexts
```

### Organization Creator Journey
```
Sign Up → Create Organization → Invite Team Members → Manage Teams
   ↓
Create Teams → Assign Contexts → Manage Permissions
```

## Memory Architecture Design

### Three-Tier Memory System

#### Tier 1: Personal Memories
- **Scope**: Individual user only
- **Access**: Private to user
- **Use Case**: Personal notes, individual learning, private contexts
- **Examples**: "my-learning-notes", "personal-project-ideas"

#### Tier 2: Team Memories
- **Scope**: Team members within organization
- **Access**: Shared within team
- **Use Case**: Project collaboration, team knowledge sharing
- **Examples**: "frontend-team-standards", "api-design-decisions"

#### Tier 3: Organization Memories
- **Scope**: All organization members
- **Access**: Organization-wide visibility
- **Use Case**: Company standards, policies, cross-team knowledge
- **Examples**: "company-coding-standards", "architecture-principles"

### Memory Hierarchy Resolution
```
Query: "authentication patterns"

Search Order:
1. Personal contexts (user's individual memories)
2. Team contexts (user's team memories)
3. Organization contexts (company-wide memories)
4. Public/shared contexts (if enabled)

Result: Hierarchical list with source attribution
```

## Database Schema Extensions

### User Account Types
```sql
-- Extend users table
ALTER TABLE users ADD COLUMN account_type VARCHAR(20) DEFAULT 'individual';
-- Values: 'individual', 'team_member', 'organization_admin'

ALTER TABLE users ADD COLUMN subscription_tier VARCHAR(20) DEFAULT 'free';
-- Values: 'free', 'pro', 'team', 'enterprise'

ALTER TABLE users ADD COLUMN personal_contexts_limit INTEGER DEFAULT 10;
ALTER TABLE users ADD COLUMN created_via VARCHAR(20) DEFAULT 'signup';
-- Values: 'signup', 'invite', 'admin'
```

### Organization Registration
```sql
-- Organization signup tracking
CREATE TABLE organization_registrations (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER REFERENCES organizations(id),
    creator_user_id INTEGER REFERENCES users(id),
    registration_data JSONB,
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT NOW(),
    activated_at TIMESTAMP
);

-- Invitation system
CREATE TABLE user_invitations (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL,
    organization_id INTEGER REFERENCES organizations(id),
    team_id INTEGER REFERENCES teams(id),
    invited_by INTEGER REFERENCES users(id),
    invitation_token VARCHAR(255) UNIQUE,
    role VARCHAR(50) DEFAULT 'user',
    status VARCHAR(20) DEFAULT 'pending',
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    accepted_at TIMESTAMP
);
```

### Context Scoping
```sql
-- Extend contexts table for proper scoping
ALTER TABLE recording_contexts ADD COLUMN scope VARCHAR(20) DEFAULT 'personal';
-- Values: 'personal', 'team', 'organization', 'public'

ALTER TABLE recording_contexts ADD COLUMN team_id INTEGER REFERENCES teams(id);
ALTER TABLE recording_contexts ADD COLUMN organization_id INTEGER REFERENCES organizations(id);

-- Context sharing permissions
CREATE TABLE context_permissions (
    id SERIAL PRIMARY KEY,
    context_id INTEGER REFERENCES recording_contexts(id),
    user_id INTEGER REFERENCES users(id),
    team_id INTEGER REFERENCES teams(id),
    organization_id INTEGER REFERENCES organizations(id),
    permission_type VARCHAR(20) NOT NULL,
    -- Values: 'read', 'write', 'admin'
    granted_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW()
);
```

## API Design

### Individual User Signup
```http
POST /auth/signup
Content-Type: application/json

{
  "email": "john@example.com",
  "password": "secure_password",
  "name": "John Doe",
  "account_type": "individual"
}

Response: 201 Created
{
  "user_id": 123,
  "email": "john@example.com",
  "account_type": "individual",
  "personal_contexts_limit": 10,
  "jwt_token": "eyJ...",
  "setup_complete": false
}
```

### Organization Registration
```http
POST /auth/signup/organization
Content-Type: application/json

{
  "user": {
    "email": "admin@company.com",
    "password": "secure_password",
    "name": "Jane Smith"
  },
  "organization": {
    "name": "Acme Corp",
    "domain": "acme.com",
    "size": "50-100",
    "industry": "Technology"
  }
}

Response: 201 Created
{
  "user_id": 124,
  "organization_id": 10,
  "role": "organization_admin",
  "jwt_token": "eyJ...",
  "setup_steps": [
    "verify_email",
    "setup_teams",
    "invite_members"
  ]
}
```

### Team Member Invitation
```http
POST /organizations/{org_id}/invitations
Authorization: Bearer {admin_jwt}
Content-Type: application/json

{
  "email": "member@company.com",
  "team_ids": [1, 2],
  "role": "user",
  "message": "Welcome to our development team!"
}

Response: 201 Created
{
  "invitation_id": 456,
  "email": "member@company.com",
  "invitation_url": "https://mem0.app/invite/abc123def456",
  "expires_at": "2024-01-22T10:30:00Z"
}
```

### Accept Invitation
```http
POST /auth/signup/invitation
Content-Type: application/json

{
  "invitation_token": "abc123def456",
  "user": {
    "password": "secure_password",
    "name": "Bob Johnson"
  }
}

Response: 201 Created
{
  "user_id": 125,
  "organization_id": 10,
  "teams": [1, 2],
  "jwt_token": "eyJ...",
  "context_access": {
    "personal": ["personal-contexts"],
    "team": ["team-1-contexts", "team-2-contexts"],
    "organization": ["org-wide-contexts"]
  }
}
```

## Context Management by User Type

### Individual Users
```python
# Personal contexts only
contexts = {
    "personal": [
        "my-learning-journal",
        "side-project-notes",
        "coding-experiments"
    ]
}

# Memory recall: Personal only
recall_hierarchy = ["personal"]
```

### Team Members
```python
# Multi-tier context access
contexts = {
    "personal": [
        "my-notes",
        "personal-experiments"
    ],
    "team": [
        "frontend-team-knowledge",
        "current-sprint-context"
    ],
    "organization": [
        "company-standards",
        "architecture-decisions"
    ]
}

# Memory recall: Personal → Team → Organization
recall_hierarchy = ["personal", "team", "organization"]
```

### Organization Admins
```python
# Full access plus management capabilities
contexts = {
    "personal": ["admin-notes"],
    "team": ["all-team-contexts"],
    "organization": ["all-org-contexts"],
    "admin": ["system-management", "user-analytics"]
}

# Memory recall: All levels plus admin contexts
recall_hierarchy = ["personal", "team", "organization", "admin"]
```

## User Experience Flows

### Individual User Onboarding
1. **Sign Up**: Email/password registration
2. **Email Verification**: Confirm email address
3. **Setup Guide**:
   - Create first personal context
   - Install VS Code extension or CLI
   - Record first memory
4. **Upgrade Path**: Option to create organization later

### Organization Setup
1. **Admin Registration**: Create organization and admin account
2. **Organization Setup**:
   - Configure organization details
   - Set up initial teams
   - Define context sharing policies
3. **Member Invitation**:
   - Bulk invite via CSV or individual invites
   - Custom invitation messages
   - Role assignment
4. **Team Configuration**:
   - Create team structures
   - Assign team contexts
   - Set permissions

### Team Member Onboarding
1. **Receive Invitation**: Email with invitation link
2. **Accept Invitation**: Create account via invitation
3. **Context Discovery**:
   - View available team contexts
   - Access organization knowledge base
   - Set up personal workspace
4. **Integration Setup**: Install tools and configure environment

## Pricing and Limits

### Individual Free Tier
- 10 personal contexts
- 1,000 memories per month
- Basic CCTV recording
- Community support

### Individual Pro Tier ($9/month)
- Unlimited personal contexts
- 10,000 memories per month
- Advanced analytics
- Priority support

### Team Tier ($19/user/month)
- All individual pro features
- Unlimited team contexts
- Organization-wide search
- Admin dashboard
- SSO integration

### Enterprise Tier (Custom)
- All team features
- Advanced security
- Compliance features
- Custom integrations
- Dedicated support

## Implementation Plan

### Phase 1: Individual User Signup (Week 1-2)
- [ ] Basic email/password registration
- [ ] Email verification system
- [ ] Personal context creation
- [ ] Individual user dashboard
- [ ] Free tier limitations

### Phase 2: Organization Registration (Week 3-4)
- [ ] Organization creation flow
- [ ] Admin account setup
- [ ] Basic team management
- [ ] Organization dashboard
- [ ] Billing integration

### Phase 3: Invitation System (Week 5-6)
- [ ] Email invitation system
- [ ] Invitation acceptance flow
- [ ] Team member onboarding
- [ ] Context access management
- [ ] Permission system

### Phase 4: Advanced Features (Week 7-8)
- [ ] Bulk user operations
- [ ] Advanced permission matrix
- [ ] Usage analytics
- [ ] Subscription management
- [ ] Enterprise features

## Security Considerations

### Account Security
- **Password Requirements**: Strong password policies
- **Email Verification**: Required for all accounts
- **Rate Limiting**: Prevent signup abuse
- **CAPTCHA**: Bot protection for registration

### Organization Security
- **Domain Verification**: Verify organization email domains
- **Admin Controls**: Restrict who can invite users
- **Context Isolation**: Ensure proper context boundaries
- **Audit Logging**: Track all organization changes

### Data Privacy
- **Personal Data**: Individual users own their personal contexts
- **Team Data**: Shared ownership within teams
- **Organization Data**: Organization owns team/org contexts
- **Data Export**: Users can export their personal data

## Success Metrics

### User Acquisition
- Individual signups per month
- Organization registrations per month
- Invitation acceptance rate
- User activation rate (first memory recorded)

### User Engagement
- Daily/monthly active users
- Contexts created per user
- Memories recorded per user
- Feature adoption rates

### Business Metrics
- Free to paid conversion rate
- Monthly recurring revenue
- Customer lifetime value
- Churn rate by user type

This comprehensive signup system transforms mem0 from a developer tool into a SaaS platform that serves individual developers, teams, and organizations while maintaining the core "simple like CCTV" philosophy.
