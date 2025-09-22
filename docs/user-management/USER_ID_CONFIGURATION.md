# NINAIVALAIGAL_USER_ID Configuration Guide for Mem0 CCTV Recording

## Overview

The Ninaivalaigal system uses user IDs to associate recording contexts and memories with specific users. This ensures proper user isolation and context ownership.

## Configuration Methods

### 1. Environment Variable (Recommended)

Set the `NINAIVALAIGAL_USER_ID` environment variable to specify your user ID:

```bash
export NINAIVALAIGAL_USER_ID=123  # Your unique user ID
```

### 2. VS Code MCP Configuration

Add the user ID to your VS Code MCP configuration:

```json
{
  "mcpServers": {
    "Ninaivalaigal": {
      "command": "/opt/homebrew/anaconda3/bin/python3.11",
      "args": ["/Users/asrajag/Workspace/Ninaivalaigal/server/mcp_server.py"],
      "env": {
        "NINAIVALAIGAL_DATABASE_URL": "postgresql://ninaivalaigaluser:ninaivalaigalpass@localhost:5432/ninaivalaigaldb",
        "NINAIVALAIGAL_JWT_SECRET": "your-secure-jwt-secret",
        "NINAIVALAIGAL_USER_ID": "123"
      }
    }
  }
}
```

### 3. Shell Configuration

Add to your shell profile (`.bashrc`, `.zshrc`, etc.):

```bash
# Ninaivalaigal Configuration
export NINAIVALAIGAL_USER_ID=123
export NINAIVALAIGAL_DATABASE_URL="postgresql://ninaivalaigaluser:ninaivalaigalpass@localhost:5432/ninaivalaigaldb"
export NINAIVALAIGAL_JWT_SECRET="your-secure-jwt-secret"
```

## User ID Assignment

### Development/Single User
- Default: `NINAIVALAIGAL_USER_ID=1`
- All contexts and memories will be associated with user ID 1

### Multi-User Team Deployment
- Each team member gets a unique user ID
- Example assignments:
  - Alice: `NINAIVALAIGAL_USER_ID=101`
  - Bob: `NINAIVALAIGAL_USER_ID=102`
  - Carol: `NINAIVALAIGAL_USER_ID=103`

### Enterprise/Organization Deployment
- Use your existing user management system IDs
- Examples:
  - Employee ID: `NINAIVALAIGAL_USER_ID=12345`
  - LDAP UID: `NINAIVALAIGAL_USER_ID=67890`
  - Database user ID: `NINAIVALAIGAL_USER_ID=555`

## How User ID Association Works

### Context Recording
When you start CCTV recording:
```bash
# Via MCP
@Ninaivalaigal context_start my-project

# Via FastAPI
curl -X POST "http://localhost:8000/context/start" \
  -H "Content-Type: application/json" \
  -d '{"context": "my-project"}'
```

The system automatically:
1. Reads `NINAIVALAIGAL_USER_ID` from environment
2. Associates the recording context with your user ID
3. All captured interactions are tagged with your user ID

### Memory Storage
All memories stored include:
- **Context**: Project/session context name
- **User ID**: Your unique identifier
- **Timestamp**: When the memory was created
- **Content**: The actual memory data

### Memory Retrieval
When recalling memories:
- System only returns memories belonging to your user ID
- Hierarchical recall respects user boundaries:
  - **Personal**: Your individual memories
  - **Team**: Shared memories within your team
  - **Organization**: Company-wide accessible memories

## User Isolation

### Security Features
- **Complete Isolation**: User A cannot access User B's contexts or memories
- **Database Level**: User ID enforced in all database queries
- **API Level**: All endpoints respect user ID boundaries
- **MCP Level**: All tools operate within user's scope

### Context Ownership
- Each context belongs to a specific user ID
- Multiple users can have contexts with the same name
- Examples:
  - User 101: `authentication-project`
  - User 102: `authentication-project` (different context, same name)

## Troubleshooting

### Missing User ID
If `NINAIVALAIGAL_USER_ID` is not set:
- System defaults to user ID `1`
- Warning message in logs
- All contexts/memories associated with default user

### User ID Changes
If you change your user ID:
- Previous contexts/memories remain with old user ID
- New recordings use the new user ID
- No automatic migration between user IDs

### Multi-Session Issues
If running multiple sessions:
- Each session should have the same `NINAIVALAIGAL_USER_ID`
- Different user IDs will create separate isolated contexts
- Use consistent environment variable across all sessions

## Best Practices

### Development
```bash
# Single developer
export NINAIVALAIGAL_USER_ID=1
```

### Team Development
```bash
# Each developer has unique ID
# Alice
export NINAIVALAIGAL_USER_ID=101

# Bob
export NINAIVALAIGAL_USER_ID=102
```

### Production Deployment
```bash
# Use your organization's user management system
export NINAIVALAIGAL_USER_ID=your_user_id  # Unix user ID
# or
export NINAIVALAIGAL_USER_ID=$EMPLOYEE_ID  # Company employee ID
```

### Context Naming
- Use descriptive context names: `project-auth`, `bug-fix-session`
- Include project/feature identifiers
- Avoid generic names like `work` or `dev`

## Integration Examples

### VS Code Workspace Settings
Create `.vscode/settings.json` in your project:
```json
{
  "terminal.integrated.env.osx": {
    "NINAIVALAIGAL_USER_ID": "123"
  },
  "terminal.integrated.env.linux": {
    "NINAIVALAIGAL_USER_ID": "123"
  },
  "terminal.integrated.env.windows": {
    "NINAIVALAIGAL_USER_ID": "123"
  }
}
```

### Docker Deployment
```dockerfile
ENV NINAIVALAIGAL_USER_ID=123
ENV NINAIVALAIGAL_DATABASE_URL=postgresql://ninaivalaigaluser:ninaivalaigalpass@db:5432/ninaivalaigaldb
ENV NINAIVALAIGAL_JWT_SECRET=your-secure-jwt-secret
```

### CI/CD Pipeline
```yaml
environment:
  NINAIVALAIGAL_USER_ID: ${{ secrets.NINAIVALAIGAL_USER_ID }}
  NINAIVALAIGAL_DATABASE_URL: ${{ secrets.NINAIVALAIGAL_DATABASE_URL }}
  NINAIVALAIGAL_JWT_SECRET: ${{ secrets.NINAIVALAIGAL_JWT_SECRET }}
```

This configuration ensures that your CCTV recording contexts and memories are properly associated with your user identity, providing secure isolation and proper context ownership.
