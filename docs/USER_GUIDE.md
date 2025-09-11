# mem0 User Guide

## Welcome to mem0

**mem0** is your intelligent memory layer for AI-assisted development. It captures, organizes, and shares development context to enhance collaboration between humans and AI agents. Whether you're working solo, in a team, or across organizations, mem0 keeps everyone aligned and productive.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Authentication & User Management](#authentication--user-management)
3. [Personal Memory Management](#personal-memory-management)
4. [Team Collaboration](#team-collaboration)
5. [Organization-Wide Sharing](#organization-wide-sharing)
6. [Advanced Workflows](#advanced-workflows)
7. [Security & Privacy](#security--privacy)
8. [Troubleshooting](#troubleshooting)
9. [Best Practices](#best-practices)

## Quick Start

### 1. Get Started in 5 Minutes

```bash
# Start the server
./manage.sh start

# Register and login
./client/mem0 auth register --username yourname --password yourpass --email you@domain.com
./client/mem0 auth login --username yourname --password yourpass

# Create your first context
./client/mem0 context-create --name "my-first-project" --description "Learning mem0" --visibility private

# Enable shell integration
source client/mem0.zsh

# Start recording
mem0_context_start my-first-project

# Work normally - commands are captured automatically
echo "Hello mem0!"
git status

# View captured memories
./client/mem0 recall --context my-first-project
```

**That's it!** You're now capturing and recalling development context.

### 2. Core Concepts

#### Contexts
- **What**: Named containers for memories (commands, notes, decisions)
- **Why**: Organize work by project, feature, or task
- **How**: Create, share, and manage contexts with different visibility levels

#### Memories
- **What**: Captured development activities and knowledge
- **Types**: Commands, notes, decisions, errors, solutions
- **Sources**: Shell commands, manual entries, file changes, AI interactions

#### Sharing Levels
- **Personal**: Private to you only
- **Team**: Shared with team members
- **Organization**: Available to entire organization
- **Public**: Open to all authenticated users

## Authentication & User Management

### User Registration

```bash
# Register a new account
./client/mem0 auth register \
  --username alice \
  --password securepass123 \
  --email alice@company.com

# Login to your account
./client/mem0 auth login \
  --username alice \
  --password securepass123
```

### Managing Your Profile

```bash
# View your profile information
./client/mem0 auth me

# Logout from current session
./client/mem0 auth logout
```

### Security Best Practices

- Use strong, unique passwords
- Enable 2FA when available
- Regularly review your active sessions
- Share contexts thoughtfully

## Architecture Overview

mem0 now runs a **dual-server architecture**:

### FastAPI Server (Port 13370)
- **Purpose**: REST API for CLI, shell integration, and VS Code extension
- **Endpoints**: `/contexts`, `/memory`, `/memory/all`, etc.
- **Usage**: Traditional HTTP clients and existing integrations

## Personal Memory Management

### Creating Personal Contexts

```bash
# Create a private context for personal projects
./client/mem0 context-create \
  --name "personal-research" \
  --description "Research and learning activities" \
  --visibility private

# Create context for side projects
./client/mem0 context-create \
  --name "side-project-ideas" \
  --description "Ideas for future projects" \
  --visibility private
```

### Working with Personal Memories

```bash
# Start recording to a personal context
mem0_context_start personal-research

# Work normally - all commands captured
cd ~/research
python analyze_data.py
git commit -m "Add data analysis"

# Manually add memories
./client/mem0 remember "Key insight: Algorithm X performs 2x better" --context personal-research

# View your memories
./client/mem0 recall --context personal-research

# Search through memories
./client/mem0 recall --context personal-research --query "algorithm"
```

### Organizing Personal Work

```bash
# List all your contexts
./client/mem0 context list

# Switch between contexts
mem0_context_start side-project-ideas
# Work on different project
mem0_context_start personal-research
# Back to research

# Clean up completed contexts
./client/mem0 context delete completed-project
```

## Team Collaboration

### Setting Up Team Structure

```bash
# Create organization (admin only)
./client/mem0 org create \
  --name "Acme Corp" \
  --description "Leading tech company"

# Create team within organization
./client/mem0 team create \
  --name "Frontend Team" \
  --org-id 1 \
  --description "React and UI development"
```

### Managing Team Membership

```bash
# Add team member with specific role
./client/mem0 team add-member \
  --team-id 1 \
  --user-id 2 \
  --role admin

# View team members and roles
./client/mem0 team members --team-id 1

# See which teams you belong to
./client/mem0 team list
```

### Collaborative Workflows

#### Creating Team Contexts

```bash
# Create team-shared context
./client/mem0 context-create \
  --name "sprint-planning" \
  --description "Q4 Sprint planning and execution" \
  --visibility team

# Share with team automatically (due to visibility setting)
# All team members can now access this context
```

#### Team Memory Capture

```bash
# Start team context
mem0_context_start sprint-planning

# Team members work collaboratively
# All commands and notes are captured in shared context
git pull origin main
npm install new-dependency
./client/mem0 remember "Decision: Use React Query for state management"

# View team memories
./client/mem0 recall --context sprint-planning
```

#### Sharing Contexts with Teams

```bash
# Share existing context with team
./client/mem0 share \
  --context-id 1 \
  --target-type team \
  --target-id 1 \
  --permission write

# Grant different permission levels
# Read-only access
./client/mem0 share \
  --context-id 2 \
  --target-type team \
  --target-id 2 \
  --permission read

# Admin access
./client/mem0 share \
  --context-id 3 \
  --target-type team \
  --target-id 1 \
  --permission admin
```

### Team Roles and Permissions

- **Owner**: Full control, can share and delete
- **Admin**: Can manage team settings and sharing
- **Member**: Can read/write to shared contexts
- **Viewer**: Read-only access to team contexts

## Organization-Wide Sharing

### Organization Setup

```bash
# Create organization (typically done by admin)
./client/mem0 org create \
  --name "Global Tech Corp" \
  --description "International technology company"

# View available organizations
./client/mem0 org list
```

### Organization-Wide Contexts

```bash
# Create organization-wide knowledge base
./client/mem0 context-create \
  --name "company-knowledge" \
  --description "Company-wide documentation and knowledge" \
  --visibility organization

# Create shared tooling context
./client/mem0 context-create \
  --name "dev-tools" \
  --description "Shared development tools and configurations" \
  --visibility organization
```

### Cross-Team Collaboration

```bash
# Share context across teams
./client/mem0 share \
  --context-id 1 \
  --target-type team \
  --target-id 1 \
  --permission write  # Frontend team

./client/mem0 share \
  --context-id 1 \
  --target-type team \
  --target-id 2 \
  --permission write  # Backend team

./client/mem0 share \
  --context-id 1 \
  --target-type team \
  --target-id 3 \
  --permission read   # QA team
```

### Organization Knowledge Management

```bash
# Create knowledge base contexts
./client/mem0 context-create \
  --name "engineering-standards" \
  --description "Coding standards and best practices" \
  --visibility organization

./client/mem0 context-create \
  --name "product-roadmap" \
  --description "Company product strategy and roadmap" \
  --visibility organization

# Populate with knowledge
./client/mem0 remember "API Design: Use RESTful conventions" --context engineering-standards
./client/mem0 remember "Q4 Goal: Launch mobile app" --context product-roadmap
```

## Advanced Workflows

### Multi-Project Development

```bash
# Developer working on multiple projects
mem0_context_start project-alpha
# Work on alpha project
cd ~/projects/alpha
git status

mem0_context_start project-beta
# Switch to beta project
cd ~/projects/beta
npm run build

# Both contexts capture separate work streams
```

### Cross-Organization Projects

```bash
# Create cross-org team for joint venture
./client/mem0 team create \
  --name "Joint-Venture-Team" \
  --description "Cross-company collaboration"

# Add members from different organizations
./client/mem0 team add-member --team-id 5 --user-id 10 --role member
./client/mem0 team add-member --team-id 5 --user-id 15 --role admin

# Share project context
./client/mem0 share \
  --context-id 10 \
  --target-type team \
  --target-id 5 \
  --permission write
```

### AI-Assisted Development

```bash
# Context for AI collaboration
./client/mem0 context-create \
  --name "ai-assistant-session" \
  --description "Working with GitHub Copilot and other AI tools" \
  --visibility private

# Capture AI interactions
./client/mem0 remember "Copilot suggested: Use TypeScript interfaces" --context ai-assistant-session
./client/mem0 remember "AI Review: Code follows SOLID principles" --context ai-assistant-session
```

### Knowledge Transfer Sessions

```bash
# Create context for onboarding
./client/mem0 context-create \
  --name "new-hire-onboarding" \
  --description "Knowledge transfer for new team members" \
  --visibility team

# Capture onboarding activities
mem0_context_start new-hire-onboarding
# Demonstrate workflows
# Answer questions
# Share best practices

# New hires can review later
./client/mem0 recall --context new-hire-onboarding
```

## Security & Privacy

### Data Isolation

- **User Isolation**: Complete separation between user data
- **Context Boundaries**: Memories only accessible to authorized users
- **Audit Trail**: Track who accesses what and when

### Permission Management

```bash
# Check what contexts you can access
./client/mem0 context list

# Verify your permissions (API call)
curl -H "Authorization: Bearer $(cat ~/.mem0/auth.json | jq -r .token)" \
  http://127.0.0.1:13370/users/me/contexts
```

### Security Best Practices

- **Regular Audits**: Review context sharing regularly
- **Principle of Least Privilege**: Grant minimum required permissions
- **Context Cleanup**: Delete unused contexts and memories
- **Secure Sharing**: Never share sensitive information inappropriately

### Per-Terminal Context Selection

Set the `MEM0_CONTEXT` environment variable to specify which context should receive commands in that terminal:

```bash
# Terminal captures to 'project-alpha'
export MEM0_CONTEXT=project-alpha
echo "Working on alpha features"

# Terminal captures to 'project-beta'  
export MEM0_CONTEXT=project-beta
echo "Testing beta functionality"
```

**Fallback Behavior:** If `MEM0_CONTEXT` is not set, commands are captured to the most recently created active context.

## Memory Operations

### Recall Commands
```bash
# Recall from active context
./client/mem0 recall

# Recall from specific context
./client/mem0 recall --context project-name

# Export memories to file
./client/mem0 export --context project-name --output project-history.json
```

### Manual Memory Addition
```bash
# Add a custom memory entry
./client/mem0 remember "Deployed version 2.1.0 to production" --context deployment-log
```

## Best Practices

### 1. Context Naming
- Use descriptive names: `frontend-redesign`, `api-v2`, `bug-fix-auth`
- Avoid spaces: Use hyphens or underscores
- Include version/iteration: `mobile-app-v1`, `database-migration-2024`

### 2. Multi-Project Workflows
- **One context per project/feature**: Keep work isolated
- **Use environment variables**: Set `MEM0_CONTEXT` in each terminal
- **Regular cleanup**: Delete old contexts when projects are complete

### 3. Team Collaboration
- **Consistent naming**: Agree on context naming conventions
- **Export/share**: Use export feature to share command histories
- **Documentation**: Include context names in project documentation

## Troubleshooting

### Commands Not Being Captured
1. **Check if context is active:**
   ```bash
   ./client/mem0 contexts
   ```

2. **Verify shell integration:**
   ```bash
   echo $MEM0_DEBUG
   # Should show debug output if set to 1
   ```

3. **Re-source shell wrapper:**
   ```bash
   source ~/Workspace/mem0/client/mem0.zsh
   ```

### Multiple Active Contexts
This is normal! You can have multiple active contexts simultaneously. Use `MEM0_CONTEXT` to control which context receives commands in each terminal.

### Server Connection Issues
1. **Check server status:**
   ```bash
   ./manage.sh status
   ```

2. **Restart server:**
   ```bash
   ./manage.sh restart
   ```

3. **Check port availability:**
   ```bash
   lsof -i :13370
   ```

### Context Not Found
- Verify context exists: `./client/mem0 contexts`
- Check spelling and case sensitivity
- Create context if needed: `./client/mem0 context start <name>`

## Advanced Configuration

### Environment Variables
- `MEM0_CONTEXT`: Specify context for current terminal
- `MEM0_DEBUG`: Enable debug logging (set to 1)
- `MEM0_PORT`: Override server port (default: 13370)

### Configuration File
Edit `mem0.config.json` to customize:
- Server host/port settings
- Cache TTL for context lookups
- Command capture patterns
- Storage options

## Examples

### Daily Development Workflow
```bash
# Morning setup
./manage.sh start
source ~/Workspace/mem0/client/mem0.zsh

# Start working on feature
export MEM0_CONTEXT=user-authentication
./client/mem0 context start user-authentication

# Development work
git checkout -b feature/auth
npm install passport
# ... more commands ...

# End of day - review work
./client/mem0 recall --context user-authentication
```

### Bug Investigation
```bash
# Create investigation context
export MEM0_CONTEXT=bug-login-issue
./client/mem0 context start bug-login-issue

# Investigation commands
grep -r "login" logs/
docker logs app-container
curl -X POST /api/login

# Later - recall investigation steps
./client/mem0 recall --context bug-login-issue
```

### Code Review Preparation
```bash
# Export command history for code review
./client/mem0 export --context feature-implementation --output review-commands.json

# Share with team or include in PR description
```

## Editor Integration

### Terminal Integration
**Setup (once per terminal):**
```bash
source client/mem0.zsh
```

**Commands:**
```bash
mem0_on [project-name]    # Start recording (uses directory name if not specified)
mem0_off                  # Stop recording
export MEM0_CONTEXT=name  # Set context for this terminal
```

### VS Code Integration
**Setup:**
1. Install mem0 VS Code extension from marketplace
2. Set workspace environment variable in `.vscode/settings.json`:
```json
{
  "terminal.integrated.env.osx": {
    "MEM0_CONTEXT": "my-project"
  },
  "terminal.integrated.env.linux": {
    "MEM0_CONTEXT": "my-project"
  },
  "terminal.integrated.env.windows": {
    "MEM0_CONTEXT": "my-project"
  }
}
```

**What gets captured:**
- File operations (create, edit, delete, rename)
- Git operations (commit, push, pull, branch)
- Debug sessions (breakpoints, variable inspection)
- Terminal commands within VS Code
- Extension installations and configurations

**Commands:**
```bash
# In VS Code integrated terminal
mem0_on my-vscode-project
# Work normally - all actions captured
mem0_off
```

### JetBrains Integration (IntelliJ, PyCharm, WebStorm)
**Setup:**
1. Install mem0 plugin from JetBrains marketplace
2. Configure project-specific context in Settings > Tools > mem0:
   - Context Name: `my-jetbrains-project`
   - Auto-start recording: ✓

**What gets captured:**
- Build operations (compile, package, deploy)
- Test runs (unit tests, integration tests)
- Refactoring operations (rename, extract method, move class)
- Code generation (templates, auto-completion usage)
- VCS operations (commit, merge, rebase)
- Plugin installations and configurations

**Commands:**
```bash
# Set context for JetBrains project
export MEM0_CONTEXT=my-jetbrains-project

# Or use IDE settings to auto-set context
# Tools > mem0 > Start Recording
```

## Integration with Development Tools

### Git Integration
mem0 works seamlessly with git workflows:
```bash
export MEM0_CONTEXT=feature-branch-name
git checkout -b feature/new-api
# Commands automatically captured to context
```

### Docker Development
```bash
export MEM0_CONTEXT=docker-setup
docker build -t myapp .
docker run -p 8080:8080 myapp
docker logs myapp
# All docker commands captured for later reference
```

### Testing Workflows
```bash
export MEM0_CONTEXT=test-suite-run
pytest tests/ -v
npm test
coverage report
# Test commands and results captured
```
