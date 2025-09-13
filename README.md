# Ninaivalaigal - e^M Agentic Execution Engine

**Exponential Memory: commands, compounding memory, exponential action**

*By Medhays (www.medhasys.com)*

## Overview

Ninaivalaigal provides an exponential memory system that allows AI assistants and developers to remember context, conversations, and insights across sessions. The e^M (exponential Memory) engine acts as a "CCTV for your AI interactions" - automatically recording and making searchable your development history with compound learning effects.

## Architecture

### Core Components

- **Server**: FastAPI-based headless API server with JWT authentication and advanced sharing (Python)
- **Client**: CLI tool with shell integration, authentication, and collaboration features
- **VS Code Extension**: IDE integration with persistent context state
- **Database**: PostgreSQL with multi-user support, organizations, teams, and sharing permissions
- **MCP Server**: Model Context Protocol implementation for AI tool integration

### Key Features

- **JWT Authentication**: Secure user authentication with token-based access
- **Multi-Level Sharing**: Personal, team, and organization-level context sharing
- **Role-Based Permissions**: Owner, admin, member, and viewer roles
- **Organization Management**: Create and manage organizations with teams
- **Context Ownership**: Contexts can be owned by users, teams, or organizations
- **Automatic Command Capture**: Shell integration via zsh hooks
- **Multi-Context Support**: Multiple active contexts per user with per-terminal selection
- **Performance Optimized**: Intelligent caching and background processing
- **Cross-Platform**: Works across different development environments

## Quick Start

### 1. Start the Server

```bash
./manage.sh start
```

The server will start on `http://127.0.0.1:13370`

### 2. Register and Authenticate

```bash
# Register a new user
./client/mem0 auth register --username alice --password secure123 --email alice@company.com

# Login (this saves your authentication token)
./client/mem0 auth login --username alice --password secure123
```

### 3. Create Organization and Teams

```bash
# Create organization
./client/mem0 org create --name "Acme Corp" --description "Tech Company"

# Create team
./client/mem0 team create --name "Frontend Team" --org-id 1 --description "UI/UX Team"

# Add team member
./client/mem0 team add-member --team-id 1 --user-id 2 --role member
```

### 4. Create and Share Contexts

```bash
# Create personal context
./client/mem0 context-create --name "my-project" --description "Personal project" --visibility private

# Create team-shared context
./client/mem0 context-create --name "team-project" --description "Team collaboration" --visibility team

# Share context with another user
./client/mem0 share --context-id 1 --target-type user --target-id 2 --permission write

# Share context with team
./client/mem0 share --context-id 1 --target-type team --target-id 1 --permission read
```

### 5. Enable Shell Integration

```bash
source client/mem0.zsh
export NINAIVALAIGAL_DEBUG=1  # Optional: Enable debug logging
```

### 6. Start Recording and Work

```bash
# Start recording to context
./client/mem0 context start my-project

# Work normally - commands auto-captured
git status
npm install
python main.py

# Stop recording
./client/mem0 context stop
```

### 7. View Captured Memories

```bash
# View memories from context
./client/mem0 recall --context my-project

# View all accessible contexts
./client/mem0 context list
```

## Multi-Level Sharing & Collaboration

### Personal Contexts (Private)
```bash
# Create personal context
./client/mem0 context-create --name "personal-notes" --visibility private

# Only you can access this context
./client/mem0 remember "My private thought" --context personal-notes
```

### Team Collaboration
```bash
# Create team-shared context
./client/mem0 context-create --name "team-sprint" --visibility team

# Share with specific team
./client/mem0 share --context-id 1 --target-type team --target-id 1 --permission write

# All team members can collaborate
./client/mem0 remember "Sprint planning notes" --context team-sprint
```

### Organization-Wide Sharing
```bash
# Create organization-wide context
./client/mem0 context-create --name "company-knowledge" --visibility organization

# Automatically shared with all organization members
./client/mem0 share --context-id 2 --target-type organization --target-id 1 --permission read
```

### Cross-Team Projects
```bash
# Share context with multiple teams
./client/mem0 share --context-id 3 --target-type team --target-id 1 --permission write  # Frontend team
./client/mem0 share --context-id 3 --target-type team --target-id 2 --permission write  # Backend team
./client/mem0 share --context-id 3 --target-type team --target-id 3 --permission read   # QA team
```

## CLI Commands

### Authentication
- `./client/mem0 auth register --username <name> --password <pwd> --email <email>` - Register new user
- `./client/mem0 auth login --username <name> --password <pwd>` - Login and save token
- `./client/mem0 auth logout` - Logout and clear token
- `./client/mem0 auth me` - Show current user information

### Organization Management
- `./client/mem0 org create --name <name> --description <desc>` - Create organization
- `./client/mem0 org list` - List all organizations

### Team Management
- `./client/mem0 team create --name <name> --org-id <id> --description <desc>` - Create team
- `./client/mem0 team add-member --team-id <id> --user-id <id> --role <role>` - Add team member
- `./client/mem0 team members --team-id <id>` - List team members
- `./client/mem0 team list` - List your teams

### Context Management
- `./client/mem0 context-create --name <name> --description <desc> --visibility <level>` - Create context with ownership
- `./client/mem0 context start <name>` - Start recording to a context
- `./client/mem0 context stop [<name>]` - Stop specific or current recording session
- `./client/mem0 context delete <name>` - Delete a context and all its memories
- `./client/mem0 context active` - Show terminal context (NINAIVALAIGAL_CONTEXT env var)
- `./client/mem0 contexts` - List all contexts with status

### Memory Operations
- `./client/mem0 remember '<json>'` - Store a memory entry
- `./client/mem0 recall [--context <name>]` - Retrieve memories

### Sharing & Permissions
- `./client/mem0 share --context-id <id> --target-type <type> --target-id <id> --permission <level>` - Share context
- `./client/mem0 context list` - List all accessible contexts

## Shell Integration Features

### Performance Optimization
- **Context Caching**: Reduces API calls by caching active context for 30 seconds
- **Background Processing**: Command capture runs asynchronously
- **Smart Filtering**: Only captures commands when recording is active

### Cache Management
- `mem0_clear_cache` - Clear the context cache manually
- Cache automatically expires after 30 seconds
- Cache is updated when context changes

### Debug Mode
Enable debug logging to troubleshoot shell integration:

```bash
export NINAIVALAIGAL_DEBUG=1
source client/mem0.zsh
```

Debug output shows:
- Hook triggers
- Cache hits/misses
- API responses
- Payload construction
- Command submission status

## VS Code Extension

The VS Code extension provides IDE integration through a chat participant.

### Setup
1. Configure the project root in VS Code settings:
   ```json
   {
     "mem0.projectRoot": "/absolute/path/to/mem0/project"
   }
   ```

2. Use the `@e^M` chat participant in VS Code

### Available Commands
- `@e^M remember <data>` - Store a memory
- `@e^M recall` - Retrieve memories
- `@e^M observe` - Observe chat history

## Configuration

### Environment Variables
- `NINAIVALAIGAL_PORT` - Server port (default: 13370)
- `NINAIVALAIGAL_DEBUG` - Enable debug logging (set to 1)
- `NINAIVALAIGAL_CONTEXT` - Specify context for current terminal session
- `NINAIVALAIGAL_SECRET_KEY` - JWT secret key for authentication

### Shell Integration Settings
- `NINAIVALAIGAL_CACHE_TTL` - Context cache duration in seconds (default: 30)

## Security & Permissions

### Permission Levels
- **Read**: View memories and context information
- **Write**: Create/modify memories in the context
- **Admin**: Manage sharing permissions and context settings
- **Owner**: Full control including deletion and ownership transfer

### Sharing Hierarchy
1. **Personal**: Private contexts owned by individual users
2. **Team**: Shared within specific teams with role-based access
3. **Organization**: Shared across entire organizations
4. **Public**: Accessible to all authenticated users

### User Roles
- **Owner**: Full control over owned resources
- **Admin**: Manage team/organization resources
- **Member**: Standard team member with write access
- **Viewer**: Read-only access to shared resources

## Development

### Dependencies

**Server:**
- FastAPI
- Uvicorn
- Pydantic
- SQLAlchemy
- Psycopg2-binary
- Bcrypt
- Python-jose[cryptography]

**Client:**
- requests

**VS Code Extension:**
- TypeScript
- VS Code API

### Testing

Run the test suite:

```bash
# Basic functionality test
./tests/run_test.sh

# Context management test
./tests/run_context_test.sh

# Session recording test
./tests/run_session_test.sh

# Authentication and sharing tests
./tests/test_sharing.py
```

### Project Structure

```
mem0/
├── server/           # FastAPI server with authentication & sharing
│   ├── main.py      # Server implementation with JWT auth
│   ├── database.py  # Database models and sharing logic
│   ├── auth.py      # Authentication middleware
│   └── requirements.txt
├── client/          # CLI tool with sharing features
│   ├── mem0         # Python CLI script with auth
│   ├── mem0.zsh     # Zsh integration with context isolation
│   └── requirements.txt
├── vscode-client/   # VS Code extension
│   ├── src/
│   └── package.json
├── tests/           # Test scripts
│   ├── TEST_CASES.md # Comprehensive test cases
│   ├── run_environment_tests.sh
│   └── test_sharing.py
├── docs/           # Documentation
│   ├── STATE.md    # Development state tracking
│   └── USER_GUIDE.md # User guide with examples
├── deploy/         # Deployment scripts and configs
│   ├── mem0-complete-deployment.yml
│   └── templates/
└── manage.sh       # Server management script
```

## Vision

mem0 transforms the messy, iterative development process into structured data that can be used for:

1. **Individual Productivity**: Personal knowledge management and task tracking
2. **Team Collaboration**: Shared project knowledge and collaborative workflows
3. **Organization Knowledge**: Company-wide knowledge sharing and documentation
4. **AI Agent Memory**: Provide persistent memory for AI development assistants
5. **Workflow Automation**: Convert development sessions into Ansible playbooks

## Contributing

The system is designed with three key principles:

1. **From Developer to Automation**: Capture development workflows for automation
2. **From Individual to Team**: Scale from personal use to team collaboration
3. **From UI to CLI**: API-first design with thin client interfaces
4. **From Personal to Enterprise**: Multi-level sharing with proper security

## License

[Add your license information here]
