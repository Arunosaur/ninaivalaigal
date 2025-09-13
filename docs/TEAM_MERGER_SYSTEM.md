# Team Merger System Documentation

## Overview

Team mergers occur within organizations when teams are consolidated, restructured, or disbanded. This system handles memory migration and access control during team reorganizations.

## Team Merger Scenarios

### Scenario 1: Team Consolidation
```
Frontend Team + Backend Team → Full Stack Team
- Merge two complementary teams
- Combine all memories and contexts
- Maintain historical team attribution
```

### Scenario 2: Team Split
```
Large Engineering Team → Frontend Team + Backend Team + DevOps Team
- Split oversized team into specialized units
- Distribute memories based on relevance
- Maintain cross-team collaboration
```

### Scenario 3: Team Dissolution
```
Legacy Team → Members distributed to other teams
- Archive team memories
- Migrate members to new teams
- Preserve historical context
```

### Scenario 4: Team Rename/Restructure
```
Marketing Team → Growth Team
- Update team identity
- Maintain all existing memories
- Update access permissions
```

## Database Schema for Team Mergers

### Team Merger Tracking
```sql
CREATE TABLE team_mergers (
    id SERIAL PRIMARY KEY,
    organization_id VARCHAR(100) NOT NULL,
    merger_type VARCHAR(20) NOT NULL, -- 'consolidation', 'split', 'dissolution', 'rename'
    source_teams JSONB NOT NULL,     -- Array of source team IDs
    target_teams JSONB NOT NULL,     -- Array of target team IDs
    merger_date TIMESTAMP NOT NULL,
    initiated_by VARCHAR(100) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'in_progress', 'completed', 'rolled_back'
    memory_migration_policy JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE team_merger_memory_mapping (
    id SERIAL PRIMARY KEY,
    merger_id INTEGER REFERENCES team_mergers(id),
    source_context_id INTEGER REFERENCES contexts(id),
    target_team_id VARCHAR(100),
    migration_type VARCHAR(20), -- 'move', 'copy', 'archive', 'delete'
    access_level VARCHAR(20) DEFAULT 'inherited' -- 'inherited', 'restricted', 'enhanced'
);

-- Enhanced team memberships for merger tracking
ALTER TABLE team_memberships ADD COLUMN previous_team_id VARCHAR(100);
ALTER TABLE team_memberships ADD COLUMN merger_id INTEGER REFERENCES team_mergers(id);
ALTER TABLE team_memberships ADD COLUMN migration_date TIMESTAMP;

-- Enhanced contexts for team merger history
ALTER TABLE contexts ADD COLUMN original_team_id VARCHAR(100);
ALTER TABLE contexts ADD COLUMN merged_from_teams JSONB;
ALTER TABLE contexts ADD COLUMN team_merger_id INTEGER REFERENCES team_mergers(id);
```

## Team Merger Implementation

### Core Merger Manager
```python
class TeamMergerManager:
    def __init__(self, db_manager):
        self.db = db_manager
        
    def initiate_team_merger(self, org_id, merger_config):
        """
        Initiate team merger process
        """
        merger = {
            'organization_id': org_id,
            'merger_type': merger_config['type'],
            'source_teams': merger_config['source_teams'],
            'target_teams': merger_config['target_teams'],
            'merger_date': datetime.now(),
            'initiated_by': merger_config['initiated_by'],
            'status': 'pending',
            'memory_migration_policy': merger_config.get('memory_policy', {})
        }
        
        merger_id = self.db.create_team_merger(merger)
        
        # Validate merger prerequisites
        self._validate_merger_prerequisites(merger_id, merger_config)
        
        return merger_id
    
    def execute_team_consolidation(self, merger_id):
        """
        Execute team consolidation merger
        """
        merger = self.db.get_team_merger(merger_id)
        
        if merger['merger_type'] != 'consolidation':
            raise ValueError("Invalid merger type for consolidation")
        
        # Update merger status
        self.db.update_merger_status(merger_id, 'in_progress')
        
        try:
            # Step 1: Create new consolidated team if needed
            target_team = self._create_or_get_target_team(merger)
            
            # Step 2: Migrate team members
            self._migrate_team_members(merger, target_team['id'])
            
            # Step 3: Migrate memories and contexts
            self._migrate_team_memories(merger, target_team['id'])
            
            # Step 4: Update access permissions
            self._update_access_permissions(merger, target_team['id'])
            
            # Step 5: Archive source teams
            self._archive_source_teams(merger)
            
            # Complete merger
            self.db.update_merger_status(merger_id, 'completed')
            
            return {
                'status': 'completed',
                'target_team': target_team,
                'migrated_contexts': self._get_migrated_contexts(merger_id),
                'migrated_members': self._get_migrated_members(merger_id)
            }
            
        except Exception as e:
            self.db.update_merger_status(merger_id, 'failed')
            self._log_merger_error(merger_id, str(e))
            raise
    
    def execute_team_split(self, merger_id):
        """
        Execute team split merger
        """
        merger = self.db.get_team_merger(merger_id)
        
        if merger['merger_type'] != 'split':
            raise ValueError("Invalid merger type for split")
        
        self.db.update_merger_status(merger_id, 'in_progress')
        
        try:
            # Step 1: Create new target teams
            target_teams = self._create_target_teams(merger)
            
            # Step 2: Distribute members based on specialization
            self._distribute_team_members(merger, target_teams)
            
            # Step 3: Distribute memories based on relevance
            self._distribute_team_memories(merger, target_teams)
            
            # Step 4: Set up cross-team collaboration
            self._setup_cross_team_collaboration(merger, target_teams)
            
            # Step 5: Archive source team
            self._archive_source_teams(merger)
            
            self.db.update_merger_status(merger_id, 'completed')
            
            return {
                'status': 'completed',
                'target_teams': target_teams,
                'distribution_summary': self._get_distribution_summary(merger_id)
            }
            
        except Exception as e:
            self.db.update_merger_status(merger_id, 'failed')
            raise
    
    def _migrate_team_memories(self, merger, target_team_id):
        """
        Migrate memories from source teams to target team
        """
        source_teams = merger['source_teams']
        migration_policy = merger.get('memory_migration_policy', {})
        
        for source_team_id in source_teams:
            # Get all contexts for source team
            contexts = self.db.get_team_contexts(source_team_id)
            
            for context in contexts:
                migration_type = self._determine_migration_type(
                    context, migration_policy
                )
                
                if migration_type == 'move':
                    self._move_context_to_team(context['id'], target_team_id, merger['id'])
                elif migration_type == 'copy':
                    self._copy_context_to_team(context['id'], target_team_id, merger['id'])
                elif migration_type == 'archive':
                    self._archive_context(context['id'], merger['id'])
                
                # Log migration
                self.db.log_memory_migration(
                    merger['id'], context['id'], target_team_id, migration_type
                )
    
    def _distribute_team_memories(self, merger, target_teams):
        """
        Distribute memories among multiple target teams based on relevance
        """
        source_team_id = merger['source_teams'][0]  # Assuming single source for split
        contexts = self.db.get_team_contexts(source_team_id)
        
        for context in contexts:
            # Determine most relevant target team
            target_team = self._determine_context_relevance(context, target_teams)
            
            # Move context to most relevant team
            self._move_context_to_team(context['id'], target_team['id'], merger['id'])
            
            # Set up cross-team access for related teams
            related_teams = self._find_related_teams(context, target_teams)
            for related_team in related_teams:
                self._grant_cross_team_access(
                    context['id'], related_team['id'], 'read'
                )
```

### Memory Migration Policies
```python
class MemoryMigrationPolicy:
    @staticmethod
    def get_consolidation_policy():
        return {
            'default_action': 'move',
            'conflict_resolution': 'merge',
            'access_inheritance': 'union',
            'context_naming': 'preserve_with_prefix'
        }
    
    @staticmethod
    def get_split_policy():
        return {
            'distribution_strategy': 'relevance_based',
            'cross_team_access': 'selective',
            'shared_contexts': ['onboarding', 'company-standards'],
            'specialization_mapping': {
                'frontend': ['ui', 'react', 'css', 'design'],
                'backend': ['api', 'database', 'server', 'auth'],
                'devops': ['deployment', 'ci/cd', 'infrastructure', 'monitoring']
            }
        }
    
    @staticmethod
    def get_dissolution_policy():
        return {
            'member_redistribution': 'manual',
            'memory_action': 'archive',
            'access_preservation': 'historical',
            'cleanup_schedule': '90_days'
        }
```

## MCP Server Integration

### Team Merger Commands
```python
@mcp.tool()
def team_merger_initiate(
    merger_type: str,
    source_teams: List[str],
    target_teams: List[str],
    memory_policy: Optional[Dict] = None
) -> Dict:
    """
    Initiate team merger process
    
    Args:
        merger_type: Type of merger ('consolidation', 'split', 'dissolution', 'rename')
        source_teams: List of source team IDs
        target_teams: List of target team IDs
        memory_policy: Memory migration policy configuration
    """
    user_info = get_current_user()
    
    # Validate user permissions
    if not has_admin_permission(user_info, 'team_management'):
        raise PermissionError("Insufficient permissions for team merger")
    
    merger_config = {
        'type': merger_type,
        'source_teams': source_teams,
        'target_teams': target_teams,
        'initiated_by': user_info['user_id'],
        'memory_policy': memory_policy or {}
    }
    
    merger_manager = TeamMergerManager(db)
    merger_id = merger_manager.initiate_team_merger(
        user_info['organization_id'], merger_config
    )
    
    return {
        'merger_id': merger_id,
        'status': 'initiated',
        'next_steps': [
            'Review merger plan',
            'Approve memory migration policy',
            'Execute merger'
        ]
    }

@mcp.tool()
def team_merger_execute(merger_id: int) -> Dict:
    """
    Execute approved team merger
    
    Args:
        merger_id: ID of the merger to execute
    """
    user_info = get_current_user()
    merger_manager = TeamMergerManager(db)
    
    merger = db.get_team_merger(merger_id)
    
    if merger['merger_type'] == 'consolidation':
        result = merger_manager.execute_team_consolidation(merger_id)
    elif merger['merger_type'] == 'split':
        result = merger_manager.execute_team_split(merger_id)
    elif merger['merger_type'] == 'dissolution':
        result = merger_manager.execute_team_dissolution(merger_id)
    elif merger['merger_type'] == 'rename':
        result = merger_manager.execute_team_rename(merger_id)
    
    return result

@mcp.tool()
def team_merger_rollback(merger_id: int, rollback_reason: str) -> Dict:
    """
    Rollback completed team merger
    
    Args:
        merger_id: ID of the merger to rollback
        rollback_reason: Reason for rollback
    """
    user_info = get_current_user()
    merger_manager = TeamMergerManager(db)
    
    result = merger_manager.rollback_merger(merger_id, rollback_reason)
    
    return {
        'status': 'rolled_back',
        'merger_id': merger_id,
        'rollback_summary': result
    }
```

## Usage Examples

### Team Consolidation
```bash
# Merge Frontend and Backend teams into Full Stack team
@e^M team_merger_initiate \
  --type consolidation \
  --source-teams "frontend_team,backend_team" \
  --target-teams "fullstack_team" \
  --memory-policy '{"default_action": "move", "conflict_resolution": "merge"}'

# Execute the merger
@e^M team_merger_execute --merger-id 123
```

### Team Split
```bash
# Split large Engineering team into specialized teams
@e^M team_merger_initiate \
  --type split \
  --source-teams "engineering_team" \
  --target-teams "frontend_team,backend_team,devops_team" \
  --memory-policy '{"distribution_strategy": "relevance_based"}'

# Execute the split
@e^M team_merger_execute --merger-id 124
```

### Team Dissolution
```bash
# Dissolve Legacy team and redistribute members
@e^M team_merger_initiate \
  --type dissolution \
  --source-teams "legacy_team" \
  --target-teams "modern_team,innovation_team" \
  --memory-policy '{"memory_action": "archive", "member_redistribution": "manual"}'

# Execute dissolution
@e^M team_merger_execute --merger-id 125
```

## Audit and Compliance

### Merger Audit Trail
```sql
CREATE TABLE team_merger_audit (
    id SERIAL PRIMARY KEY,
    merger_id INTEGER REFERENCES team_mergers(id),
    action VARCHAR(100) NOT NULL,
    performed_by VARCHAR(100) NOT NULL,
    affected_resources JSONB,
    timestamp TIMESTAMP DEFAULT NOW(),
    details JSONB
);
```

### Compliance Reports
```python
def generate_merger_compliance_report(merger_id):
    """
    Generate compliance report for team merger
    """
    merger = db.get_team_merger(merger_id)
    audit_trail = db.get_merger_audit_trail(merger_id)
    
    report = {
        'merger_summary': merger,
        'compliance_checks': {
            'data_retention': check_data_retention_compliance(merger),
            'access_controls': check_access_control_compliance(merger),
            'audit_trail': validate_audit_trail(audit_trail),
            'rollback_capability': verify_rollback_capability(merger)
        },
        'affected_users': get_affected_users(merger),
        'memory_migration_summary': get_migration_summary(merger),
        'generated_at': datetime.now()
    }
    
    return report
```

This comprehensive team merger system handles all organizational restructuring scenarios while maintaining data integrity and compliance requirements.
