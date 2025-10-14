# Developer B - Option 3A: API Reference Documentation

**Task:** Create comprehensive API endpoint reference
**Difficulty:** Medium-High
**Time:** 4-6 hours
**File:** `docs/API_REFERENCE.md`

---

## 🎯 Objective

Create a complete API endpoint reference that external developers can use to integrate with ninaivalaigal. This completes the external developer documentation trilogy:

1. ✅ Integration Guide (done)
2. ✅ API Examples (done)
3. ⏳ API Reference (this task)

---

## 📚 What to Document

### **1. Authentication Endpoints**

Document all auth endpoints:
- `POST /auth/signup/individual`
- `POST /auth/signup/team`
- `POST /auth/login`
- `POST /auth/logout`
- `POST /auth/verify-email`
- `POST /auth/password-reset/request`
- `POST /auth/password-reset/verify`
- `POST /auth/password-reset/confirm`
- `POST /auth/token/refresh`
- `POST /auth/token/revoke`
- `POST /auth/token/revoke-all`

### **2. Memory Endpoints**

- `POST /memory/remember`
- `GET /memory/recall`
- `GET /memory/memories`
- `GET /memory/memories/{id}`
- `PUT /memory/memories/{id}`
- `DELETE /memory/memories/{id}`

### **3. Context Endpoints**

- `POST /contexts`
- `GET /contexts`
- `GET /contexts/{id}`
- `PUT /contexts/{id}`
- `DELETE /contexts/{id}`
- `POST /contexts/{id}/share`
- `GET /contexts/{id}/permissions`

### **4. RBAC Endpoints** (if applicable)

- User roles
- Permissions
- Teams
- Organizations

---

## ✅ Structure for Each Endpoint

For each endpoint, document:

```markdown
### POST /endpoint/path

**Description:** Brief description of what this endpoint does

**Authentication:** Required / Optional / None

**Rate Limit:** X requests/minute

**Request:**
```http
POST /endpoint/path HTTP/1.1
Host: localhost:13390
Authorization: Bearer YOUR_JWT_TOKEN
Content-Type: application/json

{
  "field1": "value1",
  "field2": "value2"
}
```

**Request Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| field1 | string | Yes | Description |
| field2 | integer | No | Description |

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "field": "value"
  }
}
```

**Error Responses:**

| Code | Description | Example |
|------|-------------|---------|
| 400 | Bad Request | Invalid input |
| 401 | Unauthorized | Missing/invalid token |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource doesn't exist |
| 429 | Rate Limited | Too many requests |
| 500 | Server Error | Internal error |

**Example:**
```bash
curl -X POST http://localhost:13390/endpoint/path \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"field1":"value1"}'
```
```

---

## 📁 Reference Materials

### **Review these files:**

**Authentication:**
- `server/signup_api.py` - All auth endpoints
- `server/auth.py` - Auth logic
- Your SPEC-045 update

**Memory:**
- `server/memory_api.py` - Memory endpoints
- `docs/API_EXAMPLES.md` - Examples you created

**Context:**
- `server/context_api.py` or similar
- SPEC-007 documentation

**OpenAPI/Swagger:**
- Visit `http://localhost:13390/docs` for auto-generated API docs
- Use this as reference for schemas

---

## ✅ Deliverable Structure

Create: `docs/API_REFERENCE.md`

```markdown
# ninaivalaigal API Reference

**Version:** 1.0
**Last Updated:** October 12, 2025
**Base URL:** `http://localhost:13390` (development)

---

## Table of Contents

1. [Authentication](#authentication)
2. [Rate Limits](#rate-limits)
3. [Error Handling](#error-handling)
4. [Authentication Endpoints](#authentication-endpoints)
5. [Memory Endpoints](#memory-endpoints)
6. [Context Endpoints](#context-endpoints)
7. [RBAC Endpoints](#rbac-endpoints)
8. [Webhooks](#webhooks)

---

## Authentication

All endpoints except signup and login require JWT authentication.

**Include in headers:**
```http
Authorization: Bearer YOUR_JWT_TOKEN
```

**Token expires:** 24 hours
**Refresh token expires:** 30 days
**See:** [Authentication Endpoints](#authentication-endpoints)

---

## Rate Limits

| Tier | Requests/Minute | Burst |
|------|-----------------|-------|
| Free | 60 | 100 |
| Team | 600 | 1000 |
| Enterprise | 6000 | 10000 |

**Rate limit headers:**
```http
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1697123456
```

---

## Error Handling

All errors follow this format:

```json
{
  "success": false,
  "detail": "Error message",
  "error_code": "ERROR_TYPE"
}
```

**Common error codes:**
- `VALIDATION_ERROR` - Invalid input
- `AUTH_ERROR` - Authentication failed
- `PERMISSION_ERROR` - Insufficient permissions
- `NOT_FOUND` - Resource not found
- `RATE_LIMIT_ERROR` - Too many requests

---

## Authentication Endpoints

[Document all auth endpoints here with the structure above]

### POST /auth/signup/individual

[Full documentation]

### POST /auth/login

[Full documentation]

### POST /auth/token/refresh

[Full documentation]

[Continue for all auth endpoints...]

---

## Memory Endpoints

[Document all memory endpoints]

### POST /memory/remember

[Full documentation]

### GET /memory/recall

[Full documentation]

[Continue for all memory endpoints...]

---

## Context Endpoints

[Document all context endpoints]

### POST /contexts

[Full documentation]

[Continue for all context endpoints...]

---

## RBAC Endpoints

[Document RBAC endpoints if applicable]

---

## Webhooks

See [WEBHOOK_GUIDE.md](WEBHOOK_GUIDE.md) for webhook documentation (coming soon).

---

## Additional Resources

- **Integration Guide:** [INTEGRATION_GUIDE.md](INTEGRATION_GUIDE.md)
- **Code Examples:** [API_EXAMPLES.md](API_EXAMPLES.md)
- **Testing Guide:** [TESTING_AUTH.md](TESTING_AUTH.md)
- **OpenAPI/Swagger:** `http://localhost:13390/docs`

---

**For support:** support@ninaivalaigal.com
```

---

## 📊 Coverage Checklist

### **Authentication (11 endpoints)**
- [ ] Signup (individual)
- [ ] Signup (team)
- [ ] Login
- [ ] Logout
- [ ] Verify email
- [ ] Password reset (request)
- [ ] Password reset (verify)
- [ ] Password reset (confirm)
- [ ] Token refresh
- [ ] Token revoke
- [ ] Token revoke-all

### **Memory (6 endpoints)**
- [ ] Remember (store)
- [ ] Recall (search)
- [ ] List memories
- [ ] Get memory
- [ ] Update memory
- [ ] Delete memory

### **Context (6 endpoints)**
- [ ] Create context
- [ ] List contexts
- [ ] Get context
- [ ] Update context
- [ ] Delete context
- [ ] Share context

### **RBAC (if applicable)**
- [ ] Document role endpoints
- [ ] Document permission endpoints

---

## 💡 Tips

1. **Use OpenAPI docs** - Visit `/docs` endpoint for schemas
2. **Test everything** - Run curl commands to verify
3. **Be complete** - Every field, every parameter, every error
4. **Cross-reference** - Link to Integration Guide and Examples
5. **Think developer** - What would YOU want to know?

---

## 🎯 Success Criteria

- [ ] All endpoints documented
- [ ] Request/response schemas complete
- [ ] Error responses documented
- [ ] Working curl examples for each
- [ ] Rate limits specified
- [ ] Authentication requirements clear
- [ ] Cross-references to other docs
- [ ] Professional, copy-paste ready

---

## 📈 Value

**This document will:**
- ✅ Complete external developer documentation
- ✅ Serve as single source of truth for API
- ✅ Enable rapid integration (< 30 minutes)
- ✅ Reduce support questions
- ✅ Establish professional standard

**This is the final piece of world-class external developer docs!**

---

**Estimated time:** 4-6 hours
**Difficulty:** Medium-High
**Value:** Exceptional

**Ready to create the definitive API reference? 🚀**
