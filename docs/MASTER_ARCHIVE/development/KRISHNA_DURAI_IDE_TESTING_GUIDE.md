# Krishna & Durai IDE Testing Guide
**For Testing VS Code, JetBrains, and IDE Integrations with Ninaivalaigal e^M**

*Part of Ninaivalaigal by Medhays (www.medhasys.com)*

## 🎯 **What Krishna and Durai Need to Test**

### **Prerequisites (5 minutes)**
1. **Get your JWT token** from the web dashboard:
   - Login at `http://localhost:8000/login`
   - Copy token from "API Access Token" section
   - Export it: `export MEM0_USER_TOKEN="your-jwt-token-here"`

2. **Verify servers are running**:
   ```bash
   # Check FastAPI server
   curl http://localhost:8000/user/info -H "Authorization: Bearer $MEM0_USER_TOKEN"

   # Check MCP server
   ps aux | grep mcp_server
   ```

## 🔧 **VS Code Extension Testing**

### **Step 1: Install Extension**
```bash
cd /Users/asrajag/Workspace/mem0/vscode-client
npm install
npm run package
code --install-extension mem0-vscode-0.1.0.vsix
```

### **Step 2: Configure VS Code**
Create `.vscode/settings.json` in your test project:
```json
{
  "ninaivalaigal.serverUrl": "http://localhost:8000",
  "ninaivalaigal.context": "krishna-test-project",
  "ninaivalaigal.userToken": "your-jwt-token-here"
}
```

### **Step 3: Test VS Code Chat Integration**
1. Open VS Code chat panel (`Ctrl+Shift+I` or `Cmd+Shift+I`)
2. Test these commands:
   ```
   @e^M context start my-project
   @e^M remember "Added user authentication with JWT tokens"
   @e^M recall authentication
   @e^M context list
   ```

### **Expected Results:**
- ✅ Extension connects to Ninaivalaigal server
- ✅ Context creation works
- ✅ Memory storage and recall functions
- ✅ JWT authentication is handled automatically

## 🔧 **JetBrains Plugin Testing**

### **Step 1: Build Plugin**
```bash
cd /Users/asrajag/Workspace/mem0/jetbrains-plugin
./gradlew buildPlugin
```

### **Step 2: Install in IDE**
1. Open IntelliJ IDEA/PyCharm/WebStorm
2. Go to: `Settings → Plugins → Install from disk`
3. Select: `build/distributions/mem0-jetbrains-0.1.0.zip`
4. Restart IDE

### **Step 3: Configure Plugin**
1. Go to: `Settings → Tools → Ninaivalaigal`
2. Set:
   - **Server URL**: `http://localhost:8000`
   - **User Token**: `your-jwt-token-here`
   - **Default Context**: `krishna-jetbrains-test`

### **Step 4: Test Plugin Features**
1. **Keyboard Shortcuts**:
   - Select code → `Ctrl+Shift+M` (Remember)
   - `Ctrl+Shift+R` (Recall)

2. **Context Menu**:
   - Right-click in editor → "Remember Selection"
   - Tools menu → mem0 actions

3. **Tool Window**:
   - View → Tool Windows → Ninaivalaigal
   - Check current context and memories

### **Expected Results:**
- ✅ Plugin connects to Ninaivalaigal server with JWT
- ✅ Code selection remembering works
- ✅ Memory recall displays in tool window
- ✅ Context switching functions

## 🔧 **MCP Server Testing (Advanced)**

### **Step 1: Configure Claude Desktop**
Edit `~/.config/claude-desktop/claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "ninaivalaigal": {
      "command": "/opt/homebrew/anaconda3/bin/python",
      "args": ["/Users/asrajag/Workspace/mem0/server/mcp_server.py"],
      "env": {
        "NINAIVALAIGAL_DATABASE_URL": "postgresql://ninaivalaigal_user:ninaivalaigal_pass@localhost:5432/ninaivalaigal_db",
        "NINAIVALAIGAL_JWT_SECRET": "FcbdlNhk9AlKmeGjDNVmZK3CK12UZdQRrdaG1i8xesk"
      }
    }
  }
}
```

### **Step 2: Test MCP Tools**
In Claude Desktop or MCP-enabled IDE:
```bash
# Test basic memory operations
@e^M remember "Test memory for debugging"
@e^M recall "test"
@e^M context_start "mcp-test-project"
@e^M approve_cross_team_request request_id=1

# Test AI enhancement
@e^M enhance_ai_prompt_tool file_path="shared.js" language="javascript" prompt="Implement shared function" user_id=1 team_id=1_model="claude"
```

### **Expected Results:**
- ✅ MCP tools are available in chat
- ✅ Memory operations work with authentication
- ✅ AI prompt enhancement includes memories

## 📋 **Test Scenarios for Krishna & Durai**

### **Scenario 1: Basic Workflow**
```bash
# 1. Start new context
@e^M context start "user-auth-feature"

# 2. Remember design decisions
@e^M remember "Using JWT tokens for stateless authentication"
@e^M remember "Password hashing with bcrypt for security"

# 3. Code and remember implementation
# Select code in IDE → Ctrl+Shift+M
# Remember: "Implemented login endpoint with error handling"

# 4. Recall when needed
@e^M recall "authentication"
# Should show all auth-related memories
```

### **Scenario 2: Cross-Context Testing**
```bash
# Test context isolation
@e^M context start "frontend-project"
@e^M remember "Your coding preference"
@e^M context_start "project-name"
@e^M remember "Using FastAPI with PostgreSQL"

# Switch contexts and verify isolation
@e^M context switch "frontend-project"
@e^M list_contexts
@e^M recall "search term"  # Should only show frontend memories

@e^M context switch "backend-project"
@e^M recall "fastapi"  # Should only show backend memories
```

### **Scenario 3: Multi-IDE Testing**
1. **VS Code**: Create memories using chat commands
2. **JetBrains**: Recall same memories using tool window
3. **Claude Desktop**: Use memories for AI enhancement
4. **Verify**: All IDEs see the same memory data

## 🚨 **Troubleshooting Guide**

### **VS Code Extension Issues**
```bash
# Extension not loading
1. Check VS Code Developer Console (Help → Toggle Developer Tools)
2. Verify extension is enabled: Extensions → Search "Ninaivalaigal"
3. Check settings.json syntax

# Server connection failed
1. Verify server URL: http://localhost:8000
2. Test API manually: curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/contexts
3. Check JWT token is valid and not expired
```

### **JetBrains Plugin Issues**
```bash
# Plugin not working
1. Check IDE logs: Help → Show Log in Finder
2. Verify plugin installation: Settings → Plugins
3. Restart IDE after configuration changes

# Context not detected
1. Check tool window shows current context
2. Manually set context: Tools → Ninaivalaigal → Start Context
3. Verify project folder name detection
```

### **MCP Server Issues**
```bash
# MCP tools not available
1. Check server process: ps aux | grep mcp_server
2. Test server directly: python server/mcp_server.py
3. Verify config file JSON syntax

# Authentication errors
1. Check environment variables in MCP config
2. Verify database connection
3. Test with fresh JWT token
```

## ✅ **Success Criteria**

### **For Krishna to Verify:**
- [ ] VS Code extension installs and connects
- [ ] Chat commands work with JWT authentication
- [ ] Memory storage and recall functions
- [ ] Context switching works properly
- [ ] JetBrains plugin builds and installs
- [ ] Keyboard shortcuts function
- [ ] Tool window displays memories correctly

### **For Durai to Verify:**
- [ ] MCP server starts without errors
- [ ] IDE recognizes Ninaivalaigal MCP tools
- [ ] `enhance_ai_prompt_tool` returns enhanced prompts
- [ ] Memories are retrieved and ranked correctly synchronization
- [ ] Multi-user context isolation
- [ ] Performance is acceptable (< 200ms responses)

## 🎯 **Quick Test Commands**

```bash
# Get your token
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "krishna@example.com", "password": "test1234"}'

# Test API access
export TOKEN="your-jwt-token"
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/contexts

# Test memory operations
curl -X POST -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "test-context"}' \
  http://localhost:8000/contexts

curl -X POST -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/@e^M request_cross_team_access context_id=1 target_team_id=2 permission_level="read" justification="Need access for collaboration"
```

## 📞 **Getting Help**

If you encounter issues:
1. Check server logs: `tail -f /Users/asrajag/Workspace/mem0/logs/*.log`
2. Test API endpoints manually with curl
3. Verify JWT token hasn't expired (7-day default)
4. Check database connectivity: `psql -d mem0db -c "SELECT COUNT(*) FROM users;"`

The system is designed to work seamlessly across all IDEs with proper JWT authentication and context isolation.
