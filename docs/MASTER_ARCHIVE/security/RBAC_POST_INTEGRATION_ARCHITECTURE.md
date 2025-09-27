# RBAC Post-Integration System Architecture

## Overview
This document describes the complete Role-Based Access Control (RBAC) system architecture after successful integration into the Ninaivalaigal platform. The RBAC system provides fine-grained permission control across users, teams, and organizations.

## System Components

### 1. RBAC Core Components

#### Role Hierarchy
```
SYSTEM (highest precedence)
├── OWNER
├── ADMIN
├── MAINTAINER
├── MEMBER
└── VIEWER (lowest precedence)
```

#### Actions
- **READ**: View resources
- **CREATE**: Create new resources
- **UPDATE**: Modify existing resources
- **DELETE**: Remove resources
- **SHARE**: Share resources with others
- **EXPORT**: Export resource data
- **ADMINISTER**: Administrative operations
- **INVITE**: Invite users to teams/orgs
- **APPROVE**: Approve access requests
- **BACKUP**: Create backups
- **RESTORE**: Restore from backups
- **CONFIGURE**: System configuration
- **AUDIT**: Access audit logs

#### Resources
- **MEMORY**: Memory entries and data
- **CONTEXT**: Context management
- **TEAM**: Team operations
- **ORG**: Organization operations
- **USER**: User management
- **INVITATION**: Invitation management
- **BACKUP**: Backup operations
- **SYSTEM**: System administration
- **API**: API access control
- **AUDIT**: Audit log access

### 2. Database Schema

#### Core RBAC Tables
- `role_assignments`: User role assignments with scope
- `permission_audits`: Comprehensive audit trail
- `permission_delegations`: Temporary permission delegation
- `access_requests`: Permission elevation requests

#### Extended User Model
- Added `default_role` and `is_system_admin` columns
- Relationships to RBAC tables established

### 3. Authentication Integration

#### JWT Token Enhancement
JWT token  # pragma: allowlist secrets now include:
```json
{
  "user_id": 123,
  "email": "user@example.com",
  "roles": {
    "global": "MEMBER",
    "org:1": "ADMIN",
    "team:5": "MAINTAINER"
  },
  "teams": {
    "5": "MAINTAINER"
  },
  "org_id": "1"
}
```

#### RBAC Middleware
- Extracts RBAC context from JWT token  # pragma: allowlist secrets
- Validates permissions for each request
- Provides decorators for endpoint protection

### 4. API Integration

#### Protected Endpoints
All API endpoints now use RBAC decorators:
- `@require_permission(Resource.MEMORY, Action.READ)`
- `@require_role(Role.ADMIN)`
- `@require_authentication`

#### RBAC Management APIs
New endpoints under `/rbac/`:
- Role assignment management
- Permission delegation
- Access request workflow
- Audit log access
- System status monitoring

### 5. Permission Matrix

#### Role Permissions Summary

| Resource | VIEWER | MEMBER | MAINTAINER | ADMIN | OWNER | SYSTEM |
|----------|--------|--------|------------|-------|-------|--------|
| MEMORY   | R,E    | R,C,U,E| R,C,U,D,E  | R,C,U,D,E | ALL | ALL |
| CONTEXT  | R,E    | R,C,U,S,E| R,C,U,D,S,E| R,C,U,D,S,E | ALL | ALL |
| TEAM     | R      | R      | R,U,I      | R,C,U,D,A,I | ALL | ALL |
| ORG      | -      | -      | -          | R,U,A,I,C | ALL | ALL |
| USER     | R      | R      | R,I        | R,C,U,A,I | ALL | ALL |
| AUDIT    | -      | -      | R          | R,A       | ALL | ALL |

*Legend: R=Read, C=Create, U=Update, D=Delete, S=Share, E=Export, A=Administer, I=Invite*

## Security Features

### 1. Multi-Layer Security
- JWT signature verification
- Permission-based access control
- Audit logging for all actions
- Rate limiting with RBAC context
- Input validation and sanitization

### 2. Audit Trail
Complete audit logging includes:
- User ID and action performed
- Resource accessed and result (allowed/denied)
- Timestamp and request metadata
- IP address and user agent

### 3. Permission Delegation
- Temporary permission grants
- Expiration-based access
- Delegation audit trail
- Administrative approval workflow

## Deployment Architecture

### 1. Database Layer
```
PostgreSQL Database (mem0db)
├── Core Tables (users, contexts, memories, etc.)
├── RBAC Tables (role_assignments, permission_audits, etc.)
└── Indexes for performance optimization
```

### 2. Application Layer
```
FastAPI Server (Port 13370)
├── RBAC Middleware
├── Rate Limiting Middleware
├── Authentication System
├── Protected API Endpoints
└── RBAC Management APIs
```

### 3. Security Middleware Stack
```
Request Flow:
1. Rate Limiting Middleware
2. RBAC Middleware (JWT extraction)
3. CORS Middleware
4. Endpoint Permission Decorators
5. Business Logic
```

## Configuration

### 1. Environment Variables
- `NINAIVALAIGAL_JWT_SECRET`: Required for JWT signing
- `NINAIVALAIGAL_DATABASE_URL`: PostgreSQL connection
- `NINAIVALAIGAL_USER_TOKEN`: MCP server authentication

### 2. Default Role Assignments
- New users: `MEMBER` role globally
- First user: `SYSTEM` role (admin privileges)
- Team creators: `ADMIN` role in their teams
- Organization creators: `OWNER` role in their orgs

## API Usage Examples

### 1. Authentication with RBAC
```bash
# Login and receive JWT with roles
curl -X POST http://localhost:13370/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password  # pragma: allowlist secret":"password"}'

# Response includes RBAC roles
{
  "user": {
    "jwt_token  # pragma: allowlist secret": "eyJ...",
    "rbac_roles": {
      "global": "MEMBER",
      "team:1": "ADMIN"
    }
  }
}
```

### 2. Role Management
```bash
# Assign role to user
curl -X POST http://localhost:13370/rbac/roles/assign \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -d '{"user_id":123,"role":"ADMIN","scope_type":"team","scope_id":"1"}'

# Get user permissions
curl -X GET http://localhost:13370/rbac/permissions/user/123 \
  -H "Authorization: Bearer $JWT_TOKEN"
```

### 3. Access Request Workflow
```bash
# Request elevated access
curl -X POST http://localhost:13370/rbac/access-request \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -d '{"resource":"TEAM","action":"ADMINISTER","justification":"Need to manage team settings"}'

# Approve request (admin only)
curl -X POST http://localhost:13370/rbac/access-requests/1/approve \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -d '{"action":"approve","reason":"Approved for project needs"}'
```

## Monitoring and Maintenance

### 1. System Health
- RBAC status endpoint: `/rbac/status`
- Role distribution metrics
- Active delegation count
- Pending access requests

### 2. Audit Analysis
- Permission denial patterns
- User activity monitoring
- Security incident detection
- Compliance reporting

### 3. Performance Optimization
- Database indexes on RBAC tables
- JWT token  # pragma: allowlist secret caching strategies
- Permission check optimization
- Audit log rotation

## Migration and Rollback

### 1. Database Migration
- RBAC tables created with `create_rbac_tables.sql`
- Existing users assigned default roles
- Backward compatibility maintained for core functionality

### 2. Rollback Strategy
- RBAC middleware can be disabled
- Core functionality remains operational
- Database rollback scripts available
- Gradual feature deprecation possible

## Future Enhancements

### 1. Advanced Features
- Dynamic role creation
- Conditional permissions
- Time-based access controls
- Multi-factor authentication integration

### 2. Integration Opportunities
- External identity providers (LDAP, OAuth)
- Enterprise SSO integration
- Advanced audit analytics
- Compliance framework integration

## Conclusion

The RBAC integration provides enterprise-grade access control while maintaining system performance and usability. The modular architecture allows for future enhancements while ensuring security and compliance requirements are met.

**Status**: ✅ Production Ready
**Last Updated**: September 15, 2025
**Version**: 1.0.0
