# JWT Token Access Guide for mem0 Users

## 🔑 How Users Get Their JWT Tokens

### Method 1: Automatic (Web UI) - **RECOMMENDED**
When users sign up or log in through the web interface, JWT tokens are automatically handled:

1. **Signup Process**:
   - Visit `http://localhost:8000/` 
   - Create account (Individual or Organization)
   - Token is automatically generated and stored in browser localStorage

2. **Login Process**:
   - Visit `http://localhost:8000/login`
   - Enter credentials
   - Token is automatically stored as `mem0_token` in localStorage
   - User is redirected to dashboard

3. **Token Storage**:
   ```javascript
   // Automatically stored in browser
   localStorage.setItem('mem0_token', result.user.jwt_token);
   localStorage.setItem('mem0_user', JSON.stringify(userInfo));
   ```

### Method 2: Manual API Call
For CLI/programmatic access, users can retrieve tokens via API:

```bash
# Login API call
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password123"}'

# Response includes JWT token
{
  "success": true,
  "message": "Login successful",
  "user": {
    "user_id": 7,
    "email": "user@example.com",
    "name": "User Name",
    "account_type": "individual",
    "role": "user",
    "jwt_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "email_verified": false
  }
}
```

### Method 3: Browser Developer Tools
Users can extract tokens from their browser:

1. Open browser Developer Tools (F12)
2. Go to Application/Storage tab
3. Find localStorage for your domain
4. Copy the `mem0_token` value

## 🛠️ Using JWT Tokens

### Web Dashboard
- **Automatic**: Tokens are used automatically for all dashboard operations
- **No manual action required**

### CLI Integration
```bash
# Set environment variable
export MEM0_USER_TOKEN="your-jwt-token-here"

# Use with CLI commands
./client/mem0 recall --context my-project
```

### API Calls
```bash
# Include in Authorization header
curl -H "Authorization: Bearer your-jwt-token-here" \
  http://localhost:8000/contexts
```

### MCP Server Integration
```json
{
  "mcp.servers": {
    "mem0": {
      "env": {
        "MEM0_JWT_TOKEN": "your-jwt-token-here"
      }
    }
  }
}
```

## ⏰ Token Expiration

- **Duration**: 24 hours from login
- **Auto-refresh**: Currently not implemented
- **Re-authentication**: Users must log in again after expiration

## 🔒 Security Best Practices

### For Users:
- Never share JWT tokens
- Log out when finished (clears tokens)
- Use secure connections (HTTPS in production)

### For Developers:
- Store tokens securely (localStorage for web, environment variables for CLI)
- Validate token expiration
- Use HTTPS in production

## 📋 Token Information

A typical JWT token contains:
```json
{
  "user_id": 7,
  "email": "user@example.com",
  "account_type": "individual",
  "role": "user",
  "exp": 1757876262  // Expiration timestamp
}
```

## 🚨 Troubleshooting

### Token Not Working?
1. Check expiration: Tokens expire after 24 hours
2. Verify format: Should start with `eyJ`
3. Re-login: Get a fresh token

### Can't Access Token?
1. **Web Users**: Check browser localStorage
2. **CLI Users**: Use login API call
3. **Lost Token**: Simply log in again

## 🎯 Quick Start Examples

### New User Onboarding:
```bash
# 1. Sign up via web UI
open http://localhost:8000/

# 2. Login and get token automatically
# Token is now in browser localStorage

# 3. For CLI access, extract token:
# Open DevTools → Application → localStorage → mem0_token
```

### Existing User:
```bash
# 1. Login via API
TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"password123"}' \
  | jq -r '.user.jwt_token')

# 2. Use token for API calls
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/contexts
```

This system ensures users can access their JWT tokens through multiple methods while maintaining security and usability.
