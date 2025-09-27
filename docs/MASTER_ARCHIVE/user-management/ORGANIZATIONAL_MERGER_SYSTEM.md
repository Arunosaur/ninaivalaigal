# Organizational Merger & Acquisition Memory Management

## Scenario: Acme Corp Acquires StartupXYZ

When organizations merge, memory systems need to handle complex data consolidation while preserving security boundaries.

## Pre-Merger State

### Acme Corp (Acquiring Organization)
```
Organization: acme_corp
├── Users: john, alice, bob
├── Teams: frontend_team, security_team, backend_team
└── Memories: 10,000+ contexts across teams
```

### StartupXYZ (Acquired Organization)
```
Organization: startup_xyz
├── Users: sarah, mike, lisa
├── Teams: product_team, engineering_team
└── Memories: 2,000+ contexts
```

## Database Schema for Mergers

### Enhanced Organization Structure
```sql
CREATE TABLE organizations (
    id VARCHAR(100) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    parent_org_id VARCHAR(100) REFERENCES organizations(id),
    merger_date TIMESTAMP,
    status VARCHAR(20) DEFAULT 'active', -- 'active', 'merged', 'acquired'
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE organization_mergers (
    id SERIAL PRIMARY KEY,
    acquiring_org_id VARCHAR(100) REFERENCES organizations(id),
    acquired_org_id VARCHAR(100) REFERENCES organizations(id),
    merger_date TIMESTAMP NOT NULL,
    merger_type VARCHAR(20), -- 'acquisition', 'merger', 'consolidation'
    access_policy VARCHAR(20), -- 'isolate', 'integrate', 'selective'
    status VARCHAR(20) DEFAULT 'pending' -- 'pending', 'in_progress', 'completed'
);

-- Enhanced contexts table for merger tracking
ALTER TABLE contexts ADD COLUMN original_org_id VARCHAR(100);
ALTER TABLE contexts ADD COLUMN merged_from_org VARCHAR(100);
ALTER TABLE contexts ADD COLUMN merger_access_level VARCHAR(20) DEFAULT 'restricted';

-- Enhanced memories table
ALTER TABLE memories ADD COLUMN original_org_id VARCHAR(100);
ALTER TABLE memories ADD COLUMN access_post_merger VARCHAR(20) DEFAULT 'original_org_only';
```

## Merger Process Workflow

### Phase 1: Pre-Merger Setup
```python
class OrganizationalMerger:
    def initiate_merger(self, acquiring_org, acquired_org, merger_type='acquisition'):
        merger = {
            'acquiring_org_id': acquiring_org,
            'acquired_org_id': acquired_org,
            'merger_date': datetime.now(),
            'merger_type': merger_type,
            'access_policy': 'isolate',  # Start with isolation
            'status': 'pending'
        }

        # Create merger record
        self.db.create_merger_record(merger)

        # Notify all users of pending merger
        self.notify_users_of_merger(acquiring_org, acquired_org)

        return merger['id']
```

### Phase 2: Access Policy Configuration
```python
def configure_merger_access_policy(self, merger_id, policy_config):
    """
    Configure how memories will be accessible post-merger
    """
    policies = {
        'isolate': {
            'cross_org_access': False,
            'shared_contexts': [],
            'user_migration': False
        },
        'integrate': {
            'cross_org_access': True,
            'shared_contexts': 'all',
            'user_migration': True,
            'new_org_structure': 'unified'
        },
        'selective': {
            'cross_org_access': True,
            'shared_contexts': policy_config.get('allowed_contexts', []),
            'restricted_contexts': policy_config.get('restricted_contexts', []),
            'team_mapping': policy_config.get('team_mapping', {}),
            'access_levels': policy_config.get('access_levels', {})
        }
    }

    return self.apply_merger_policy(merger_id, policies[policy_config['type']])
```

## Merger Access Patterns

### Pattern 1: Complete Isolation (Conservative)
```python
# StartupXYZ users keep their original access
# Acme Corp users cannot see StartupXYZ memories
# Separate organizational boundaries maintained

merger_config = {
    'type': 'isolate',
    'cross_org_visibility': False,
    'maintain_separate_auth': True
}
```

**User Experience:**
```bash
# Sarah (from StartupXYZ) still sees only her org's memories
@e^M recall --scope organization  # Only startup_xyz memories

# John (from Acme) cannot access StartupXYZ memories
@e^M recall --scope organization  # Only acme_corp memories
```

### Pattern 2: Full Integration (Aggressive)
```python
# All users become part of unified organization
# Cross-organizational memory access enabled
# Teams may be merged or restructured

merger_config = {
    'type': 'integrate',
    'new_org_id': 'acme_corp_unified',
    'team_consolidation': {
        'startup_xyz.engineering_team': 'acme_corp.backend_team',
        'startup_xyz.product_team': 'acme_corp.frontend_team'
    },
    'memory_migration': 'full_access'
}
```

**User Experience:**
```bash
# Sarah can now access relevant Acme Corp memories
@e^M recall --scope organization  # All unified memories

# Cross-team collaboration enabled
@e^M context_start unified-project --scope team --team backend_team
```

### Pattern 3: Selective Integration (Balanced)
```python
# Gradual integration with controlled access
# Specific contexts shared based on business needs
# Maintains security while enabling collaboration

merger_config = {
    'type': 'selective',
    'shared_contexts': [
        'customer-support-knowledge',
        'product-roadmap-2024',
        'security-standards'
    ],
    'restricted_contexts': [
        'financial-data',
        'hr-records',
        'proprietary-algorithms'
    ],
    'cross_team_access': {
        'acme_corp.security_team': ['startup_xyz.engineering_team'],
        'startup_xyz.product_team': ['acme_corp.frontend_team']
    }
}
```

## JWT Token Updates Post-Merger

### Sarah's Updated Token (StartupXYZ → Acme Corp)
```python
# Before merger
old_token  # pragma: allowlist secret = {
    'user_id': 'sarah',
    'organization_id': 'startup_xyz',
    'teams': [{'team_id': 'product_team', 'role': 'lead'}]
}

# After selective merger
new_token  # pragma: allowlist secret = {
    'user_id': 'sarah',
    'primary_organization_id': 'acme_corp',
    'original_organization_id': 'startup_xyz',
    'organizations': [
        {
            'org_id': 'acme_corp',
            'access_level': 'selective',
            'teams': [{'team_id': 'frontend_team', 'role': 'member'}]
        },
        {
            'org_id': 'startup_xyz',
            'access_level': 'full',
            'teams': [{'team_id': 'product_team', 'role': 'lead'}]
        }
    ],
    'merger_context': {
        'merger_id': 'merger_123',
        'access_policy': 'selective',
        'effective_date': '2024-01-15'
    }
}
```

## Memory Access Control Post-Merger

### Enhanced Row-Level Security
```sql
-- Policy for cross-organizational access post-merger
CREATE POLICY merger_memory_access ON memories FOR SELECT
USING (
    -- Original organization access (always allowed)
    original_org_id = current_setting('app.current_user_org_id')
    OR
    -- Cross-org access based on merger policy
    (
        EXISTS (
            SELECT 1 FROM organization_mergers om
            WHERE (om.acquiring_org_id = current_setting('app.current_user_org_id')
                   OR om.acquired_org_id = current_setting('app.current_user_org_id'))
            AND om.status = 'completed'
            AND (
                om.access_policy = 'integrate'
                OR (
                    om.access_policy = 'selective'
                    AND memories.context_id IN (
                        SELECT context_id FROM merger_shared_contexts
                        WHERE merger_id = om.id
                    )
                )
            )
        )
    )
);
```

## Migration Commands

### Administrative Merger Operations
```bash
# Initiate merger
@e^M admin merger_initiate --acquiring acme_corp --acquired startup_xyz --type selective

# Configure shared contexts
@e^M admin merger_share_context --merger-id merger_123 --context customer-support-knowledge

# Migrate user to new team structure
@e^M admin user_migrate --user sarah --from startup_xyz.product_team --to acme_corp.frontend_team

# Complete merger
@e^M admin merger_complete --merger-id merger_123
```

### User Experience During Merger
```bash
# Sarah's gradual access expansion
@e^M recall --scope organization  # Initially only startup_xyz

# After selective sharing is enabled
@e^M recall --scope shared  # Can see shared contexts from both orgs

# After team migration
@e^M context_start new-unified-project --scope team --team frontend_team
```

## Rollback and Audit

### Merger Rollback Capability
```python
def rollback_merger(self, merger_id, rollback_to_date):
    """
    Rollback merger to previous state if needed
    """
    merger = self.get_merger(merger_id)

    # Restore original organizational boundaries
    self.restore_user_organizations(merger['acquired_org_id'])

    # Revoke cross-organizational access
    self.revoke_cross_org_access(merger_id)

    # Restore original team memberships
    self.restore_team_memberships(merger['acquired_org_id'], rollback_to_date)

    # Update merger status
    self.update_merger_status(merger_id, 'rolled_back')
```

### Audit Trail
```sql
CREATE TABLE merger_audit_log (
    id SERIAL PRIMARY KEY,
    merger_id INTEGER REFERENCES organization_mergers(id),
    action VARCHAR(100) NOT NULL,
    user_id VARCHAR(100) NOT NULL,
    affected_resources JSONB,
    timestamp TIMESTAMP DEFAULT NOW()
);
```

## Best Practices for Organizational Mergers

### 1. Phased Approach
- Start with isolation
- Gradually enable selective sharing
- Move to full integration only when ready

### 2. Security First
- Maintain audit trails
- Enable rollback capabilities
- Preserve original access controls

### 3. User Communication
- Notify users of merger timeline
- Provide training on new access patterns
- Maintain support during transition

This system handles organizational complexity while preserving security and enabling business continuity during mergers and acquisitions.
