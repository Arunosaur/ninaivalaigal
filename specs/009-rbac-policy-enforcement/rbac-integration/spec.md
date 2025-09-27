# Spec 006: RBAC Integration
## Role-Based Access Control System Integration

**Status**: Draft
**Created**: 2025-09-15
**Author**: AI Development Team
**Priority**: High

---

## Overview

Integrate the existing RBAC package (`ninaivalaigal_ci_rbac_pack`) into the main Ninaivalaigal platform to provide comprehensive role-based access control for multi-user and team environments.

## Goals

### Primary Goals
- Integrate RBAC system with existing authentication
- Provide fine-grained permission control for all resources
- Support hierarchical role-based access (User → Team → Organization)
- Maintain backward compatibility with existing APIs
- Ensure security and performance standards

### Secondary Goals
- Enable audit logging for all permission changes
- Support dynamic permission delegation
- Provide admin interfaces for permission management
- Enable compliance reporting and access reviews

## Context and Background

### Current State
- Basic JWT authentication with simple user roles
- Database supports team/organization structures
- Limited permission granularity (read/write/admin)
- No hierarchical access control
- RBAC package exists but not integrated

### Motivation
- Multi-tenant platform requires sophisticated access control
- Team collaboration needs role-based permissions
- Security compliance requires audit trails
- Scalability demands efficient permission checking

## Detailed Design

### 1. Enhanced RBAC System

#### Extended Role Hierarchy
```python
class Role(Enum):
    VIEWER = auto()      # Read-only access
    MEMBER = auto()      # Basic user permissions
    MAINTAINER = auto()  # Advanced user permissions
    ADMIN = auto()       # Administrative permissions
    OWNER = auto()       # Full access
    SYSTEM = auto()      # System-level operations (new)
```

#### Extended Actions
```python
class Action(Enum):
    # Existing actions
    READ = auto()
    CREATE = auto()
    UPDATE = auto()
    DELETE = auto()
    SHARE = auto()
    EXPORT = auto()
    ADMINISTER = auto()

    # New actions
    INVITE = auto()      # Invite users
    APPROVE = auto()     # Approve requests
    BACKUP = auto()      # Create backups
    RESTORE = auto()     # Restore data
    CONFIGURE = auto()   # System configuration
    AUDIT = auto()       # Access audit logs
```

#### Extended Resources
```python
class Resource(Enum):
    # Existing resources
    MEMORY = auto()
    CONTEXT = auto()
    TEAM = auto()
    ORG = auto()
    AUDIT = auto()

    # New resources
    USER = auto()        # User management
    INVITATION = auto()  # Invitation management
    BACKUP = auto()      # Backup operations
    SYSTEM = auto()      # System administration
    API = auto()         # API access control
```

### 2. Database Integration

#### Enhanced User Model
```python
class User(Base):
    # Existing fields...

    # RBAC integration
    default_role = Column(Enum(Role), default=Role.MEMBER)
    is_system_admin = Column(Boolean, default=False)

    # Relationships
    team_memberships = relationship("TeamMember", back_populates="user")
    org_memberships = relationship("OrganizationMember", back_populates="user")
```

#### New RBAC Models
```python
class RoleAssignment(Base):
    __tablename__ = "role_assignments"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    role = Column(Enum(Role), nullable=False)
    scope_type = Column(String(20), nullable=False)  # 'global', 'org', 'team', 'context'
    scope_id = Column(String(50), nullable=True)  # ID of org/team/context
    granted_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    granted_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)

class PermissionAudit(Base):
    __tablename__ = "permission_audits"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    action = Column(Enum(Action), nullable=False)
    resource = Column(Enum(Resource), nullable=False)
    resource_id = Column(String(50), nullable=True)
    allowed = Column(Boolean, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    request_ip = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
```

### 3. Authentication Integration

#### Enhanced JWT Payload
```python
def create_access_token(user: User, context: Optional[str] = None) -> str:
    # Get user's effective roles
    roles = get_user_roles(user.id, context)

    payload = {
        "user_id": user.id,
        "email": user.email,
        "roles": {
            "global": user.default_role.name,
            "teams": {str(tm.team_id): tm.role.name for tm in user.team_memberships},
            "orgs": {str(om.org_id): om.role.name for om in user.org_memberships}
        },
        "permissions": get_effective_permissions(user.id, context),
        "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
```

#### RBAC Middleware
```python
class RBACMiddleware:
    def __init__(self, app: FastAPI):
        self.app = app

    async def __call__(self, request: Request, call_next):
        # Extract user context from JWT
        user_context = await self.extract_user_context(request)

        # Add RBAC context to request
        request.state.rbac_context = user_context

        response = await call_next(request)
        return response

    async def extract_user_context(self, request: Request) -> Optional[SubjectContext]:
        token = request.headers.get("Authorization")
        if not token:
            return None

        try:
            payload = jwt.decode(token.replace("Bearer ", ""), JWT_SECRET, algorithms=["HS256"])
            return SubjectContext(
                user_id=payload["user_id"],
                org_id=payload.get("org_id"),
                team_ids=set(payload.get("team_ids", [])),
                roles=payload.get("roles", {})
            )
        except jwt.InvalidTokenError:
            return None
```

### 4. Permission Decorators

#### FastAPI Permission Decorator
```python
def require_permission(resource: Resource, action: Action,
                      scope: Optional[str] = None):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            request = kwargs.get('request') or args[0]

            # Get RBAC context
            rbac_context = getattr(request.state, 'rbac_context', None)
            if not rbac_context:
                raise HTTPException(status_code=401, detail="Authentication required")

            # Check permission
            if not authorize(rbac_context, resource, action, scope):
                audit_permission_attempt(rbac_context, resource, action, False)
                raise HTTPException(status_code=403, detail="Insufficient permissions")

            # Log successful access
            audit_permission_attempt(rbac_context, resource, action, True)

            return await func(*args, **kwargs)
        return wrapper
    return decorator
```

#### Usage Examples
```python
@app.post("/contexts")
@require_permission(Resource.CONTEXT, Action.CREATE)
async def create_context(request: Request, context_data: ContextCreate):
    # Implementation
    pass

@app.delete("/teams/{team_id}")
@require_permission(Resource.TEAM, Action.DELETE, scope="team:{team_id}")
async def delete_team(request: Request, team_id: int):
    # Implementation
    pass
```

### 5. Role Management APIs

#### Role Assignment Endpoints
```python
@app.post("/users/{user_id}/roles")
@require_permission(Resource.USER, Action.ADMINISTER)
async def assign_role(request: Request, user_id: int, role_data: RoleAssignmentCreate):
    """Assign role to user in specific scope"""
    pass

@app.delete("/users/{user_id}/roles/{assignment_id}")
@require_permission(Resource.USER, Action.ADMINISTER)
async def revoke_role(request: Request, user_id: int, assignment_id: int):
    """Revoke role assignment"""
    pass

@app.get("/users/{user_id}/permissions")
@require_permission(Resource.USER, Action.READ)
async def get_user_permissions(request: Request, user_id: int):
    """Get effective permissions for user"""
    pass
```

## Implementation Plan

### Phase 1: Core RBAC Extension (Week 1)
1. **Extend RBAC System**
   - Add new roles, actions, and resources
   - Enhance permission matrix
   - Create comprehensive test suite

2. **Database Schema Updates**
   - Create new RBAC tables
   - Update existing models
   - Create migration scripts

3. **RBAC Middleware**
   - Implement FastAPI middleware
   - Create permission decorators
   - Add audit logging

### Phase 2: Authentication Integration (Week 2)
1. **JWT Enhancement**
   - Add RBAC context to tokens
   - Update token validation
   - Implement role-based token refresh

2. **API Integration**
   - Add permission checks to all endpoints
   - Update error handling
   - Implement role-based filtering

3. **Data Migration**
   - Migrate existing user roles
   - Establish team/org relationships
   - Set default permissions

### Phase 3: Advanced Features (Week 3)
1. **Permission Management**
   - Role assignment APIs
   - Permission delegation
   - Temporary access grants

2. **Audit System**
   - Permission attempt logging
   - Access pattern analysis
   - Compliance reporting

3. **Performance Optimization**
   - Permission caching
   - Efficient role resolution
   - Database query optimization

### Phase 4: Frontend Integration (Week 4)
1. **UI Components**
   - Role-based navigation
   - Permission-aware forms
   - Admin interfaces

2. **User Experience**
   - Clear permission feedback
   - Role selection interfaces
   - Access request workflows

## Security Considerations

### Access Control
- **Principle of Least Privilege**: Default to minimal permissions
- **Role Separation**: Clear separation between roles
- **Permission Inheritance**: Hierarchical permission model
- **Audit Trail**: Complete audit log of all permission changes

### Performance
- **Permission Caching**: Cache frequently accessed permissions
- **Efficient Queries**: Optimize database queries for role resolution
- **Minimal Overhead**: <10ms permission check latency
- **Scalable Design**: Support for large numbers of users/teams

### Compliance
- **GDPR Compliance**: Audit logs for data access
- **SOC 2 Requirements**: Access control documentation
- **Role Review Process**: Regular permission audits
- **Data Retention**: Configurable audit log retention

## Testing Strategy

### Unit Tests
- RBAC permission matrix validation
- Role hierarchy and precedence
- Permission decorator functionality
- Database model relationships

### Integration Tests
- End-to-end permission flows
- JWT token integration
- API endpoint protection
- Database migration validation

### Security Tests
- Permission bypass attempts
- Role escalation testing
- Audit log integrity
- Performance under load

## Success Metrics

### Functional Metrics
- **Permission Coverage**: 100% of API endpoints protected
- **Role Compliance**: All users have appropriate roles
- **Migration Success**: Zero data loss during migration
- **Backward Compatibility**: Existing APIs continue to work

### Performance Metrics
- **Permission Check Latency**: <10ms average
- **API Response Time**: <5% increase from baseline
- **Database Performance**: Optimized role queries
- **Memory Usage**: Minimal RBAC overhead

### Security Metrics
- **Audit Coverage**: 100% of permission attempts logged
- **Access Control**: Zero unauthorized access incidents
- **Compliance**: Pass all security audits
- **Vulnerability Assessment**: Zero high-severity findings

## Risks and Mitigation

### High Risk
1. **Data Migration Failure**
   - Mitigation: Comprehensive backup and rollback plan
   - Testing: Full migration testing in staging environment

2. **Performance Degradation**
   - Mitigation: Permission caching and query optimization
   - Testing: Load testing with RBAC enabled

3. **Security Vulnerabilities**
   - Mitigation: Security audit and penetration testing
   - Testing: Comprehensive security test suite

### Medium Risk
1. **Breaking API Changes**
   - Mitigation: Backward compatibility layer
   - Testing: Existing API client validation

2. **Complex Permission Logic**
   - Mitigation: Clear documentation and examples
   - Testing: Comprehensive permission scenario testing

## Dependencies

### Technical Dependencies
- ✅ P0 Security fixes completed
- ✅ Database schema supports team/org structures
- ✅ JWT authentication system operational
- ✅ RBAC package available

### Team Dependencies
- Security team review and approval
- Database migration coordination
- Frontend development for UI components
- QA testing for permission scenarios

## Acceptance Criteria

### Must Have
- [ ] All API endpoints protected with appropriate permissions
- [ ] User roles migrated from existing system
- [ ] Team and organization permissions functional
- [ ] Audit logging for all permission attempts
- [ ] Performance meets specified metrics

### Should Have
- [ ] Admin interfaces for permission management
- [ ] Role delegation functionality
- [ ] Compliance reporting capabilities
- [ ] Permission caching for performance

### Could Have
- [ ] Temporary access grants
- [ ] Advanced audit analytics
- [ ] Integration with external identity providers
- [ ] Automated permission reviews

---

**Next Steps**: Begin Phase 1 implementation with RBAC system extension

**Review Required**: Security team approval before implementation

**Timeline**: 4 weeks for complete integration
