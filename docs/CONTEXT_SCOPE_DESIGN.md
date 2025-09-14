# Context Scope and Ownership Design

## Context Scope Differentiation

### 1. Context Types by Ownership
```sql
-- Personal Context: owner_id IS NOT NULL, team_id IS NULL, organization_id IS NULL
-- Team Context: owner_id IS NULL, team_id IS NOT NULL, organization_id IS NULL  
-- Organizational Context: owner_id IS NULL, team_id IS NULL, organization_id IS NOT NULL
```

### 2. Context Resolution Priority (for ambiguous names)
When multiple contexts with same name exist:
1. **Personal context** (highest priority)
2. **Team context** (if user is team member)
3. **Organizational context** (if user is org member)
4. **Shared contexts** (lowest priority)

### 3. Context Naming Convention
- **Personal**: `context-name` (simple name)
- **Team**: `@team:team-name/context-name` 
- **Organizational**: `@org:org-name/context-name`
- **Explicit scope**: `--scope personal|team|org`

## API Design

### Context Creation

#### Personal Context (Default)
```bash
eM start --context my-project
# Creates: owner_id=user_id, team_id=NULL, organization_id=NULL
```

#### Team Context
```bash
eM start --context @team:engineering/sprint-planning
# OR
eM start --context sprint-planning --scope team --team engineering
# Creates: owner_id=NULL, team_id=team_id, organization_id=NULL
```

#### Organizational Context
```bash
eM start --context @org:acme-corp/quarterly-review
# OR  
eM start --context quarterly-review --scope org --organization acme-corp
# Creates: owner_id=NULL, team_id=NULL, organization_id=org_id
```

### Context Resolution Logic

```python
def resolve_context(context_name: str, user_id: int, scope: str = None):
    """
    Resolve context based on name and user's access
    Priority: personal > team > org > shared
    """
    if scope == "personal":
        return get_personal_context(context_name, user_id)
    elif scope == "team":
        return get_team_context(context_name, user_id)
    elif scope == "org":
        return get_org_context(context_name, user_id)
    else:
        # Auto-resolve with priority
        contexts = []
        
        # 1. Check personal contexts
        personal = get_personal_context(context_name, user_id)
        if personal:
            contexts.append(("personal", personal))
        
        # 2. Check team contexts
        team_contexts = get_user_team_contexts(context_name, user_id)
        for ctx in team_contexts:
            contexts.append(("team", ctx))
        
        # 3. Check org contexts
        org_contexts = get_user_org_contexts(context_name, user_id)
        for ctx in org_contexts:
            contexts.append(("org", ctx))
        
        # 4. Check shared contexts
        shared_contexts = get_shared_contexts(context_name, user_id)
        for ctx in shared_contexts:
            contexts.append(("shared", ctx))
        
        if len(contexts) == 1:
            return contexts[0][1]
        elif len(contexts) > 1:
            # Ambiguous - require explicit scope
            raise AmbiguousContextError(contexts)
        else:
            return None
```

## Ownership and Permissions

### Team Ownership
- **Team Admins/Owners** can create team contexts
- **Team Members** can access team contexts (read/write based on permissions)
- **Team context creation** requires team admin role

### Organizational Ownership  
- **Organization Admins** can create organizational contexts
- **Organization Members** can access org contexts (read/write based on permissions)
- **Org context creation** requires org admin role

### Permission Levels
```sql
-- Context permissions table already exists
CREATE TABLE context_permissions (
    id SERIAL PRIMARY KEY,
    context_id INTEGER REFERENCES contexts(id),
    user_id INTEGER REFERENCES users(id),
    team_id INTEGER REFERENCES teams(id), 
    organization_id INTEGER REFERENCES organizations(id),
    permission_level VARCHAR(50) NOT NULL, -- 'read', 'write', 'admin', 'owner'
    granted_by INTEGER REFERENCES users(id),
    granted_at TIMESTAMP DEFAULT NOW()
);
```

## Context Sharing System

### Share Context API
```python
@app.post("/contexts/{context_id}/share")
async def share_context(
    context_id: int,
    share_data: ContextShare,
    current_user: User = Depends(get_current_user)
):
    """
    Share context with user/team/organization
    Only context owner or admin can share
    """
    # Validate ownership
    if not check_context_permission(context_id, current_user.id, "admin"):
        raise HTTPException(403, "Insufficient permissions")
    
    # Create permission entry
    permission = ContextPermission(
        context_id=context_id,
        user_id=share_data.target_id if share_data.target_type == "user" else None,
        team_id=share_data.target_id if share_data.target_type == "team" else None,
        organization_id=share_data.target_id if share_data.target_type == "organization" else None,
        permission_level=share_data.permission_level,
        granted_by=current_user.id
    )
```

### CLI Sharing
```bash
# Share with user (read-only)
eM share --context my-project --user john@example.com --permission read

# Share with team (read-write)  
eM share --context my-project --team engineering --permission write

# Share with organization (admin)
eM share --context sensitive-data --organization acme-corp --permission admin
```

## Context Transfer System

### Transfer Context API
```python
@app.post("/contexts/{context_id}/transfer")
async def transfer_context(
    context_id: int,
    transfer_data: ContextTransfer,
    current_user: User = Depends(get_current_user)
):
    """
    Transfer context ownership
    Only current owner can transfer
    """
    context = get_context(context_id)
    
    # Validate current ownership
    if not is_context_owner(context, current_user.id):
        raise HTTPException(403, "Only owner can transfer context")
    
    # Update ownership
    if transfer_data.target_type == "user":
        context.owner_id = transfer_data.target_id
        context.team_id = None
        context.organization_id = None
    elif transfer_data.target_type == "team":
        context.owner_id = None
        context.team_id = transfer_data.target_id
        context.organization_id = None
    elif transfer_data.target_type == "organization":
        context.owner_id = None
        context.team_id = None
        context.organization_id = transfer_data.target_id
```

### CLI Transfer
```bash
# Transfer to user
eM transfer --context my-project --to-user jane@example.com

# Transfer to team
eM transfer --context my-project --to-team engineering

# Transfer to organization  
eM transfer --context my-project --to-organization acme-corp
```

## Memory Recording with Context Scopes

### Explicit Scope Recording
```bash
# Record to personal context
eM remember "Important note" --context project-alpha --scope personal

# Record to team context
eM remember "Team decision" --context project-alpha --scope team

# Record to org context
eM remember "Company policy" --context project-alpha --scope org
```

### Auto-Resolution with Disambiguation
```bash
# If multiple "project-alpha" contexts exist:
eM remember "Important note" --context project-alpha
# Output: 
# Multiple contexts found for 'project-alpha':
# 1. Personal: project-alpha (created 2025-01-01)
# 2. Team: engineering/project-alpha (created 2025-01-02)  
# 3. Organization: acme-corp/project-alpha (created 2025-01-03)
# Please specify scope: --scope personal|team|org
```

## Database Schema Updates

### Add Scope Column for Clarity
```sql
ALTER TABLE contexts ADD COLUMN scope VARCHAR(20) GENERATED ALWAYS AS (
    CASE 
        WHEN owner_id IS NOT NULL THEN 'personal'
        WHEN team_id IS NOT NULL THEN 'team'
        WHEN organization_id IS NOT NULL THEN 'organization'
        ELSE 'unknown'
    END
) STORED;

CREATE INDEX idx_contexts_scope ON contexts(scope);
CREATE INDEX idx_contexts_name_scope ON contexts(name, scope);
```

### Unique Constraints by Scope
```sql
-- Ensure unique context names within scope
CREATE UNIQUE INDEX idx_contexts_unique_personal 
ON contexts(name, owner_id) 
WHERE owner_id IS NOT NULL;

CREATE UNIQUE INDEX idx_contexts_unique_team 
ON contexts(name, team_id) 
WHERE team_id IS NOT NULL;

CREATE UNIQUE INDEX idx_contexts_unique_org 
ON contexts(name, organization_id) 
WHERE organization_id IS NOT NULL;
```

## Spec-Kit Implementation Status

1. **Context scope differentiation** ✅ (implemented via ContextScope enum)
2. **Context resolution logic** ✅ (implemented via ContextResolver)
3. **Team/org context creation APIs** ✅ (implemented via SpecKitContextManager)
4. **Context sharing system** ✅ (implemented via ContextPermissionSpec)
5. **Context transfer system** ✅ (implemented via transfer_context method)
6. **CLI scope handling** ✅ (updated with scope parameters)
7. **FastAPI/MCP parity** ✅ (both use spec-kit interfaces)
8. **Backward compatibility removed** ✅ (all legacy code cleaned up)
