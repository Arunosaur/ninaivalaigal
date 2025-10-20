# Core API Reference

## Authentication

### POST /auth/signup

Create a new user account.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!",  // pragma: allowlist secret
  "name": "User Name"
}
```

**Response (201):**
```json
{
  "success": true,
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "name": "User Name"
  },
  "jwt_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "Bearer"
}
```

**Example curl:**
```bash
# Example password - not a real secret pragma: allowlist secret
curl -X POST http://localhost:8000/auth/signup \
-H "Content-Type: application/json" \
-d '{
  "email": "user@example.com",
  "password": "SecurePass123!",
  "name": "User Name"
}'
```

---

### POST /auth/login

Login with credentials.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!"  // pragma: allowlist secret
}
```

**Response (200):**
```json
{
  "success": true,
  "user": {
    "id": "uuid",
    "email": "user@example.com"
  },
  "jwt_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "Bearer"
}
```

**Example curl:**
```bash
# Example password - not a real secret pragma: allowlist secret
curl -X POST http://localhost:8000/auth/login \
-H "Content-Type: application/json" \
-d '{
  "email": "user@example.com",
  "password": "SecurePass123!"
}'
```
