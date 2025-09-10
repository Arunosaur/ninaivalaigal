# Multi-Editor, Multi-User Context Management

## Overview

mem0 supports complex development scenarios with multiple editors, terminals, and users working simultaneously on different projects. Each context is isolated and tracked independently.

## Scenario: Multiple Editors, Multiple Users

### Example Setup
```
User A:
├── Terminal 1: mem0_on shared-backend     (shared with VS Code 1)
├── VS Code 1: MEM0_CONTEXT=shared-backend (shared with Terminal 1)  
└── VS Code 2: MEM0_CONTEXT=frontend-app   (independent project)

User B:
├── JetBrains: MEM0_CONTEXT=mobile-app     (independent project)
├── Terminal 2: mem0_on data-pipeline      (independent project)
└── VS Code 3: MEM0_CONTEXT=devops-tools   (independent project)
```

## How Context Isolation Works

### Per-Terminal Context Selection
Each terminal can record to a different context:
```bash
# Terminal 1
mem0_on shared-backend
git commit -m "Backend API changes"

# Terminal 2  
mem0_on data-pipeline
python process_data.py
```

### Per-Editor Context Selection
Each editor sets its own context via environment variable:
```bash
# VS Code 1 (shares context with Terminal 1)
export MEM0_CONTEXT=shared-backend

# VS Code 2 (independent context)
export MEM0_CONTEXT=frontend-app

# JetBrains (independent context)
export MEM0_CONTEXT=mobile-app
```

### Multi-User Isolation
Each user sees only their own contexts:
```bash
# User A sees their contexts
./client/mem0 contexts
# Output: shared-backend, frontend-app

# User B sees their contexts  
./client/mem0 contexts
# Output: mobile-app, data-pipeline, devops-tools
```

## Power User Context Management

### View All Your Contexts
```bash
# List all contexts with status
./client/mem0 contexts

# List only active contexts
./client/mem0 contexts active

# Check current terminal context
./client/mem0 context active
```

### Context Recall for AI Agents
```bash
# AI agent recalls specific project context
./client/mem0 recall --context shared-backend

# AI agent recalls frontend work
./client/mem0 recall --context frontend-app
```

## Database Architecture

### User Isolation
- Each user has separate context namespaces
- Contexts are isolated by `user_id` in database
- No cross-user context visibility

### Context Independence  
- Multiple active contexts per user supported
- Each context tracks memories independently
- No interference between contexts

### Memory Storage
```sql
-- Memories are isolated by user_id and context
SELECT * FROM memories WHERE user_id = 1 AND context = 'shared-backend';
SELECT * FROM memories WHERE user_id = 2 AND context = 'mobile-app';
```

## Integration Points

### Terminal Integration
- Shell wrapper uses `MEM0_CONTEXT` environment variable
- Simple `mem0_on`/`mem0_off` commands per terminal
- Automatic context creation and management

### VS Code Integration
- Extension reads `MEM0_CONTEXT` from workspace environment
- Can override with workspace-specific settings
- Captures file operations, git actions, debug sessions

### JetBrains Integration  
- Plugin reads `MEM0_CONTEXT` from IDE environment
- Project-specific context configuration
- Captures build actions, test runs, refactoring operations

## Best Practices

### For Individual Developers
```bash
# Start recording for current project
cd ~/projects/my-app
mem0_on  # Uses 'my-app' as context name

# Work across multiple editors on same project
export MEM0_CONTEXT=my-app  # In all terminals/editors
```

### For Team Collaboration
```bash
# Each team member uses consistent context names
mem0_on team-project-backend
mem0_on team-project-frontend  
mem0_on team-project-mobile
```

### For Power Users
```bash
# Quick context switching
mem0_off && mem0_on new-project

# Context overview
./client/mem0 contexts | grep ACTIVE

# Bulk context management (future feature)
./client/mem0 contexts stop --all
```

## Limitations & Considerations

### Current Limitations
- No authentication system (single-user per server instance)
- Context names must be unique per user
- No context sharing between users

### Future Enhancements
- User authentication and authorization
- Context sharing and collaboration features
- Cross-context memory search and correlation
- Automated context detection based on git repositories

## Technical Implementation

### Environment Variable Priority
1. `MEM0_CONTEXT` environment variable (highest priority)
2. Active context from `mem0_on` command
3. Server's most recently created active context (fallback)

### API Endpoints
```
GET  /contexts          # List user's contexts
GET  /context/active    # Get active context
POST /context/start     # Start new context
POST /context/stop      # Stop context
GET  /memory?context=X  # Recall context memories
```

This architecture ensures complete isolation and flexibility for complex multi-editor, multi-user development scenarios while maintaining the simple CCTV observer philosophy.
