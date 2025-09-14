# Spec 008: Team and Organization Ownership Management

## Overview
Design and implement comprehensive team and organization ownership management system with user interface for creating, managing, and transferring ownership roles.

## Current System Analysis

### Existing Database Schema
```sql
-- Teams table
CREATE TABLE teams (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    organization_id INTEGER REFERENCES organizations(id),
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Team members with roles
CREATE TABLE team_members (
    id SERIAL PRIMARY KEY,
    team_id INTEGER REFERENCES teams(id) NOT NULL,
    user_id INTEGER REFERENCES users(id) NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'member', -- owner, admin, member, viewer
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Organizations table
CREATE TABLE organizations (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    description TEXT,
    domain VARCHAR(255),
    settings JSON,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Current Gaps
1. **No explicit organization ownership model** - Missing organization_members table
2. **Team ownership creation unclear** - Who can create teams and assign initial owners?
3. **Ownership transfer mechanisms** - No APIs for changing owners
4. **Permission validation** - Limited checks for ownership operations
5. **User interface missing** - No web UI for management

## Requirements

### Team Ownership Management
1. **Team Creation**
   - Organization admins can create teams within their org
   - System admins can create cross-org teams
   - Team creator becomes initial owner
   - Must specify at least one owner during creation

2. **Team Owner Management**
   - Teams must have at least one owner at all times
   - Owners can promote members to admin/owner
   - Owners can demote admins (but not other owners)
   - Ownership transfer requires current owner action
   - Last owner cannot be removed without transfer

3. **Role Hierarchy**
   - `owner`: Full control, can manage all members and settings
   - `admin`: Can manage members (except owners), manage contexts
   - `member`: Can access team contexts, limited management
   - `viewer`: Read-only access to team contexts

### Organization Ownership Management
1. **Organization Creation**
   - System admin creates organizations
   - Organization creator becomes initial owner
   - Must specify domain and initial settings

2. **Organization Member Management**
   - Need new `organization_members` table
   - Roles: `owner`, `admin`, `member`, `viewer`
   - Organization owners can manage all members
   - Organization admins can manage members and teams

3. **Organization Owner Transfer**
   - Current owner can transfer to another member
   - Requires confirmation from new owner
   - Must maintain at least one owner

## Technical Implementation

### New Database Schema
```sql
-- Organization members table (NEW)
CREATE TABLE organization_members (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER REFERENCES organizations(id) NOT NULL,
    user_id INTEGER REFERENCES users(id) NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'member', -- owner, admin, member, viewer
    invited_by INTEGER REFERENCES users(id),
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(organization_id, user_id)
);

-- Ownership transfer requests (NEW)
CREATE TABLE ownership_transfer_requests (
    id SERIAL PRIMARY KEY,
    entity_type VARCHAR(20) NOT NULL, -- 'team' or 'organization'
    entity_id INTEGER NOT NULL,
    current_owner_id INTEGER REFERENCES users(id) NOT NULL,
    new_owner_id INTEGER REFERENCES users(id) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending', -- pending, accepted, rejected, expired
    message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP DEFAULT (CURRENT_TIMESTAMP + INTERVAL '7 days')
);
```

### API Endpoints

#### Team Management
```python
# Team creation with ownership
POST /teams
{
    "name": "Engineering Team",
    "organization_id": 1,
    "description": "Core engineering team",
    "initial_owners": [user_id1, user_id2]  # At least one required
}

# Team member role management
PUT /teams/{team_id}/members/{user_id}/role
{
    "role": "admin"  # owner, admin, member, viewer
}

# Transfer team ownership
POST /teams/{team_id}/transfer-ownership
{
    "new_owner_id": 123,
    "message": "Transferring ownership due to role change"
}

# Accept/reject ownership transfer
POST /ownership-transfers/{transfer_id}/respond
{
    "action": "accept",  # accept, reject
    "message": "Accepted ownership transfer"
}
```

#### Organization Management
```python
# Organization creation (admin only)
POST /organizations
{
    "name": "Acme Corp",
    "domain": "acme.com",
    "description": "Technology company",
    "initial_owner_id": 123
}

# Organization member management
POST /organizations/{org_id}/members
{
    "user_id": 456,
    "role": "admin"
}

PUT /organizations/{org_id}/members/{user_id}/role
{
    "role": "member"
}

# Organization ownership transfer
POST /organizations/{org_id}/transfer-ownership
{
    "new_owner_id": 789,
    "message": "CEO transition"
}
```

### User Interface Design

#### Team Management Dashboard
```html
<!-- Team Overview -->
<div class="team-dashboard">
    <h2>Team: Engineering</h2>
    <div class="team-info">
        <p>Organization: Acme Corp</p>
        <p>Members: 12</p>
        <p>Created: 2024-01-15</p>
    </div>
    
    <!-- Members Management -->
    <div class="members-section">
        <h3>Team Members</h3>
        <table class="members-table">
            <thead>
                <tr>
                    <th>Name</th>
                    <th>Email</th>
                    <th>Role</th>
                    <th>Joined</th>
                    <th>Actions</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>John Doe</td>
                    <td>john@acme.com</td>
                    <td>
                        <select class="role-select" data-user-id="123">
                            <option value="owner" selected>Owner</option>
                            <option value="admin">Admin</option>
                            <option value="member">Member</option>
                            <option value="viewer">Viewer</option>
                        </select>
                    </td>
                    <td>2024-01-15</td>
                    <td>
                        <button class="btn-transfer-ownership">Transfer Ownership</button>
                        <button class="btn-remove-member">Remove</button>
                    </td>
                </tr>
            </tbody>
        </table>
        
        <button class="btn-add-member">Add Member</button>
    </div>
    
    <!-- Ownership Transfer -->
    <div class="ownership-section">
        <h3>Ownership Management</h3>
        <button class="btn-transfer-team">Transfer Team Ownership</button>
        
        <!-- Pending transfers -->
        <div class="pending-transfers">
            <h4>Pending Ownership Transfers</h4>
            <div class="transfer-item">
                <p>Transfer to: Jane Smith (jane@acme.com)</p>
                <p>Requested: 2024-01-20</p>
                <p>Expires: 2024-01-27</p>
                <button class="btn-cancel-transfer">Cancel</button>
            </div>
        </div>
    </div>
</div>
```

#### Organization Management Dashboard
```html
<!-- Organization Overview -->
<div class="org-dashboard">
    <h2>Organization: Acme Corp</h2>
    <div class="org-info">
        <p>Domain: acme.com</p>
        <p>Members: 150</p>
        <p>Teams: 12</p>
        <p>Created: 2023-06-01</p>
    </div>
    
    <!-- Organization Members -->
    <div class="org-members-section">
        <h3>Organization Members</h3>
        <div class="member-filters">
            <select class="role-filter">
                <option value="">All Roles</option>
                <option value="owner">Owners</option>
                <option value="admin">Admins</option>
                <option value="member">Members</option>
                <option value="viewer">Viewers</option>
            </select>
            <input type="text" class="search-members" placeholder="Search members...">
        </div>
        
        <table class="org-members-table">
            <thead>
                <tr>
                    <th>Name</th>
                    <th>Email</th>
                    <th>Role</th>
                    <th>Teams</th>
                    <th>Joined</th>
                    <th>Actions</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>Alice Johnson</td>
                    <td>alice@acme.com</td>
                    <td>
                        <span class="role-badge owner">Owner</span>
                    </td>
                    <td>3</td>
                    <td>2023-06-01</td>
                    <td>
                        <button class="btn-transfer-org-ownership">Transfer Ownership</button>
                        <button class="btn-manage-teams">Manage Teams</button>
                    </td>
                </tr>
            </tbody>
        </table>
        
        <button class="btn-invite-member">Invite Member</button>
    </div>
    
    <!-- Teams Management -->
    <div class="org-teams-section">
        <h3>Organization Teams</h3>
        <div class="teams-grid">
            <div class="team-card">
                <h4>Engineering</h4>
                <p>12 members</p>
                <p>Owner: John Doe</p>
                <button class="btn-manage-team">Manage</button>
            </div>
        </div>
        
        <button class="btn-create-team">Create Team</button>
    </div>
</div>
```

### Spec-Kit Integration

#### Ownership Management Interface
```python
from spec_kit import OwnershipInterface, OwnershipOperationResult

class OwnershipSpec:
    entity_type: str  # 'team' or 'organization'
    entity_id: int
    current_owner_id: int
    new_owner_id: int
    transfer_message: Optional[str] = None

class OwnershipInterface(ABC):
    @abstractmethod
    def create_team_with_owners(self, team_spec: TeamSpec, owner_ids: List[int]) -> OwnershipOperationResult:
        pass
    
    @abstractmethod
    def transfer_ownership(self, ownership_spec: OwnershipSpec) -> OwnershipOperationResult:
        pass
    
    @abstractmethod
    def accept_ownership_transfer(self, transfer_id: int, user_id: int) -> OwnershipOperationResult:
        pass
    
    @abstractmethod
    def get_ownership_transfers(self, user_id: int) -> OwnershipOperationResult:
        pass
```

## Implementation Tasks

### Phase 1: Database Schema Updates
- [ ] Create `organization_members` table
- [ ] Create `ownership_transfer_requests` table
- [ ] Add indexes for performance
- [ ] Create migration scripts

### Phase 2: API Implementation
- [ ] Team ownership management endpoints
- [ ] Organization ownership management endpoints
- [ ] Ownership transfer workflow APIs
- [ ] Permission validation middleware

### Phase 3: Spec-Kit Integration
- [ ] Create ownership management interfaces
- [ ] Implement ownership validators
- [ ] Update context creation to check ownership
- [ ] Add ownership transfer workflows

### Phase 4: User Interface
- [ ] Team management dashboard
- [ ] Organization management dashboard
- [ ] Ownership transfer modals
- [ ] Member invitation system

### Phase 5: Testing and Documentation
- [ ] Unit tests for ownership operations
- [ ] Integration tests for transfer workflows
- [ ] API documentation updates
- [ ] User guide for management features

## Success Criteria
- Teams and organizations have clear ownership models
- Ownership can be transferred securely with confirmation
- User interface provides intuitive management capabilities
- All operations integrated through spec-kit framework
- Comprehensive permission validation at all levels
- Audit trail for all ownership changes

## Security Considerations
- Ownership transfers require confirmation from new owner
- Minimum one owner requirement enforced at database level
- All ownership operations logged for audit
- Permission checks at API and database level
- Rate limiting on ownership transfer requests
- Email notifications for ownership changes
