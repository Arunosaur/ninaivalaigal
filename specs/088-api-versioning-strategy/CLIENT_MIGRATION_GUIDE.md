# Client Migration Guide: Unversioned → V1

**Date**: November 2, 2025
**Timeline**: 90-day migration period
**Sunset Date**: February 1, 2026
**Related**: SPEC-088 API Versioning Strategy

---

## Overview

This guide helps you migrate from unversioned API endpoints to the new V1 versioned API.

**Why Migrate?**
- ✅ Stable, versioned API with guaranteed backward compatibility
- ✅ Clear deprecation timelines
- ✅ Better error handling and documentation
- ✅ Future-proof your integration

**Timeline**:
- **Now - January 31, 2026**: Both unversioned and V1 endpoints work
- **February 1, 2026**: Unversioned endpoints will be removed

---

## Quick Start

### Before (Unversioned)
```bash
curl https://api.ninaivalaigal.com/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"secret"}'  # pragma: allowlist secret
```

### After (V1)
```bash
curl https://api.ninaivalaigal.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"secret"}'  # pragma: allowlist secret
```

**Key Change**: Add `/api/v1` prefix to all endpoints

---

## Endpoint Mapping

### Authentication

| Unversioned | V1 | Notes |
|-------------|-----|-------|
| `POST /auth/signup` | `POST /api/v1/auth/signup/individual` | Split into individual/organization |
| `POST /auth/login` | `POST /api/v1/auth/login` | Same |
| `GET /auth/me` | `GET /api/v1/auth/me` | Same |
| `POST /auth/refresh` | `POST /api/v1/auth/refresh` | New endpoint |

### Users

| Unversioned | V1 | Notes |
|-------------|-----|-------|
| `GET /users/me` | `GET /api/v1/users/me` | Same |
| `PUT /users/me` | `PUT /api/v1/users/me` | Same |
| `GET /users/{id}` | `GET /api/v1/users/{id}` | Same |

### Memory

| Unversioned | V1 | Notes |
|-------------|-----|-------|
| `POST /memory` | `POST /api/v1/memory` | Same |
| `GET /memory` | `GET /api/v1/memory` | Same |
| `GET /memory/{id}` | `GET /api/v1/memory/{id}` | Same |
| `DELETE /memory/{id}` | `DELETE /api/v1/memory/{id}` | Same |
| `POST /memory/search` | `POST /api/v1/memory/search` | Same |

### Teams

| Unversioned | V1 | Notes |
|-------------|-----|-------|
| `POST /teams` | `POST /api/v1/teams` | Same |
| `GET /teams` | `GET /api/v1/teams` | Same |
| `GET /teams/{id}` | `GET /api/v1/teams/{id}` | Same |

### Organizations

| Unversioned | V1 | Notes |
|-------------|-----|-------|
| `POST /organizations` | `POST /api/v1/organizations` | Same |
| `GET /organizations` | `GET /api/v1/organizations` | Same |
| `GET /organizations/{id}` | `GET /api/v1/organizations/{id}` | Same |

---

## Code Examples

### JavaScript/TypeScript

**Before**:
```typescript
const response = await fetch('https://api.ninaivalaigal.com/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ email, password })
});
```

**After**:
```typescript
const response = await fetch('https://api.ninaivalaigal.com/api/v1/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ email, password })
});
```

**Helper Function**:
```typescript
const API_VERSION = 'v1';
const BASE_URL = `https://api.ninaivalaigal.com/api/${API_VERSION}`;

async function apiRequest(endpoint: string, options: RequestInit = {}) {
  const url = `${BASE_URL}${endpoint}`;
  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers
    }
  });
  return response.json();
}

// Usage
const result = await apiRequest('/auth/login', {
  method: 'POST',
  body: JSON.stringify({ email, password })
});
```

---

### Python

**Before**:
```python
import requests

response = requests.post(
    'https://api.ninaivalaigal.com/auth/login',
    json={'email': email, 'password': password}
)
```

**After**:
```python
import requests

response = requests.post(
    'https://api.ninaivalaigal.com/api/v1/auth/login',
    json={'email': email, 'password': password}
)
```

**Helper Class**:
```python
class NinaivalaigalClient:
    def __init__(self, api_version='v1'):
        self.base_url = f'https://api.ninaivalaigal.com/api/{api_version}'
        self.token = None

    def request(self, method, endpoint, **kwargs):
        url = f'{self.base_url}{endpoint}'
        headers = kwargs.pop('headers', {})

        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'

        response = requests.request(method, url, headers=headers, **kwargs)
        return response.json()

    def login(self, email, password):
        result = self.request('POST', '/auth/login',
                            json={'email': email, 'password': password})
        self.token = result['jwt_token']
        return result

# Usage
client = NinaivalaigalClient()
client.login('user@example.com', 'password')
memories = client.request('GET', '/memory')
```

---

### cURL

**Before**:
```bash
curl -X POST https://api.ninaivalaigal.com/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"secret"}'  # pragma: allowlist secret
```

**After**:
```bash
curl -X POST https://api.ninaivalaigal.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"secret"}'  # pragma: allowlist secret
```

**With Environment Variable**:
```bash
export API_BASE="https://api.ninaivalaigal.com/api/v1"

curl -X POST $API_BASE/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"secret"}'  # pragma: allowlist secret
```

---

## Migration Checklist

### Phase 1: Preparation (Week 1)
- [ ] Review this migration guide
- [ ] Identify all API calls in your codebase
- [ ] Create a list of endpoints you use
- [ ] Set up a test environment

### Phase 2: Update Code (Week 2-3)
- [ ] Update base URL to include `/api/v1`
- [ ] Update authentication endpoints
- [ ] Update user management endpoints
- [ ] Update memory endpoints
- [ ] Update team endpoints
- [ ] Update organization endpoints

### Phase 3: Testing (Week 4)
- [ ] Test all updated endpoints
- [ ] Verify authentication flow
- [ ] Test error handling
- [ ] Check response format compatibility
- [ ] Load testing (if applicable)

### Phase 4: Deployment (Week 5-6)
- [ ] Deploy to staging
- [ ] Monitor for errors
- [ ] Deploy to production
- [ ] Monitor production traffic
- [ ] Remove old unversioned calls

---

## Response Format Changes

### V1 Response Format

All V1 responses follow this format:

**Success**:
```json
{
  "success": true,
  "message": "Operation successful",
  "data": {...}
}
```

**Error**:
```json
{
  "success": false,
  "error": "Error message",
  "details": {...}
}
```

### Headers

V1 responses include version headers:
```http
X-API-Version: v1
```

If deprecated:
```http
X-API-Deprecated: true
X-API-Sunset-Date: 2026-01-30T00:00:00Z
X-API-Replacement: v2
```

---

## Common Issues

### Issue 1: 404 Not Found

**Problem**: Getting 404 errors after migration

**Solution**: Ensure you're using the correct V1 prefix:
```
❌ /auth/login
✅ /api/v1/auth/login
```

---

### Issue 2: Authentication Fails

**Problem**: JWT token not working

**Solution**: Check that you're including the Authorization header:
```http
Authorization: Bearer YOUR_JWT_TOKEN
```

---

### Issue 3: Response Format Different

**Problem**: Response structure changed

**Solution**: V1 uses consistent format. Update your parsing:
```javascript
// Before
const data = response.data;

// After
const data = response.data; // Same, but check for 'success' field
if (data.success) {
  // Handle success
}
```

---

## Testing Your Migration

### 1. Test Authentication
```bash
# Login
curl -X POST https://api.ninaivalaigal.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"your@email.com","password":"yourpassword"}'  # pragma: allowlist secret

# Should return JWT token
```

### 2. Test Authenticated Endpoint
```bash
# Get profile
curl https://api.ninaivalaigal.com/api/v1/users/me \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# Should return user profile
```

### 3. Check Version Header
```bash
curl -I https://api.ninaivalaigal.com/api/v1/users/me \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# Should include: X-API-Version: v1
```

---

## Support

### Documentation
- **V1 API Reference**: [V1_API_REFERENCE.md](./V1_API_REFERENCE.md)
- **SPEC-088**: [README.md](./README.md)

### Contact
- **Email**: api-support@ninaivalaigal.com
- **Emergency**: api-emergency@ninaivalaigal.com
- **Slack**: #api-support

### Office Hours
- **Weekly**: Tuesdays 2-4 PM PST
- **Zoom**: https://zoom.us/j/api-support

---

## FAQ

**Q: Do I need to migrate immediately?**
A: No, you have until February 1, 2026. However, we recommend migrating soon to ensure a smooth transition.

**Q: Will my existing code break?**
A: No, unversioned endpoints will continue to work until February 1, 2026.

**Q: What if I can't migrate by the deadline?**
A: Contact api-support@ninaivalaigal.com for assistance. We can provide extended support in special cases.

**Q: Are there any breaking changes in V1?**
A: No, V1 maintains compatibility with unversioned endpoints. The main change is the URL prefix.

**Q: Will there be a V2?**
A: Yes, V2 is planned for Q2 2026. It will include breaking changes (camelCase, cursor pagination, etc.).

**Q: How do I know if I'm using deprecated endpoints?**
A: Check response headers for `X-API-Deprecated: true`.

---

**Last Updated**: November 2, 2025
**Status**: Active
**Deadline**: February 1, 2026
