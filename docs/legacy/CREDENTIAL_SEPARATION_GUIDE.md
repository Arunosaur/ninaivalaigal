# Credential Separation Guide - Who Gets What

## The Problem: Why Three Different Credentials?

You're seeing three credentials and wondering why you need all of them:

```json
{
  "NINAIVALAIGAL_DATABASE_URL": "postgresql://ninaivalaigal_app:app_secret@localhost:5432/ninaivalaigal_db",
  "NINAIVALAIGAL_JWT_SECRET": "ninaivalaigal-super-secret-jwt-signing-key-min-32-chars-2024",
  "NINAIVALAIGAL_USER_TOKEN": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

## The Answer: Different People Get Different Credentials

### **Server Administrator** (You, setting up the system)
Gets these **server-side environment variables**:
```bash
# Server environment (.env file or system environment)
NINAIVALAIGAL_DATABASE_URL=postgresql://ninaivalaigal_app:strong_password@localhost:5432/ninaivalaigal_db
NINAIVALAIGAL_JWT_SECRET=your-super-secret-jwt-signing-key-min-32-chars
```

### **End Users** (People using the system)
Get **only their personal JWT token**:
```json
{
  "mcpServers": {
    "e^m": {
      "command": "/opt/homebrew/anaconda3/bin/python",
      "args": ["/path/to/server/mcp_server.py"],
      "env": {
        "NINAIVALAIGAL_USER_TOKEN": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
      }
    }
  }
}
```

## Proper Deployment Architecture

### **Production Server Setup**
```bash
# /etc/environment or docker-compose.yml
NINAIVALAIGAL_DATABASE_URL=postgresql://ninaivalaigal_app:prod_password@db:5432/ninaivalaigal_db
NINAIVALAIGAL_JWT_SECRET=production-jwt-secret-key-very-long-and-secure
```

### **User 1 (Alice) - VS Code Config**
```json
{
  "mcpServers": {
    "e^m": {
      "command": "python",
      "args": ["https://your-server.com/mcp_server.py"],
      "env": {
        "NINAIVALAIGAL_USER_TOKEN": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.alice_token"
      }
    }
  }
}
```

### **User 2 (Bob) - VS Code Config**
```json
{
  "mcpServers": {
    "e^m": {
      "command": "python",
      "args": ["https://your-server.com/mcp_server.py"],
      "env": {
        "NINAIVALAIGAL_USER_TOKEN": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.bob_token"
      }
    }
  }
}
```

## Why Each Credential Exists

### **1. Database URL** - Server Infrastructure
- **Purpose**: Application connects to PostgreSQL
- **Who needs it**: Only the server/application
- **Security**: Hidden from users, stored in server environment
- **Analogy**: Like the key to the bank vault (only bank employees have it)

### **2. JWT Secret** - Token Factory
- **Purpose**: Creates and validates user tokens
- **Who needs it**: Only the server/application
- **Security**: Never shared with users
- **Analogy**: Like the machine that makes credit cards (only the bank has it)

### **3. User Token** - Individual Identity
- **Purpose**: Proves who you are to the system
- **Who needs it**: Each user gets their own unique token
- **Security**: Each user only gets their own token
- **Analogy**: Like your credit card (made by the bank's machine, but only you have yours)

## Development vs Production

### **Development (What you're doing now)**
For testing, you put all three in your local config because you're playing all roles:
- You're the server administrator
- You're the user
- You're testing the system

### **Production (Real deployment)**
```
Server Environment:
├── NINAIVALAIGAL_DATABASE_URL (admin only)
├── NINAIVALAIGAL_JWT_SECRET (admin only)
└── MCP Server running

User Environments:
├── Alice: NINAIVALAIGAL_USER_TOKEN=alice_token
├── Bob: NINAIVALAIGAL_USER_TOKEN=bob_token
└── Charlie: NINAIVALAIGAL_USER_TOKEN=charlie_token
```

## Updated VS Code Config (Users Only Need This)

For end users, they only need their token:

```json
{
  "mcpServers": {
    "e^m": {
      "command": "/opt/homebrew/anaconda3/bin/python",
      "args": ["/Users/asrajag/Workspace/mem0/server/mcp_server.py"],
      "env": {
        "NINAIVALAIGAL_USER_TOKEN": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
      }
    }
  }
}
```

The server gets the database URL and JWT secret from its environment, not from the user's MCP config.

## Summary

- **Database URL + JWT Secret** = Server administrator credentials (you)
- **User Token** = Individual user credentials (each person gets their own)
- **In development**: You need all three because you're testing everything
- **In production**: Users only get their token, server keeps the other two secret
