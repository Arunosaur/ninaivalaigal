# Team and Organization Ownership Management

## Overview

The Ninaivalaigal platform implements a comprehensive ownership management system for teams and organizations, providing secure role-based access control and ownership transfer workflows.

## Key Features

### Team Ownership
- **Multi-owner support**: Teams can have multiple owners for redundancy
- **Role hierarchy**: Owner > Admin > Member > Viewer
- **Ownership transfer**: Secure workflow with confirmation and expiration
- **Minimum owner requirement**: At least one owner must exist at all times

### Organization Ownership
- **Single owner model**: Organizations have one primary owner
- **Member management**: Role-based membership with permissions
- **Cross-organizational teams**: Teams can span multiple organizations
- **Ownership succession**: Planned transfer workflows for continuity

## Database Schema

### Team Members
```sql
CREATE TABLE team_members (
    id SERIAL PRIMARY KEY,
    team_id INTEGER REFERENCES teams(id),
    user_id INTEGER REFERENCES users(id),
    role VARCHAR(50) NOT NULL DEFAULT 'member', -- owner, admin, member, viewer
    joined_at TIMESTAMP DEFAULT NOW()
);
```

### Organization Members (New)
```sql
CREATE TABLE organization_members (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER REFERENCES organizations(id),
    user_id INTEGER REFERENCES users(id),
    role VARCHAR(50) NOT NULL DEFAULT 'member', -- owner, admin, member, viewer
    joined_at TIMESTAMP DEFAULT NOW()
);
```

### Ownership Transfer Requests (New)
```sql
CREATE TABLE ownership_transfer_requests (
    id SERIAL PRIMARY KEY,
    entity_type VARCHAR(50) NOT NULL, -- 'team' or 'organization'
    entity_id INTEGER NOT NULL,
    current_owner_id INTEGER REFERENCES users(id),
    new_owner_id INTEGER REFERENCES users(id),
    message TEXT,
    status VARCHAR(50) DEFAULT 'pending', -- pending, accepted, rejected, expired
    expires_at TIMESTAMP DEFAULT NOW() + INTERVAL '7 days',
    created_at TIMESTAMP DEFAULT NOW(),
    processed_at TIMESTAMP
);
```

## API Endpoints

### Team Management
- `POST /api/teams` - Create team with initial owners
- `PUT /api/teams/{team_id}/members/{user_id}/role` - Change member role
- `POST /api/teams/{team_id}/transfer-ownership` - Initiate ownership transfer
- `GET /api/teams/{team_id}/members` - List team members with roles

### Organization Management
- `POST /api/organizations` - Create organization with owner
- `PUT /api/organizations/{org_id}/members/{user_id}/role` - Change member role
- `POST /api/organizations/{org_id}/transfer-ownership` - Initiate ownership transfer
- `GET /api/organizations/{org_id}/members` - List organization members

### Ownership Transfers
- `GET /api/ownership-transfers` - Get pending transfers for user
- `POST /api/ownership-transfers/{transfer_id}/accept` - Accept ownership transfer
- `POST /api/ownership-transfers/{transfer_id}/reject` - Reject ownership transfer

## Spec-Kit Integration

The ownership management system is fully integrated with the spec-kit framework:

### Ownership Interface
```python
class OwnershipInterface(ABC):
    @abstractmethod
    def create_team_with_owners(self, team_spec: TeamSpec, owner_ids: List[int]) -> ContextOperationResult:
        pass
    
    @abstractmethod
    def transfer_ownership(self, ownership_spec: OwnershipSpec, user_id: int) -> ContextOperationResult:
        pass
    
    @abstractmethod
    def change_member_role(self, entity_type: EntityType, entity_id: int, user_id: int, new_role: OwnershipRole, changed_by: int) -> ContextOperationResult:
        pass
```

### Ownership Specifications
```python
@dataclass
class OwnershipSpec:
    entity_type: EntityType
    entity_id: int
    current_owner_id: int
    new_owner_id: int
    transfer_message: Optional[str] = None
    expires_at: Optional[str] = None

@dataclass
class TeamSpec:
    name: str
    organization_id: Optional[int] = None
    description: Optional[str] = None
    initial_owners: List[int] = None
```

## Permission Model

### Role Permissions

| Role | Team Permissions | Organization Permissions |
|------|------------------|-------------------------|
| Owner | Full control, ownership transfer | Full control, ownership transfer |
| Admin | Manage members, contexts | Manage members, teams |
| Member | View, create contexts | View teams, limited access |
| Viewer | View only | View only |

### Validation Rules
1. **Minimum owners**: Teams and organizations must have at least one owner
2. **Role hierarchy**: Higher roles can manage lower roles (except owner-to-owner)
3. **Ownership transfer**: Only owners can initiate transfers
4. **Confirmation required**: New owners must accept transfers
5. **Expiration**: Transfer requests expire after 7 days

## User Interface

### Team Management Dashboard
- Member list with role badges
- Role change dropdowns (permission-based)
- Ownership transfer modal with confirmation
- Member invitation system
- Pending transfer notifications

### Organization Management Dashboard
- Organization overview with member count
- Member management with role controls
- Ownership succession planning
- Team management within organization
- Audit log for ownership changes

## Security Considerations

### Access Control
- JWT-based authentication for all operations
- Role-based permission validation at API layer
- Database constraints for ownership integrity
- Audit logging for ownership changes

### Transfer Security
- Confirmation workflow prevents unauthorized transfers
- Expiration prevents stale transfer requests
- Email notifications for transfer events
- Rollback capability for failed transfers

## Implementation Status

### ✅ Completed
- Spec-kit framework with ownership interfaces
- Team management UI with role controls
- Database schema design and specifications
- Ownership transfer workflow design

### 🔄 In Progress
- Team ownership management APIs
- Spec-kit ownership manager implementation

### ⏳ Pending
- Organization ownership management APIs
- Database schema migration scripts
- Ownership transfer acceptance/rejection APIs
- Email notification system
- Audit logging implementation

## Usage Examples

### Creating a Team with Owners
```python
team_spec = TeamSpec(
    name="Engineering Team",
    organization_id=1,
    description="Core engineering team",
    initial_owners=[101, 102]
)

result = ownership_manager.create_team_with_owners(team_spec, [101, 102])
```

### Transferring Team Ownership
```python
ownership_spec = OwnershipSpec(
    entity_type=EntityType.TEAM,
    entity_id=5,
    current_owner_id=101,
    new_owner_id=103,
    transfer_message="Transitioning leadership to Alice"
)

result = ownership_manager.transfer_ownership(ownership_spec, user_id=101)
```

### Changing Member Role
```python
result = ownership_manager.change_member_role(
    entity_type=EntityType.TEAM,
    entity_id=5,
    user_id=104,
    new_role=OwnershipRole.ADMIN,
    changed_by=101
)
```

## Testing Strategy

### Unit Tests
- Ownership validation logic
- Role permission checks
- Transfer workflow states
- Spec-kit interface compliance

### Integration Tests
- API endpoint functionality
- Database constraint validation
- UI component interactions
- End-to-end ownership workflows

### Security Tests
- Permission bypass attempts
- Transfer manipulation tests
- Role escalation prevention
- Authentication validation

## Deployment Considerations

### Database Migration
1. Create new tables for organization_members and ownership_transfer_requests
2. Migrate existing team ownership data
3. Add foreign key constraints and indexes
4. Validate data integrity

### API Versioning
- New endpoints under `/api/v2/` for ownership management
- Backward compatibility for existing team APIs
- Deprecation timeline for legacy endpoints

### Monitoring
- Ownership transfer success/failure rates
- Role change frequency and patterns
- Security event logging and alerting
- Performance metrics for ownership operations

---

*Last updated: 2025-09-14*
*Version: 1.0*
