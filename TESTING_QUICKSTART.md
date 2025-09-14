# Ninaivalaigal (e^m) Testing Quickstart

## Prerequisites
1. **PostgreSQL Database** running locally
2. **Python environment** with dependencies installed
3. **VS Code** with MCP support (Windsurf/Cascade)

## Step 1: Database Setup
```bash
# Start PostgreSQL (if using Homebrew)
brew services start postgresql

# Create database and user
createdb ninaivalaigal_db
psql ninaivalaigal_db -c "CREATE USER ninaivalaigal_user WITH PASSWORD 'your_password';"
psql ninaivalaigal_db -c "GRANT ALL PRIVILEGES ON DATABASE ninaivalaigal_db TO ninaivalaigal_user;"

# Run schema creation
psql -U ninaivalaigal_user -d ninaivalaigal_db -f scripts/create-postgresql-schema.sql
psql -U ninaivalaigal_user -d ninaivalaigal_db -f scripts/create-team-merger-schema.sql
```

## Step 2: Environment Configuration
Create `.env` file in project root:
```bash
NINAIVALAIGAL_DATABASE_URL=postgresql://ninaivalaigal_user:your_password@localhost:5432/ninaivalaigal_db
NINAIVALAIGAL_JWT_SECRET=your-super-secret-jwt-key-min-32-chars
NINAIVALAIGAL_USER_TOKEN=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
NINAIVALAIGAL_DEBUG=true
```

## Step 3: VS Code MCP Configuration
**File: `.vscode/mcp.json`**
```json
{
  "mcpServers": {
    "e^m": {
      "command": "/opt/homebrew/anaconda3/bin/python",
      "args": ["/Users/asrajag/Workspace/mem0/server/mcp_server.py"],
      "env": {
        "NINAIVALAIGAL_DATABASE_URL": "postgresql://ninaivalaigal_user:your_password@localhost:5432/ninaivalaigal_db",
        "NINAIVALAIGAL_JWT_SECRET": "your-super-secret-jwt-key-min-32-chars",
        "NINAIVALAIGAL_USER_TOKEN": "your-jwt-token-here"
      }
    }
  }
}
```

## Step 4: Test MCP Server Standalone
```bash
# Test MCP server directly
cd /Users/asrajag/Workspace/mem0
python server/mcp_server.py

# Should show: "e^m MCP Server running on stdio"
```

## Step 5: Test Basic Memory Operations
In VS Code chat, try these commands:

### Basic Memory Operations
```
@e^m remember "Testing the Ninaivalaigal system setup" --context setup-test
@e^m recall --context setup-test
@e^m list_contexts
```

### Team Operations (if you have teams configured)
```
@e^m context_start team-project --scope team --team engineering
@e^m remember "Team collaboration test" --context team-project
@e^m cross_team_share_memory --context team-project --target-team frontend --justification "Testing cross-team sharing"
```

### Team Merger Operations (admin only)
```
@e^m team_merger_initiate --type consolidation --source-teams "old_team" --target-teams "new_team"
@e^m team_merger_status --merger-id 1
```

## Step 6: Verify All MCP Tools
Test that all 15+ MCP tools are available:
```
@e^m remember
@e^m recall  
@e^m context_start
@e^m context_stop
@e^m list_contexts
@e^m cross_team_share_memory
@e^m approve_cross_team_request
@e^m team_merger_initiate
@e^m team_merger_execute
@e^m team_merger_status
@e^m team_merger_rollback
@e^m enhance_prompt
@e^m get_relevant_memories
```

## Troubleshooting

### MCP Server Not Starting
```bash
# Check Python path
which python
/opt/homebrew/anaconda3/bin/python --version

# Test dependencies
pip install fastapi uvicorn sqlalchemy psycopg2-binary python-jose

# Check database connection
python -c "
import os
from sqlalchemy import create_engine
engine = create_engine('postgresql://ninaivalaigal_user:your_password@localhost:5432/ninaivalaigal_db')
print('Database connection successful!')
"
```

### VS Code MCP Issues
1. **Restart VS Code** after changing `.vscode/mcp.json`
2. **Check VS Code output panel** for MCP server logs
3. **Verify file paths** are absolute and correct
4. **Test with simple echo server** first

### Database Issues
```bash
# Check PostgreSQL status
brew services list | grep postgresql

# Test connection
psql -U ninaivalaigal_user -d ninaivalaigal_db -c "SELECT version();"

# Check tables exist
psql -U ninaivalaigal_user -d ninaivalaigal_db -c "\dt"
```

## Expected Results
- ✅ MCP server starts without errors
- ✅ All 15+ tools available in VS Code
- ✅ Memory operations work (remember/recall)
- ✅ Context management functional
- ✅ Team operations work (if configured)
- ✅ Database queries execute successfully

## Performance Benchmarks
- **Memory retrieval**: < 100ms
- **Context switching**: < 50ms  
- **Team merger initiation**: < 200ms
- **Cross-team sharing**: < 150ms

## Next Steps After Testing
1. **Configure real JWT tokens** for your users
2. **Set up team hierarchies** in database
3. **Test organizational merger scenarios**
4. **Deploy to production environment**
5. **Configure other IDEs** (Claude Desktop, JetBrains)

## IDE-Specific Configurations

### Claude Desktop
**File: `~/.config/claude-desktop/claude_desktop_config.json`**
```json
{
  "mcpServers": {
    "e^m": {
      "command": "/opt/homebrew/anaconda3/bin/python",
      "args": ["/Users/asrajag/Workspace/mem0/server/mcp_server.py"],
      "env": {
        "NINAIVALAIGAL_DATABASE_URL": "postgresql://ninaivalaigal_user:your_password@localhost:5432/ninaivalaigal_db",
        "NINAIVALAIGAL_JWT_SECRET": "your-super-secret-jwt-key-min-32-chars",
        "NINAIVALAIGAL_USER_TOKEN": "your-jwt-token-here"
      }
    }
  }
}
```

### Universal MCP Client (Any IDE)
```bash
# Use the universal shell script
./client/mem0-universal.sh remember "Universal test" --context universal-test
./client/mem0-universal.sh recall --context universal-test
```

This configuration works across **all MCP-compatible IDEs** with the same environment variables and server setup.
