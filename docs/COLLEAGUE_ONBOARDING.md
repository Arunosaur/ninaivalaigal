# 🎉 Welcome to Ninaivalaigal MCP Server!

**Quick Start Guide for Colleagues**
**Setup Time**: 2 minutes
**No Local Installation Required**

---

## 🚀 What You Get

Access to a centralized memory management system via Model Context Protocol (MCP):
- **Store memories** from your Copilot sessions
- **Recall context** automatically
- **Share knowledge** across your team
- **Zero local setup** - just configure and go!

---

## 📝 Quick Setup (2 Minutes)

### **Step 1: Get Your MCP Server URL**

Your admin will provide you with a URL like:
```
https://mac-studio-swami.ts.net:3000
```

### **Step 2: Test the Connection**

Open your browser or terminal and test:
```bash
curl https://mac-studio-swami.ts.net:3000/health
```

**Expected response**:
```json
{
  "status": "healthy",
  "api_connected": true,
  "redis_connected": true,
  "version": "1.0.0"
}
```

✅ If you see this, you're good to go!

### **Step 3: Configure Your Copilot**

Add this to your Copilot MCP configuration:

```json
{
  "mcp_servers": {
    "ninaivalaigal": {
      "url": "https://mac-studio-swami.ts.net:3000",
      "name": "Ninaivalaigal Memory Server",
      "description": "Team memory management",
      "endpoints": {
        "store": "/mcp/memory/store",
        "recall": "/mcp/memory/recall",
        "contexts": "/mcp/contexts",
        "tokenize": "/mcp/memory/tokenize"
      }
    }
  }
}
```

---

## 🎯 How to Use

### **Store a Memory**

When working with Copilot, memories are automatically stored. You can also manually store:

```bash
curl -X POST https://mac-studio-swami.ts.net:3000/mcp/memory/store \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Important project decision: Use React for frontend",
    "context": "project-alpha",
    "tags": ["decision", "frontend", "react"]
  }'
```

### **Recall Memories**

```bash
curl -X POST https://mac-studio-swami.ts.net:3000/mcp/memory/recall \
  -H "Content-Type: application/json" \
  -d '{
    "query": "frontend decisions",
    "context": "project-alpha",
    "limit": 10
  }'
```

### **List Available Contexts**

```bash
curl https://mac-studio-swami.ts.net:3000/mcp/contexts
```

---

## 📚 Available Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/health` | GET | Check server status |
| `/mcp/memory/store` | POST | Store a memory |
| `/mcp/memory/recall` | POST | Recall memories |
| `/mcp/contexts` | GET | List contexts |
| `/mcp/memory/tokenize` | POST | Tokenize text |

---

## 💡 Best Practices

### **1. Use Descriptive Contexts**
```json
{
  "context": "project-alpha-backend"  // Good
  "context": "stuff"                   // Bad
}
```

### **2. Add Relevant Tags**
```json
{
  "tags": ["bug-fix", "authentication", "urgent"]  // Good
  "tags": ["misc"]                                  // Bad
}
```

### **3. Include Metadata**
```json
{
  "metadata": {
    "author": "your-name",
    "date": "2025-09-30",
    "related_pr": "PR-123"
  }
}
```

---

## 🐛 Troubleshooting

### **Issue: Cannot Connect to MCP Server**

**Check 1**: Verify URL is correct
```bash
curl https://mac-studio-swami.ts.net:3000/health
```

**Check 2**: Contact your admin if health check fails

### **Issue: Copilot Not Using MCP**

**Check 1**: Verify MCP configuration in Copilot settings
**Check 2**: Restart Copilot after configuration change
**Check 3**: Check Copilot logs for MCP connection errors

### **Issue: Memories Not Storing**

**Check 1**: Verify you're using correct context name
```bash
curl https://mac-studio-swami.ts.net:3000/mcp/contexts
```

**Check 2**: Check request format matches examples above

---

## 📞 Getting Help

### **Quick Health Check**
```bash
# Save this as check-mcp.sh
#!/bin/bash
MCP_URL="https://mac-studio-swami.ts.net:3000"
echo "Checking MCP server..."
curl -s ${MCP_URL}/health | jq
```

### **Contact Your Admin**

If you encounter issues:
1. Run the health check above
2. Share the output with your admin
3. Include any error messages from Copilot

---

## 🎉 You're All Set!

Start using Ninaivalaigal MCP server with your Copilot:
1. ✅ MCP URL configured
2. ✅ Health check passing
3. ✅ Ready to store and recall memories

**Happy coding!** 🚀

---

## 📖 Additional Resources

- **Full Documentation**: [Link to your docs]
- **API Reference**: `https://mac-studio-swami.ts.net:3000/docs`
- **Team Wiki**: [Link to your wiki]
- **Support Channel**: [Your support channel]

---

*Last Updated: 2025-09-30*
*Questions? Contact your admin*
