# Developer B - Task Assignment

**Date:** October 12, 2025
**Focus:** Documentation & SPEC Updates
**Risk Level:** ✅ LOW (No code conflicts)

---

## 🎯 Your Mission

Update documentation to reflect recent authentication fixes and agentic testing setup.

**Working Directory:** `specs/` and `docs/`
**No Code Changes:** Documentation only
**Duration:** 2-3 hours

---

## ✅ Task 1: Update SPEC-001 (User Management)

**File:** `specs/001-user-management/README.md`

**What to Add:**

### **Section: JWT Token Flow**

Add new section after "Authentication" section:

```markdown
## JWT Token Generation

### Signup Flow
1. User submits signup form
2. Password hashed with bcrypt
3. User created in database via ORM
4. JWT token generated with claims:
   - user_id (string UUID)
   - email
   - account_type
   - role
   - exp (24 hours)
5. Token returned in response

### Login Flow
1. User submits credentials
2. Password verified against hash
3. Last login timestamp updated
4. User roles retrieved from RBAC
5. JWT token generated with:
   - All signup claims
   - RBAC roles
   - Team memberships
   - Organization ID
6. Token returned in response

### Token Usage
```bash
# API requests with token
curl -X GET http://localhost:13390/memory/list \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Token Expiration
- **Default:** 24 hours
- **Renewal:** Login again for new token
- **Refresh:** Not yet implemented (planned)
```

---

## ✅ Task 2: Update SPEC-084 (Agentic Testing)

**File:** `specs/084-agentic-ui-testing/README.md`

**What to Update:**

### **Section: Implementation Status**

Change status from:
```markdown
**Status:** ✅ IMPLEMENTED
```

To:
```markdown
**Status:** ✅ ENHANCED - Hybrid OpenAI/Ollama Strategy
**Updated:** October 12, 2025
```

### **Add New Section: Hybrid LLM Strategy**

Add after "Tech Stack" section:

```markdown
## Hybrid LLM Strategy

### Overview
Intelligent LLM provider selection for cost optimization:

| Environment | Provider | Cost | Use Case |
|-------------|----------|------|----------|
| Development | OpenAI API | ~$0.005/test | Fast feedback, reliable |
| CI Nightly | Ollama | FREE | Scheduled tests, no API cost |
| Fallback | Ollama | FREE | Budget exhausted |

### Infrastructure

**Shared Ollama Container:**
```bash
# Shared across all projects (not ninaivalaigal-specific)
container: ollama
port: 11434
model: llama3.2 (2GB)
```

**Benefits:**
- ✅ Cost-effective: Free for CI, cheap for dev
- ✅ Reusable: One Ollama serves all projects
- ✅ Flexible: Auto-detects or force specific LLM

### Test Files

**Hybrid Implementation:**
- `tests/agentic/test_signup_hybrid.py` - Auto-detects OpenAI vs Ollama
- `tests/agentic/test_signup_flow.py` - Original OpenAI-only version

**Usage:**
```bash
# Auto-detect (OpenAI if key set, else Ollama)
make test-agentic

# Force OpenAI
make test-agentic-openai

# Force Ollama (free)
make test-agentic-ollama
```

### Cost Analysis

**OpenAI (gpt-4o-mini):**
- Input: $0.15 per 1M tokens
- Output: $0.60 per 1M tokens
- Per test: ~$0.005
- Monthly (10 tests/day): ~$1.50

**Ollama:**
- All tests: FREE
- Initial download: 2GB (one-time)
- Uses local compute

### CI/CD Integration

**Nightly Tests:** Use Ollama (free)
**Pre-release:** Use OpenAI (reliable)
**On-demand:** Developer choice
```

---

## ✅ Task 3: Update SPEC Index

**File:** `specs/SPEC_INDEX.md`

**What to Update:**

Find SPEC-001 entry and update implementation percentage:
```markdown
**Before:**
- SPEC-001: User Management & Authentication - 85% implemented

**After:**
- SPEC-001: User Management & Authentication - 95% implemented
  - ✅ Signup working (ORM-based, proper RBAC)
  - ✅ Login working (UUID serialization fixed)
  - ✅ Logout endpoint added
  - ✅ JWT tokens generated
  - ⏳ Email verification (endpoint exists, needs testing)
  - ⏳ Password reset (planned)
```

Find SPEC-084 entry and update:
```markdown
**Before:**
- SPEC-084: Agentic UI Testing Framework - IMPLEMENTED

**After:**
- SPEC-084: Agentic UI Testing Framework - ENHANCED
  - ✅ Original OpenAI implementation
  - ✅ Hybrid OpenAI/Ollama framework
  - ✅ Shared Ollama container
  - ✅ Makefile targets added
  - ✅ Cost optimization strategy
  - ✅ CI/CD ready
```

---

## ✅ Task 4: Create Migration Guide

**File:** `docs/MIGRATION_JWT_AUTH.md`

**Create New File:**

```markdown
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
```

---

## ✅ Task 5: Update README (Quick Reference)

**File:** `README.md` (root)

**Find "Authentication" section and add:**

```markdown
## Quick Start: Authentication

### 1. Signup
```bash
curl -X POST http://localhost:13390/auth/signup/individual \
  -H "Content-Type: application/json" \
  -d '{"email":"you@example.com","password":"SecurePass123!","name":"Your Name"}'
```

### 2. Login
```bash
curl -X POST http://localhost:13390/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"you@example.com","password":"SecurePass123!"}'
```

### 3. Use JWT Token
```bash
export JWT_TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

curl -X GET http://localhost:13390/memory/list \
  -H "Authorization: Bearer $JWT_TOKEN"
```

**See:** `/docs/JWT_TOKEN_USAGE.md` for complete guide
```

---

## 📊 Deliverables Checklist

When done, report back with:

- [ ] Updated `specs/001-user-management/README.md`
- [ ] Updated `specs/084-agentic-ui-testing/README.md`
- [ ] Updated `specs/SPEC_INDEX.md`
- [ ] Created `docs/MIGRATION_JWT_AUTH.md`
- [ ] Updated `README.md` with quick start

---

## ⚠️ Important Guidelines

### **Do NOT Modify:**
- ❌ Any files in `server/` directory
- ❌ Any files in `tests/` directory
- ❌ Any files in `.github/` directory
- ❌ Any code files (`.py`, `.js`, `.ts`)

### **Only Modify:**
- ✅ Files in `specs/` directory
- ✅ Files in `docs/` directory
- ✅ `README.md` (root level only)

### **Collaboration Safety:**
- ✅ Your work is in different directories than others
- ✅ No code conflicts possible
- ✅ Can commit independently
- ✅ Changes can be reviewed separately

---

## 🚀 Getting Started

```bash
# 1. Pull latest changes
git pull

# 2. Create branch
git checkout -b docs/auth-spec-updates

# 3. Do your work (files listed above)

# 4. Review changes
git diff

# 5. Commit
git add specs/ docs/ README.md
git commit -m "docs: Update SPEC-001, SPEC-084 with JWT auth and hybrid testing"

# 6. Push
git push origin docs/auth-spec-updates
```

---

## ❓ Questions?

**If stuck:**
1. Check existing docs: `/docs/JWT_TOKEN_USAGE.md`
2. Check fix summary: `/docs/SIGNUP_FIX_COMPLETE.md`
3. Ask for clarification

**Estimated time:** 2-3 hours
**Difficulty:** Easy (documentation only)
**Risk:** Very low (no code changes)

---

Good luck! 🎉
