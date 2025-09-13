# Memory Architecture for Individual, Team, and Organization Users

## Three-Tier Memory System

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    MEMORY HIERARCHY                         │
├─────────────────────────────────────────────────────────────┤
│  Personal Memories (Private to Individual User)            │
│  ├── my-learning-notes                                     │
│  ├── personal-experiments                                  │
│  └── individual-project-ideas                             │
├─────────────────────────────────────────────────────────────┤
│  Team Memories (Shared within Team)                        │
│  ├── frontend-team-standards                               │
│  ├── current-sprint-context                                │
│  └── team-architecture-decisions                           │
├─────────────────────────────────────────────────────────────┤
│  Organization Memories (Company-wide)                      │
│  ├── company-coding-standards                              │
│  ├── security-policies                                     │
│  └── cross-team-knowledge                                  │
└─────────────────────────────────────────────────────────────┘
```

## User Type Support

### ✅ Individual Users (Personal Memories Only)
**Perfect for**: Solo developers, freelancers, personal AI assistance

**Memory Access**:
- **Personal Contexts**: Unlimited private contexts
- **Team Contexts**: None
- **Organization Contexts**: None

**Use Cases**:
- Personal learning journal
- Side project notes
- Individual coding experiments
- Private AI conversation history

**Example Contexts**:
```json
{
  "personal": [
    "learning-react-hooks",
    "side-project-ideas", 
    "coding-interview-prep",
    "personal-ai-experiments"
  ]
}
```

### ✅ Team Users (Personal + Team + Organization)
**Perfect for**: Employees in organizations with team collaboration

**Memory Access**:
- **Personal Contexts**: Private individual contexts
- **Team Contexts**: Shared with team members
- **Organization Contexts**: Company-wide knowledge

**Use Cases**:
- Personal notes + team collaboration
- Individual learning + team standards
- Private experiments + shared team knowledge

**Example Contexts**:
```json
{
  "personal": [
    "my-learning-notes",
    "personal-experiments"
  ],
  "team": [
    "frontend-team-knowledge",
    "current-sprint-context",
    "team-code-reviews"
  ],
  "organization": [
    "company-standards",
    "architecture-principles",
    "security-guidelines"
  ]
}
```

### ✅ Organization Creators (Full Access + Management)
**Perfect for**: Team leads, CTOs, organization administrators

**Memory Access**:
- **Personal Contexts**: Private admin contexts
- **Team Contexts**: All team contexts (read/write)
- **Organization Contexts**: Full organization knowledge
- **Admin Contexts**: System management and analytics

## Memory Recall Hierarchy

### Individual Users
```python
def recall_memories(query, user_type="individual"):
    search_order = ["personal"]
    
    results = {
        "personal": search_personal_contexts(query, user_id)
    }
    return results
```

### Team Members
```python
def recall_memories(query, user_type="team_member"):
    search_order = ["personal", "team", "organization"]
    
    results = {
        "personal": search_personal_contexts(query, user_id),
        "team": search_team_contexts(query, user_teams),
        "organization": search_org_contexts(query, user_org)
    }
    return results
```

### Organization Admins
```python
def recall_memories(query, user_type="org_admin"):
    search_order = ["personal", "team", "organization", "admin"]
    
    results = {
        "personal": search_personal_contexts(query, user_id),
        "team": search_all_team_contexts(query, organization_id),
        "organization": search_org_contexts(query, organization_id),
        "admin": search_admin_contexts(query, user_id)
    }
    return results
```

## Context Scoping Implementation

### Database Schema
```sql
-- Context scoping
ALTER TABLE recording_contexts ADD COLUMN scope VARCHAR(20) DEFAULT 'personal';
-- Values: 'personal', 'team', 'organization', 'admin'

ALTER TABLE recording_contexts ADD COLUMN visibility VARCHAR(20) DEFAULT 'private';
-- Values: 'private', 'team', 'organization', 'public'

-- Context ownership and access
CREATE TABLE context_access (
    id SERIAL PRIMARY KEY,
    context_id INTEGER REFERENCES recording_contexts(id),
    user_id INTEGER REFERENCES users(id),
    team_id INTEGER REFERENCES teams(id),
    organization_id INTEGER REFERENCES organizations(id),
    access_level VARCHAR(20) NOT NULL,
    -- Values: 'read', 'write', 'admin', 'owner'
    granted_at TIMESTAMP DEFAULT NOW()
);
```

### API Context Creation
```python
# Individual user creates personal context
POST /context/start
{
    "context": "my-learning-notes",
    "scope": "personal",
    "visibility": "private"
}

# Team member creates team context
POST /context/start  
{
    "context": "frontend-team-standards",
    "scope": "team",
    "team_id": 5,
    "visibility": "team"
}

# Organization admin creates org-wide context
POST /context/start
{
    "context": "company-architecture",
    "scope": "organization", 
    "organization_id": 1,
    "visibility": "organization"
}
```

## User Journey Examples

### Individual Developer Journey
```
1. Sign up as individual user
2. Create personal contexts:
   - "learning-python"
   - "side-project-notes"
   - "interview-prep"
3. Record memories in personal contexts
4. Recall only from personal memories
5. Optional: Upgrade to create organization later
```

### Team Member Journey
```
1. Receive team invitation
2. Sign up via invitation link
3. Gain access to:
   - Personal contexts (private)
   - Team contexts (shared with team)
   - Organization contexts (company-wide)
4. Create personal contexts for individual work
5. Contribute to team contexts
6. Access organization knowledge base
```

### Organization Creator Journey
```
1. Sign up and create organization
2. Set up organization structure:
   - Create teams
   - Define context sharing policies
   - Set up organization-wide contexts
3. Invite team members
4. Manage context permissions
5. Access all contexts for administration
```

## Context Sharing Rules

### Personal Contexts
- **Owner**: Individual user only
- **Access**: Private to user
- **Sharing**: Cannot be shared (user can copy/move to team context)
- **Visibility**: Never visible to others

### Team Contexts  
- **Owner**: Team (all team members)
- **Access**: All team members (read/write)
- **Sharing**: Can be promoted to organization context
- **Visibility**: Visible to team members only

### Organization Contexts
- **Owner**: Organization
- **Access**: All organization members (read), admins (write)
- **Sharing**: Can be made public (if enabled)
- **Visibility**: All organization members

## Privacy and Data Ownership

### Individual Users
- **Own**: All personal contexts and memories
- **Control**: Complete control over personal data
- **Export**: Can export all personal data
- **Delete**: Can delete account and all personal data

### Team Members
- **Own**: Personal contexts only
- **Share**: Contribute to team/org contexts
- **Export**: Can export personal data, not team/org data
- **Leave**: Personal data stays, loses access to team/org data

### Organizations
- **Own**: Team and organization contexts
- **Control**: Admin controls over team/org data
- **Member Data**: Cannot access member personal contexts
- **Compliance**: Responsible for team/org data governance

## Implementation Priority

### Phase 1: Individual Users ✅
- Personal context creation and management
- Individual memory storage and recall
- Personal dashboard and analytics
- Account management and data export

### Phase 2: Organization Setup
- Organization registration and admin accounts
- Team creation and management
- Context scoping and permissions
- Admin dashboard for organization management

### Phase 3: Team Integration
- Invitation system for team members
- Multi-tier memory recall
- Context sharing and collaboration
- Team analytics and insights

This architecture ensures that individual users get full personal memory management while organizations get the collaborative features they need, all within the same system.
