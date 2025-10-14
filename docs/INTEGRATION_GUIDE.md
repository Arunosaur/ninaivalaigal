# Integration Guide: ninaivalaigal API

**For:** External developers building applications with ninaivalaigal
**Last Updated:** October 12, 2025

---

## 📚 Table of Contents

1. [Overview](#overview)
2. [Getting Started](#getting-started)
3. [Authentication](#authentication)
4. [Core Concepts](#core-concepts)
5. [Common Use Cases](#common-use-cases)
6. [Rate Limits](#rate-limits)
7. [Error Handling](#error-handling)
8. [Best Practices](#best-practices)
9. [Webhook Integration](#webhook-integration)
10. [SDKs and Client Libraries](#sdks-and-client-libraries)
11. [Support](#support)

---

## 1. Overview

### What is ninaivalaigal?

ninaivalaigal is an AI memory management platform that provides:
- **Context-aware memory storage** - Store and retrieve memories with context
- **Multi-user collaboration** - Team and organization support
- **Intelligent search** - Similarity-based memory retrieval
- **Secure authentication** - JWT + refresh tokens

### Use Cases

- **AI Agent Memory** - Give your AI agents persistent memory
- **Context Management** - Organize information by projects/contexts
- **Team Collaboration** - Share memories across teams
- **Knowledge Base** - Build searchable knowledge repositories

---

## 2. Getting Started

### Prerequisites

- API endpoint: `http://localhost:13390` (development) or your deployed URL
- Programming language: Python, JavaScript, or any HTTP client
- Understanding of REST APIs and JWT authentication

### Quick Start (5 minutes)

1. **Create an account**
2. **Get your JWT token**
3. **Store your first memory**
4. **Retrieve memories**

[Detailed steps below]

---

## 3. Authentication

ninaivalaigal uses **JWT (JSON Web Tokens)** for authentication.

### Step 1: Sign Up

```bash
POST /auth/signup/individual

Body:
{
  "email": "you@example.com",
  "password": "SecurePass123!",
  "name": "Your Name"
}

Response:
{
  "success": true,
  "user": {
    "jwt_token": "eyJhbGci...",
    "refresh_token": "abc123...",
    "user_id": "uuid-here"
  }
}
```

### Step 2: Store Your Tokens

**Save both tokens:**
- **Access Token** (jwt_token): Use for API requests, expires in 24 hours
- **Refresh Token**: Use to get new access tokens, expires in 30 days

### Step 3: Make Authenticated Requests

Include access token in `Authorization` header:

```bash
GET /memory/list
Authorization: Bearer YOUR_JWT_TOKEN
```

### Step 4: Refresh Your Token

When access token expires:

```bash
POST /auth/token/refresh

Body:
{
  "refresh_token": "YOUR_REFRESH_TOKEN"
}

Response:
{
  "access_token": "new_token_here"
}
```

---

## 4. Core Concepts

### Contexts

Contexts are named groupings for memories:
- **Personal**: Only you can access
- **Team**: Shared with team members
- **Organization**: Visible to org users

**Example:** `project-alpha`, `customer-support`, `research-2025`

### Memories

Individual pieces of information stored with metadata:
- Text content
- Metadata (JSON)
- Timestamps
- Context association

### Scopes

Determines memory visibility:
- **Personal**: Private to you
- **Team**: Shared with specific team
- **Organization**: Shared with organization

---

## 5. Common Use Cases

### Use Case 1: AI Agent Memory

**Scenario:** Store conversation history for AI agent

```python
# Store memory
POST /memory/remember
{
  "text": "User prefers dark mode",
  "context_id": "user-preferences",
  "meta": {
    "user_id": "123",
    "timestamp": "2025-10-12",
    "confidence": 0.95
  }
}

# Recall relevant memories
GET /memory/recall?query=user preferences&k=5
```

### Use Case 2: Team Knowledge Base

**Scenario:** Build searchable team wiki

```python
# Store team knowledge
POST /contexts
{
  "name": "engineering-wiki",
  "scope": "team",
  "team_id": 456
}

POST /memory/remember
{
  "text": "How to deploy to production: run make deploy-prod",
  "context_id": "engineering-wiki",
  "meta": {
    "category": "deployment",
    "tags": ["production", "deployment"]
  }
}
```

### Use Case 3: Context-Aware Search

**Scenario:** Find relevant information based on current context

```python
# Search within specific context
GET /memory/recall?query=deployment steps&context_id=engineering-wiki&k=10
```

---

## 6. Rate Limits

| Tier | Requests/Minute | Burst |
|------|-----------------|-------|
| Free | 60 | 100 |
| Team | 600 | 1000 |
| Enterprise | 6000 | 10000 |

**Rate Limit Headers:**
```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1697123456
```

**Handling Rate Limits:**
- Implement exponential backoff
- Cache responses when possible
- Use refresh tokens efficiently

---

## 7. Error Handling

### HTTP Status Codes

| Code | Meaning | Action |
|------|---------|--------|
| 200 | Success | Continue |
| 400 | Bad Request | Check request format |
| 401 | Unauthorized | Refresh token or re-login |
| 403 | Forbidden | Check permissions |
| 429 | Rate Limited | Wait and retry |
| 500 | Server Error | Report to support |

### Error Response Format

```json
{
  "success": false,
  "detail": "Invalid email format",
  "error_code": "VALIDATION_ERROR"
}
```

### Common Errors

**401 Unauthorized:**
```bash
# Solution: Refresh your token
POST /auth/token/refresh
{
  "refresh_token": "YOUR_REFRESH_TOKEN"
}
```

**403 Forbidden:**
```bash
# Solution: Check context permissions
GET /contexts/{id}
# Verify you have access
```

---

## 8. Best Practices

### Security

✅ **DO:**
- Store tokens securely (environment variables, secure storage)
- Use HTTPS in production
- Rotate refresh tokens regularly
- Implement token refresh before expiry

❌ **DON'T:**
- Hardcode tokens in source code
- Commit tokens to version control
- Share tokens between users
- Use expired tokens

### Performance

✅ **DO:**
- Cache frequently accessed memories
- Batch requests when possible
- Use appropriate `k` values for recall
- Implement pagination for large results

❌ **DON'T:**
- Make redundant API calls
- Request all memories at once
- Ignore rate limits
- Skip error handling

### Data Management

✅ **DO:**
- Use meaningful context names
- Add metadata to memories
- Clean up old contexts
- Organize by scope

❌ **DON'T:**
- Create duplicate contexts
- Store sensitive data in metadata
- Mix unrelated memories in same context

---

## 9. Webhook Integration

*Not yet available.* Stay tuned for updates on webhook support for real-time event notifications.

---

## 10. SDKs and Client Libraries

*Coming soon.* We are developing official Python and JavaScript/TypeScript SDKs to simplify integration.

---

## 11. Support

### Documentation

- **API Reference:** `/docs` (OpenAPI/Swagger)
- **Code Examples:** `docs/API_EXAMPLES.md`
- **SPECs:** `specs/` directory
- **Migration Guides:** `docs/MIGRATION_*.md`

### Help & Support

- **GitHub Issues:** Report bugs and feature requests
- **Email:** support@ninaivalaigal.com
- **Documentation:** https://docs.ninaivalaigal.com

### Community

- **Discord:** Join our developer community
- **Forum:** Share integration stories
- **Blog:** Latest updates and tutorials

---

## Next Steps

1. **Read API Examples:** `docs/API_EXAMPLES.md`
2. **Explore OpenAPI Docs:** `http://localhost:13390/docs`
3. **Try the Quickstart:** Build your first integration
4. **Join Community:** Connect with other developers

---

**Happy Building! 🚀**
