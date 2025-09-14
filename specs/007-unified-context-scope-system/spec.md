# Spec 007: Unified Context Scope System

## Overview
Unified context management system with personal, team, and organizational scopes integrated through spec-kit framework. Removes all backward compatibility and ensures FastAPI and MCP server parity.

## Objectives
- Implement unified context scope differentiation (personal/team/organization)
- Remove all backward compatibility code
- Integrate with spec-kit framework for consistent implementation
- Ensure FastAPI and MCP server functional parity
- Provide context resolution, sharing, and transfer capabilities

## Technical Requirements

### Database Schema
```sql
-- Unified contexts table (replaces recording_contexts)
CREATE TABLE contexts (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    scope VARCHAR(20) NOT NULL DEFAULT 'personal', -- personal, team, organization
    owner_id INTEGER REFERENCES users(id),
    team_id INTEGER REFERENCES teams(id),
    organization_id INTEGER REFERENCES organizations(id),
    visibility VARCHAR(20) DEFAULT 'private',
    is_active BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT scope_ownership_check CHECK (
        (scope = 'personal' AND owner_id IS NOT NULL AND team_id IS NULL AND organization_id IS NULL) OR
        (scope = 'team' AND team_id IS NOT NULL AND owner_id IS NULL AND organization_id IS NULL) OR
        (scope = 'organization' AND organization_id IS NOT NULL AND owner_id IS NULL AND team_id IS NULL)
    )
);

-- Context permissions for sharing
CREATE TABLE context_permissions (
    id SERIAL PRIMARY KEY,
    context_id INTEGER REFERENCES contexts(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id),
    team_id INTEGER REFERENCES teams(id),
    organization_id INTEGER REFERENCES organizations(id),
    permission_level VARCHAR(20) NOT NULL, -- read, write, admin, owner
    granted_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### API Endpoints

#### FastAPI Endpoints
```python
# Context Management
POST /contexts - Create context with scope
GET /contexts - List user-accessible contexts
GET /contexts/{id} - Get specific context
PUT /contexts/{id} - Update context
DELETE /contexts/{id} - Delete context

# Context Operations
POST /contexts/{id}/share - Share context with permissions
POST /contexts/{id}/transfer - Transfer context ownership
POST /contexts/{id}/activate - Set as active context
POST /contexts/{id}/deactivate - Deactivate context

# Context Resolution
GET /contexts/resolve/{name} - Resolve context by name with scope priority
```

#### MCP Server Methods
```python
# Must mirror FastAPI functionality exactly
create_context(name, scope, description, team_id, organization_id)
list_contexts(user_id)
get_context(context_id)
update_context(context_id, updates)
delete_context(context_id)
share_context(context_id, target_type, target_id, permission_level)
transfer_context(context_id, target_type, target_id)
resolve_context(name, user_id, scope_hint)
```

### Context Resolution Logic
Priority order for ambiguous context names:
1. Personal contexts (owned by user)
2. Team contexts (user is member)
3. Organization contexts (user belongs to org)
4. Shared contexts (user has permissions)

### Scope Validation Rules
- **Personal**: Only context owner can manage
- **Team**: Team admins/owners can create and manage
- **Organization**: Organization admins can create and manage
- **Sharing**: Only owners/admins can share contexts
- **Transfer**: Only owners can transfer ownership

## Implementation Tasks

### Phase 1: Remove Backward Compatibility
- [ ] Remove legacy context command structures from CLI
- [ ] Remove RecordingContext model references
- [ ] Clean up deprecated API endpoints
- [ ] Remove SQLite fallback code

### Phase 2: Spec-Kit Integration
- [ ] Define context scope interfaces in spec-kit
- [ ] Implement context resolution through spec-kit
- [ ] Standardize error handling and responses
- [ ] Create spec-kit validators for context operations

### Phase 3: FastAPI/MCP Parity
- [ ] Audit all FastAPI endpoints
- [ ] Implement identical MCP server methods
- [ ] Create shared validation logic
- [ ] Ensure consistent error responses

### Phase 4: Documentation and Testing
- [ ] Update all documentation
- [ ] Create comprehensive test suite
- [ ] Validate end-to-end workflows
- [ ] Performance testing for context resolution

## Success Criteria
- All context operations work identically through FastAPI and MCP
- Context resolution handles ambiguous names correctly
- Sharing and transfer permissions enforced properly
- No backward compatibility code remains
- All operations integrated through spec-kit framework
- Comprehensive test coverage > 90%

## Dependencies
- PostgreSQL database with updated schema
- JWT authentication system
- Team and organization management
- Spec-kit framework integration

## Risks and Mitigation
- **Breaking Changes**: Remove backward compatibility cleanly with clear migration path
- **Performance**: Optimize context resolution queries with proper indexing
- **Security**: Enforce strict permission validation at all levels
- **Consistency**: Use spec-kit to ensure FastAPI/MCP parity

## Timeline
- Phase 1: 1 day (Remove backward compatibility)
- Phase 2: 2 days (Spec-kit integration)
- Phase 3: 1 day (FastAPI/MCP parity)
- Phase 4: 1 day (Documentation and testing)

**Total: 5 days**
