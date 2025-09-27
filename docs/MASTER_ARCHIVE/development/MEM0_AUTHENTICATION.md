# mem0 Sidecar Authentication

This document describes the authentication system for the mem0 sidecar service, which provides secure access control for memory operations.

## Overview

The mem0 sidecar implements a shared secret authentication system to secure memory operations between the main API and the mem0 service. This prevents unauthorized access to user memories and ensures proper isolation between users, teams, and organizations.

## Authentication Methods

### 1. Shared Secret Authentication

The simplest authentication method uses a shared secret token:

```bash
# Set the shared secret
export MEMORY_SHARED_SECRET="your-secure-secret-here"

# Make authenticated request
curl -H "Authorization: Bearer your-secure-secret-here" \
     http://localhost:7070/auth/test
```

### 2. HMAC-Based Authentication (Recommended)

For enhanced security, the sidecar supports HMAC-SHA256 authentication with timestamp validation:

```bash
# Generate HMAC token (format: timestamp:signature)
timestamp=$(date +%s)
signature=$(echo -n "$timestamp" | openssl dgst -sha256 -hmac "$MEMORY_SHARED_SECRET" -hex | cut -d' ' -f2)
token="${timestamp}:${signature}"  # pragma: allowlist secret

# Make authenticated request
curl -H "Authorization: Bearer $token" \
     http://localhost:7070/auth/test
```

**HMAC Benefits:**
- **Replay Protection**: 5-minute timestamp window prevents token reuse
- **Tamper Resistance**: HMAC signature prevents token modification
- **Forward Security**: Each request uses a unique token

## User Context Headers

The sidecar extracts user context from HTTP headers for proper isolation:

```bash
curl -H "Authorization: Bearer $MEMORY_SHARED_SECRET" \
     -H "X-User-Id: user123" \
     -H "X-Team-Id: team456" \
     -H "X-Org-Id: org789" \
     http://localhost:7070/remember \
     -d '{"text": "Remember this for the user"}'
```

**Context Headers:**
- `X-User-Id`: Individual user identifier
- `X-Team-Id`: Team identifier for team-scoped memories
- `X-Org-Id`: Organization identifier for org-scoped memories

## Configuration

### Environment Variables

```bash
# Required: Shared secret for authentication
MEMORY_SHARED_SECRET=your-secure-secret-here

# Optional: Memory provider configuration
MEMORY_PROVIDER=http
MEMORY_HTTP_BASE=http://localhost:7070
```

### Container Deployment

The mem0 container automatically receives the shared secret:

```bash
# Start with authentication enabled
MEMORY_SHARED_SECRET=your-secret make stack-up

# Check authentication status
curl http://localhost:7070/health
```

### Development vs Production

**Development (.env.example):**
```bash
MEMORY_SHARED_SECRET=dev-memory-secret-change-in-production
```

**Production:**
```bash
# Use a cryptographically secure secret
MEMORY_SHARED_SECRET=$(openssl rand -hex 32)
```

## API Endpoints

### Health Check (No Auth Required)

```bash
GET /health
```

Response:
```json
{
  "status": "ok",
  "authentication": "enabled",
  "version": "1.0.0"
}
```

### Authentication Test

```bash
GET /auth/test
Authorization: Bearer <token>
```

Response:
```json
{
  "authenticated": true,
  "context": {
    "user_id": "user123",
    "team_id": "team456",
    "org_id": "org789"
  },
  "message": "Authentication successful"
}
```

### Memory Operations

All memory operations require authentication:

#### Store Memory
```bash
POST /remember
Authorization: Bearer <token>
X-User-Id: <user_id>
Content-Type: application/json

{
  "text": "Memory content to store"
}
```

#### Recall Memories
```bash
GET /recall?q=search_query&k=5
Authorization: Bearer <token>
X-User-Id: <user_id>
```

#### List Memories
```bash
GET /memories?limit=10&offset=0
Authorization: Bearer <token>
X-User-Id: <user_id>
```

#### Delete Memory
```bash
DELETE /memories/{memory_id}
Authorization: Bearer <token>
X-User-Id: <user_id>
```

## Security Features

### Authentication Enforcement

- **Required Headers**: All protected endpoints require valid authentication
- **Context Validation**: User context headers are validated and logged
- **Error Handling**: Proper HTTP status codes (401, 403) for auth failures

### Request Logging

All authenticated requests are logged with context:

```
INFO: Remember request from user_id=user123
INFO: Recall request from user_id=user123, query='search term'
INFO: Delete request from user_id=user123, memory_id=mem_456
```

### Token Validation

- **Simple Secret**: Direct comparison with configured secret
- **HMAC Token**: Timestamp validation (5-minute window) + signature verification
- **Constant-Time Comparison**: Prevents timing attacks

## Testing

### Automated Testing

```bash
# Run authentication test suite
make test-mem0-auth

# Test specific authentication method
MEMORY_SHARED_SECRET=test-secret ./scripts/test-mem0-auth.sh
```

### Manual Testing

```bash
# Test health endpoint
curl http://localhost:7070/health

# Test authentication
curl -H "Authorization: Bearer $MEMORY_SHARED_SECRET" \
     http://localhost:7070/auth/test

# Test with user context
curl -H "Authorization: Bearer $MEMORY_SHARED_SECRET" \
     -H "X-User-Id: test-user" \
     -H "X-Team-Id: test-team" \
     http://localhost:7070/auth/test
```

## Troubleshooting

### Authentication Disabled

If `MEMORY_SHARED_SECRET` is not set:
- All endpoints allow unauthenticated access
- Warning logged: "MEMORY_SHARED_SECRET not set - authentication disabled"
- Health endpoint shows: `"authentication": "disabled"`

### Common Issues

**401 Unauthorized:**
- Missing `Authorization` header
- Invalid or expired token
- Incorrect shared secret

**Token Expired (HMAC):**
- Timestamp older than 5 minutes
- System clock skew between client/server

**Invalid HMAC Signature:**
- Incorrect shared secret
- Malformed token format
- Signature calculation error

### Debug Commands

```bash
# Check container logs
container logs nv-mem0

# Verify environment variables
container exec nv-mem0 env | grep MEMORY

# Test connectivity
curl -v http://localhost:7070/health
```

## Production Deployment

### Secret Management

1. **Generate Secure Secret:**
   ```bash
   openssl rand -hex 32
   ```

2. **Store in Environment:**
   ```bash
   export MEMORY_SHARED_SECRET=<generated_secret>
   ```

3. **Verify Configuration:**
   ```bash
   make test-mem0-auth
   ```

### Monitoring

- **Health Checks**: Monitor `/health` endpoint
- **Authentication Logs**: Monitor for 401/403 errors
- **Performance**: Track authentication overhead

### Security Considerations

- **Secret Rotation**: Regularly rotate shared secrets
- **Network Security**: Use HTTPS in production
- **Access Logging**: Monitor authentication attempts
- **Rate Limiting**: Implement request rate limiting

This authentication system provides secure, scalable access control for mem0 operations while maintaining simplicity and performance.
