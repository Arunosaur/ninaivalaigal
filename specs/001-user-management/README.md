# SPEC-002: User Management & Authentication

**Note:** This was originally numbered 001 but is now SPEC-002. SPEC-001 is Core Memory System (platform foundation).

**Status:** 85% Implemented

## Authentication

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
