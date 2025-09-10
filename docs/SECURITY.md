# Security Architecture for Multi-User mem0

## Current Security Status: SINGLE-USER ONLY

**⚠️ CRITICAL: The current implementation is NOT secure for multi-user deployment.**

## Security Vulnerabilities in Proposed Simple Solutions

### Environment Variables (INSECURE)
```bash
export MEM0_USER_ID=user_a  # Can be spoofed by any user
export MEM0_USER_ID=user_b  # No authentication, just identification
```
**Risk**: Any user can set any user_id and access other users' contexts.

### API Keys Without Validation (INSECURE)
```bash
curl -H "X-API-Key: user_a_key"  # If keys are predictable or shared
```
**Risk**: Keys can be guessed, shared, or intercepted.

### Username Parameters (INSECURE)
```bash
./client/mem0 --user user_b context start  # Any user can specify any username
```
**Risk**: Trivial to impersonate other users.

## Secure Multi-User Architecture

### Option 1: JWT Token Authentication
```python
# Secure authentication flow
@app.middleware("http")
async def authenticate_user(request, call_next):
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user_id = payload["user_id"]
        request.state.authenticated_user_id = user_id
    except jwt.InvalidTokenError:
        raise HTTPException(401, "Invalid authentication token")
    return await call_next(request)

# Usage
curl -H "Authorization: Bearer <jwt_token>" /context/start
```

### Option 2: OAuth2 Integration
```python
# Integration with existing identity providers
from fastapi.security import OAuth2PasswordBearer
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@app.post("/context/start")
def start_recording(context: str, token: str = Depends(oauth2_scheme)):
    user_id = verify_oauth_token(token)
    db.set_active_context(context, user_id=user_id)
```

### Option 3: mTLS Client Certificates
```python
# Client certificate authentication
@app.middleware("http")
async def verify_client_cert(request, call_next):
    client_cert = request.headers.get("X-SSL-Client-Cert")
    user_id = verify_certificate(client_cert)
    request.state.authenticated_user_id = user_id
    return await call_next(request)
```

## Authorization Layer

### Context Ownership Validation
```python
def verify_context_access(user_id: int, context_name: str):
    """Ensure user can only access their own contexts"""
    context = db.get_context_by_name(context_name)
    if context and context.user_id != user_id:
        raise HTTPException(403, "Access denied: Context belongs to another user")
    return context

@app.get("/memory")
def get_memory(context: str, request: Request):
    user_id = request.state.authenticated_user_id
    verify_context_access(user_id, context)  # Authorization check
    return db.get_memories(context, user_id=user_id)
```

### Database-Level Security
```sql
-- Row-level security policies
CREATE POLICY user_isolation_memories ON memories
    FOR ALL TO mem0_app
    USING (user_id = current_setting('app.current_user_id')::int);

CREATE POLICY user_isolation_contexts ON recording_contexts  
    FOR ALL TO mem0_app
    USING (user_id = current_setting('app.current_user_id')::int);
```

## Recommended Deployment Architecture

### Single-User Mode (Current - Secure)
```bash
# Each user runs their own mem0 server instance
./manage.sh start  # Port 13370 for user A
./manage.sh start --port 13371  # Port 13371 for user B
```

### Multi-User Mode (Future - Requires Authentication)
```bash
# Shared server with proper authentication
./manage.sh start --auth-mode jwt --secret-key <secure_key>
./manage.sh start --auth-mode oauth2 --provider google
```

## Security Best Practices

### For Development Teams
1. **Use separate server instances per user/team**
2. **Network isolation** (VPN, private networks)
3. **Regular security audits** of context access patterns
4. **Audit logging** of all context operations

### For Production Deployment
1. **Implement proper authentication** before multi-user deployment
2. **Use HTTPS/TLS** for all API communications
3. **Regular token rotation** for API access
4. **Monitor for suspicious cross-user access attempts**

## Current Recommendation

**For immediate use**: Deploy separate mem0 server instances per user/team.
**For future multi-user**: Implement JWT or OAuth2 authentication first.

## Implementation Priority

1. **HIGH**: Add authentication middleware
2. **HIGH**: Implement authorization checks  
3. **MEDIUM**: Add audit logging
4. **MEDIUM**: Database-level security policies
5. **LOW**: Advanced features (SSO, RBAC)

**Until proper authentication is implemented, mem0 should only be deployed in single-user or trusted team environments.**
