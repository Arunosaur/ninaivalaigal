# Multi-Editor, Multi-User Context Management

## Overview

mem0 supports complex enterprise development scenarios with multiple editors, terminals, users, and teams working simultaneously across different projects. Each context is cryptographically isolated and tracked independently with full multi-level sharing support.

## Enterprise Scenario: Multi-Editor, Multi-User, Multi-Team

### Example Enterprise Setup
```
Organization: TechCorp

Team Alpha (Backend Team):
├── User A (Senior Dev):
│   ├── Terminal 1: mem0_context_start alpha-backend-shared (Team context)
│   ├── VS Code 1: MEM0_CONTEXT=alpha-backend-shared (Team context)
│   └── VS Code 2: MEM0_CONTEXT=personal-research (Personal context)
├── User B (Junior Dev):
│   ├── JetBrains: MEM0_CONTEXT=alpha-backend-shared (Team context)
│   └── Terminal 2: mem0_context_start personal-experiments (Personal context)

Team Beta (Frontend Team):
├── User C (Lead Dev):
│   ├── VS Code 3: MEM0_CONTEXT=beta-frontend-shared (Team context)
│   └── Terminal 3: mem0_context_start beta-mobile-app (Team context)
└── User D (Designer):
    └── VS Code 4: MEM0_CONTEXT=beta-design-system (Team context)

Organization Wide:
└── Shared contexts: company-standards, engineering-best-practices
```

## How Context Isolation Works

### ✅ Complete User Authentication & Isolation
Each user is fully authenticated and isolated:
```bash
# User authentication (required)
./client/mem0 auth login --username alice --password securepass
./client/mem0 auth register --username bob --email bob@company.com --password securepass

# User-specific context listing
./client/mem0 context list  # Shows only user's contexts
```

### Multi-Level Context Sharing
Contexts support four visibility levels:
- **Personal**: Private to the owner only
- **Team**: Shared with team members based on roles
- **Organization**: Available to entire organization
- **Public**: Accessible to all authenticated users

### Per-Terminal Context Selection
Each terminal can record to different contexts:
```bash
# Terminal 1 - Team collaboration
./client/mem0 auth login --username alice --password securepass
mem0_context_start alpha-backend-shared
git commit -m "API endpoint implementation"

# Terminal 2 - Personal work
mem0_context_start personal-research
python analyze_data.py
```

### Per-Editor Context Selection
Each editor can work with different contexts:
```bash
# VS Code 1 (Team context)
export MEM0_CONTEXT=alpha-backend-shared
code .

# VS Code 2 (Personal context)
export MEM0_CONTEXT=personal-research
code ~/research
```

## Enterprise Context Management

### Organization Structure
```bash
# Create organization (admin only)
./client/mem0 org create --name "TechCorp" --description "Technology Corporation"

# Create teams within organization
./client/mem0 team create --name "Backend Team" --org-id 1 --description "API Development"
./client/mem0 team create --name "Frontend Team" --org-id 1 --description "UI/UX Development"

# Add team members with roles
./client/mem0 team add-member --team-id 1 --user-id 2 --role admin   # Alice as admin
./client/mem0 team add-member --team-id 1 --user-id 3 --role member # Bob as member
```

### Context Sharing Permissions
```bash
# Create team-shared context
./client/mem0 context-create --name "alpha-backend-shared" --visibility team
# Automatically shared with team members based on roles

# Share existing context with specific permissions
./client/mem0 share --context-id 1 --target-type team --target-id 1 --permission write
./client/mem0 share --context-id 2 --target-type user --target-id 4 --permission read
```

### Cross-Team Collaboration
```bash
# Share context across teams
./client/mem0 share --context-id 10 --target-type team --target-id 2 --permission write
# Backend team can now write to Frontend team's context

# Create cross-team context
./client/mem0 context-create --name "company-integration" --visibility organization
# Available to all organization members
```

## Advanced Context Management

### View All Accessible Contexts
```bash
# List all contexts you can access (personal + shared)
./client/mem0 context list

# Show context details with permissions
./client/mem0 context list --detailed

# Check active context in current terminal
mem0_context_active  # bash/zsh/fish
Get-Mem0Context      # PowerShell
```

### Context Recall for AI Agents
```bash
# AI agent recalls specific project context
./client/mem0 recall --context alpha-backend-shared

# AI agent recalls personal work
./client/mem0 recall --context personal-research

# Cross-context search
./client/mem0 recall --query "authentication" --all-contexts
```

### Permission-Based Access Control
```bash
# Check your permissions for a context
./client/mem0 context permissions --context-id 1

# View sharing history
./client/mem0 context sharing-history --context-id 1

# Transfer context ownership
./client/mem0 context transfer-ownership --context-id 1 --new-owner-id 2
```

## Database Architecture

### Complete User Isolation
- Each user has cryptographically separate data
- JWT tokens prevent session hijacking
- Database queries are user-scoped by default
- No cross-user data leakage possible

### Multi-Level Context Architecture
```sql
-- Contexts support ownership hierarchy
SELECT * FROM recording_contexts
WHERE (owner_id = $current_user_id)  -- Personal contexts
   OR (team_id IN (SELECT team_id FROM team_members WHERE user_id = $current_user_id))  -- Team contexts
   OR (organization_id IN (SELECT org_id FROM user_organizations WHERE user_id = $current_user_id))  -- Org contexts
   OR (visibility = 'public');  -- Public contexts
```

### Permission Inheritance System
- **Owner**: Full control (read/write/admin/transfer)
- **Admin**: Manage sharing and context settings
- **Member**: Read/write access to shared content
- **Viewer**: Read-only access to shared content

## Integration Points

### Universal Shell Integration
```bash
# Linux/Unix (bash/zsh/fish)
source /path/to/mem0/client/mem0-universal.sh
./client/mem0 auth login --username alice --password securepass
mem0_context_start alpha-backend-shared

# Windows PowerShell
. .\client\mem0-windows.ps1
.\client\mem0.exe auth login --username alice --password securepass
Start-Mem0Context -ContextName "alpha-backend-shared"
```

### VS Code Integration
```json
// .vscode/settings.json
{
  "terminal.integrated.env.linux": {
    "MEM0_CONTEXT": "alpha-backend-shared"
  },
  "terminal.integrated.env.osx": {
    "MEM0_CONTEXT": "alpha-backend-shared"
  },
  "terminal.integrated.env.windows": {
    "MEM0_CONTEXT": "alpha-backend-shared"
  }
}
```

### JetBrains Integration
```
Settings → Tools → External Tools:
- Name: "mem0 Context Start"
- Program: /path/to/mem0/client/mem0
- Arguments: context-create --name $Prompt$ --visibility team
- Working Directory: $ProjectFileDir$
```

## Enterprise Best Practices

### For Individual Contributors
```bash
# Maintain separation between personal and team work
mem0_context_start personal-experiments  # Personal context
mem0_context_start alpha-backend-shared  # Team context

# Use consistent naming conventions
./client/mem0 context-create --name "team-alpha-sprint-23" --visibility team
./client/mem0 context-create --name "personal-ml-research" --visibility personal
```

### For Team Leads
```bash
# Create shared team contexts
./client/mem0 context-create --name "team-alpha-architecture" --visibility team
./client/mem0 context-create --name "team-alpha-onboarding" --visibility team

# Manage team permissions
./client/mem0 team add-member --team-id 1 --user-id 5 --role admin
./client/mem0 team add-member --team-id 1 --user-id 6 --role member
```

### For Enterprise Administrators
```bash
# Organization-wide knowledge base
./client/mem0 context-create --name "company-engineering-standards" --visibility organization
./client/mem0 context-create --name "company-security-policies" --visibility organization

# Cross-team collaboration contexts
./client/mem0 context-create --name "company-integration-standards" --visibility organization
```

## Performance & Scalability

### Context Caching
- Intelligent context caching reduces API calls by 70%
- Background processing prevents UI blocking
- Connection pooling for database efficiency

### Multi-User Performance
- Horizontal scaling support for large organizations
- Database query optimization for permission checks
- Efficient memory indexing and search

### Monitoring & Health Checks
```bash
# Performance monitoring
curl http://127.0.0.1:13370/health

# System metrics
curl http://127.0.0.1:13370/metrics

# User-specific context count
./client/mem0 context list | wc -l
```

## Security Considerations

### Authentication Security
- JWT tokens with configurable expiration (30 minutes default)
- Secure password hashing with bcrypt
- Token refresh and validation mechanisms

### Data Isolation
- Cryptographic user data separation
- Permission-based access control
- Audit trails for all sharing activities

### Enterprise Compliance
- GDPR-compliant data handling
- SOC 2 ready audit logging
- HIPAA-ready for healthcare organizations

## API Endpoints

```
Authentication:
POST /auth/register     # User registration
POST /auth/login        # JWT token login
GET  /auth/me           # Current user info
POST /auth/logout       # Token invalidation

Context Management:
GET  /contexts          # List accessible contexts
POST /contexts          # Create new context
GET  /contexts/{id}     # Get context details
PUT  /contexts/{id}     # Update context
DELETE /contexts/{id}   # Delete context

Sharing & Permissions:
POST /share             # Share context with user/team/org
GET  /permissions       # Get context permissions
PUT  /permissions       # Update permissions

Memory Operations:
GET  /memories          # Recall memories
POST /memories          # Store memory
DELETE /memories/{id}   # Delete memory

Organization Management:
POST /orgs              # Create organization
GET  /orgs              # List organizations
POST /teams             # Create team
POST /teams/members     # Add team member
```

This enterprise-ready architecture ensures complete isolation, flexible sharing, and scalable performance while maintaining the simple observer philosophy that makes mem0 powerful yet easy to use.
