# Migration Guide: JWT Authentication

**For:** Developers integrating with ninaivalaigal API
**Date:** October 12, 2025
**Status:** Active

---

## What Changed

### Before (Old)
- Basic authentication only
- Session-based tokens
- No MCP server support

### After (New)
- JWT tokens for all authentication
- 24-hour token expiration
- MCP server ready
- RBAC claims in token

---

## How to Migrate

### Step 1: Get JWT Token

**Signup (New Users):**
```bash
curl -X POST http://localhost:13390/auth/signup/individual \
  -H "Content-Type: application/json" \
  -d '{
    "email": "your@email.com",
    "password": "SecurePassword123!",
    "name": "Your Name"
  }'
```

**Login (Existing Users):**
```bash
curl -X POST http://localhost:13390/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "your@email.com",
    "password": "YourPassword"
  }'
```

**Response:**
```json
{
  "success": true,
  "user": {
    "jwt_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "user_id": "uuid-here",
    "email": "your@email.com"
  }
}
```

### Step 2: Use Token in Requests

**Old Way (Don't use):**
```bash
# Session-based (deprecated)
curl -X GET http://localhost:13390/memory/list \
  -H "Cookie: session=..."
```

**New Way (Use this):**
```bash
# JWT token in Authorization header
curl -X GET http://localhost:13390/memory/list \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Step 3: Handle Token Expiration

**Tokens expire after 24 hours.**

**Check expiration:**
```python
import jwt
decoded = jwt.decode(token, options={"verify_signature": False})
print(decoded["exp"])  # Unix timestamp
```

**Renew token:**
```bash
# Login again to get new token
curl -X POST http://localhost:13390/auth/login ...
```

---

## MCP Server Integration

**Configuration:**
```bash
# Environment variable
export NINAIVALAIGAL_JWT_TOKEN="your_jwt_token_here"

# Or in config file
{
  "server": {
    "url": "http://localhost:13390",
    "auth": {
      "type": "jwt",
      "token": "your_jwt_token_here"
    }
  }
}
```

---

## Troubleshooting

### Token Invalid
**Error:** `401 Unauthorized`
**Solution:** Token expired or invalid, login again

### UUID Serialization Error
**Error:** `Object of type UUID is not JSON serializable`
**Solution:** Fixed in latest version, update your code

### Missing Authorization Header
**Error:** `403 Forbidden`
**Solution:** Add `Authorization: Bearer TOKEN` header

---

## Breaking Changes

**None!** Old session-based auth still works (deprecated).

**Recommendation:** Migrate to JWT tokens for:
- ✅ Better security
- ✅ MCP server support
- ✅ Stateless authentication
- ✅ RBAC claims included

---

## Support

**Documentation:**
- `/docs/JWT_TOKEN_USAGE.md` - Complete guide
- `/docs/SIGNUP_FIX_COMPLETE.md` - Implementation details

**Questions:** Create issue in GitHub
