# Hierarchical Memory System for Multi-Team Organizations

## John's Scenario: Personal + Team1 + Team2 + Organization

John works in one organization but belongs to multiple teams. Here's how memory isolation works:

```
Organization: Acme Corp
├── Personal: John's private memories
├── Team1: Frontend Development Team
├── Team2: Security Team
└── Organization: Company-wide shared memories
```

## Database Schema Design

### Enhanced Context Table
```sql
CREATE TABLE contexts (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    owner_id VARCHAR(100) NOT NULL,
    scope_type VARCHAR(20) NOT NULL, -- 'personal', 'team', 'organization'
    scope_id VARCHAR(100),            -- team_id or org_id
    visibility VARCHAR(20) DEFAULT 'private', -- 'private', 'team', 'organization'
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE memories (
    id SERIAL PRIMARY KEY,
    context_id INTEGER REFERENCES contexts(id),
    user_id VARCHAR(100) NOT NULL,
    scope_type VARCHAR(20) NOT NULL,
    scope_id VARCHAR(100),
    content JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE team_memberships (
    user_id VARCHAR(100) NOT NULL,
    team_id VARCHAR(100) NOT NULL,
    organization_id VARCHAR(100) NOT NULL,
    role VARCHAR(50) DEFAULT 'member', -- 'member', 'admin', 'owner'
    PRIMARY KEY (user_id, team_id)
);
```

## JWT Token with Multi-Team Information

### John's Enhanced JWT Token
```python
# When John logs in
token = jwt.encode({
    'user_id': 'john',
    'email': 'john@acmecorp.com',
    'organization_id': 'acme_corp',
    'teams': [
        {'team_id': 'frontend_team', 'role': 'member'},
        {'team_id': 'security_team', 'role': 'admin'}
    ],
    'default_scope': 'personal',  # Default context scope
    'exp': datetime.utcnow() + timedelta(days=7)
}, JWT_SECRET)
```

## Context Creation with Scopes

### Personal Context
```python
# John creates personal context
@e^M context_create --name "john-learning" --scope personal
```
```sql
INSERT INTO contexts (name, owner_id, scope_type, scope_id, visibility)
VALUES ('john-learning', 'john', 'personal', 'john', 'private');
```

### Team Context
```python
# John creates team context for Frontend team
@e^M context_create --name "frontend-auth-project" --scope team --team frontend_team
```
```sql
INSERT INTO contexts (name, owner_id, scope_type, scope_id, visibility)
VALUES ('frontend-auth-project', 'john', 'team', 'frontend_team', 'team');
```

### Organization Context
```python
# John creates organization-wide context
@e^M context_create --name "company-security-standards" --scope organization
```
```sql
INSERT INTO contexts (name, owner_id, scope_type, scope_id, visibility)
VALUES ('company-security-standards', 'john', 'organization', 'acme_corp', 'organization');
```

## Row-Level Security Policies

### Personal Memory Access
```sql
CREATE POLICY personal_memories ON memories FOR ALL
USING (
    scope_type = 'personal' AND
    user_id = current_setting('app.current_user_id')
);
```

### Team Memory Access
```sql
CREATE POLICY team_memories ON memories FOR ALL
USING (
    scope_type = 'team' AND
    scope_id IN (
        SELECT team_id FROM team_memberships
        WHERE user_id = current_setting('app.current_user_id')
    )
);
```

### Organization Memory Access
```sql
CREATE POLICY org_memories ON memories FOR ALL
USING (
    scope_type = 'organization' AND
    scope_id = current_setting('app.current_org_id')
);
```

## MCP Server Implementation

### Context Scoping Logic
```python
class HierarchicalMemoryManager:
    def __init__(self, jwt_token):
        self.user_info = jwt.decode(jwt_token, JWT_SECRET)
        self.user_id = self.user_info['user_id']
        self.org_id = self.user_info['organization_id']
        self.teams = self.user_info['teams']

    def create_context(self, name, scope='personal', team_id=None):
        if scope == 'personal':
            return self._create_personal_context(name)
        elif scope == 'team':
            if not self._user_in_team(team_id):
                raise PermissionError(f"User not in team {team_id}")
            return self._create_team_context(name, team_id)
        elif scope == 'organization':
            return self._create_org_context(name)

    def get_accessible_contexts(self):
        contexts = []

        # Personal contexts
        contexts.extend(self._get_personal_contexts())

        # Team contexts for all user's teams
        for team in self.teams:
            contexts.extend(self._get_team_contexts(team['team_id']))

        # Organization contexts
        contexts.extend(self._get_org_contexts())

        return contexts

    def store_memory(self, content, context_name, scope_hint=None):
        context = self._resolve_context(context_name, scope_hint)

        memory = {
            'context_id': context.id,
            'user_id': self.user_id,
            'scope_type': context.scope_type,
            'scope_id': context.scope_id,
            'content': content
        }

        return self.db.store_memory(memory)
```

## John's VS Code Configuration

### Multi-Scope Context Switching
```json
{
  "mcp.servers": {
    "e^m": {
      "command": "/opt/homebrew/anaconda3/bin/python",
      "args": ["/Users/asrajag/Workspace/mem0/server/mcp_server.py"],
      "env": {
        "NINAIVALAIGAL_USER_TOKEN": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
        "NINAIVALAIGAL_DEFAULT_SCOPE": "personal"
      }
    }
  }
}
```

## Usage Examples

### John's Daily Workflow

#### Morning: Personal Learning
```bash
@e^M context_start john-learning --scope personal
@e^M remember "Learned about React hooks today"
```

#### Work: Frontend Team Project
```bash
@e^M context_start auth-implementation --scope team --team frontend_team
@e^M remember "Implemented JWT authentication for login component"
```

#### Afternoon: Security Team Meeting
```bash
@e^M context_start security-audit --scope team --team security_team
@e^M remember "Found vulnerability in user input validation"
```

#### Company All-Hands: Organization Context
```bash
@e^M context_start company-goals-2024 --scope organization
@e^M remember "CEO announced new security compliance requirements"
```

### Memory Retrieval with Scope Filtering

#### Get All Accessible Memories
```bash
@e^M recall --all-scopes
```

#### Get Team-Specific Memories
```bash
@e^M recall --scope team --team frontend_team
```

#### Get Personal Memories Only
```bash
@e^M recall --scope personal
```

#### Cross-Team Search (if John has access)
```bash
@e^M search "authentication" --scopes personal,team,organization
```

## Access Control Matrix

| Memory Type | John Can Read | John Can Write | Team Members Can Read | Org Members Can Read |
|-------------|---------------|----------------|----------------------|---------------------|
| Personal | ✅ | ✅ | ❌ | ❌ |
| Team1 (Frontend) | ✅ | ✅ | ✅ | ❌ |
| Team2 (Security) | ✅ | ✅ | ✅ | ❌ |
| Organization | ✅ | ✅ | ✅ | ✅ |

## Context Auto-Detection

### Smart Context Switching
```python
def auto_detect_context(self, file_path, git_branch):
    # Detect context based on project structure
    if 'frontend/' in file_path:
        return self._get_team_context('frontend_team')
    elif 'security/' in file_path:
        return self._get_team_context('security_team')
    elif git_branch.startswith('personal/'):
        return self._get_personal_context()
    else:
        return self._get_default_context()
```

## Memory Sharing Workflow

### Cross-Team Collaboration
```python
# John shares frontend context with security team
@e^M share_context frontend-auth-project --with-team security_team --permission read

# Security team can now see frontend authentication memories
@e^M recall --context frontend-auth-project --scope team --team frontend_team
```

This hierarchical system ensures John's memories are properly isolated while enabling appropriate collaboration across his multiple team memberships.
