---
{}
---




### Refresh Token vs Access Token

| Feature | Access Token (JWT) | Refresh Token |
|---------|-------------------|---------------|
| Duration | 24 hours | 30 days |
| Storage | Client only | Client + Database |
| Revocable | No (stateless JWT) | Yes (database-backed) |
| Purpose | API authentication | Token renewal only |
| Security Level | High (short-lived) | Medium (revocable) |

---

### Architecture

#### Database Schema

**Table:** `refresh_tokens`

```sql
CREATE TABLE refresh_tokens (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    token_hash VARCHAR(255) UNIQUE NOT NULL,  -- SHA256 hash
    expires_at TIMESTAMP NOT NULL,             -- 30 days from creation
    created_at TIMESTAMP DEFAULT NOW(),
    revoked_at TIMESTAMP NULL,                -- NULL = active
    revoked_by UUID REFERENCES users(id),     -- Audit trail
    device_info JSON,                          -- Platform, browser, etc.
    ip_address VARCHAR(45),                    -- Security tracking
    user_agent TEXT                            -- Device identification
);
```

**Indexes:**
- `idx_refresh_tokens_user_id` - Fast user lookups
- `idx_refresh_tokens_expires_at` - Cleanup of expired tokens

#### Security Measures

1. **Token Hashing:** Tokens hashed with SHA256 before storage (never store plaintext)
2. **Expiration:** Automatic 30-day expiration
3. **Revocation:** Can be revoked individually or all at once
4. **Device Tracking:** IP, user agent, device info logged
5. **Audit Trail:** Who revoked the token and when

---

### API Endpoints

#### POST /auth/login (Enhanced)

**Now returns refresh token in addition to access token:**

```bash
curl -X POST http://localhost:13390/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePass123!"
  }'
```

**Response:**
```json
{
  "success": true,
  "user": {
    "jwt_token": "eyJhbGci...",                    // Access token (24h)
    "refresh_token": "abc123xyz...",               // Refresh token (30d)
    "refresh_token_expires": "2025-11-11T19:00:00",
    "user_id": "uuid-here",
    "email": "user@example.com"
  }
}
```

#### POST /auth/token/refresh (NEW)

**Get new access token without re-login:**

```bash
curl -X POST http://localhost:13390/auth/token/refresh \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "abc123xyz..."
  }'
```

**Response:**
```json
{
  "success": true,
  "access_token": "new_eyJhbGci...",
  "token_type": "bearer",
  "expires_in": 86400  // 24 hours in seconds
}
```

**Errors:**
- `401`: Invalid or expired refresh token
- `401`: User not found or inactive
- `500`: Internal server error

#### POST /auth/token/revoke (NEW)

**Revoke specific refresh token (e.g., logout from one device):**

```bash
curl -X POST http://localhost:13390/auth/token/revoke \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "abc123xyz..."
  }'
```

**Response:**
```json
{
  "success": true,
  "message": "Refresh token revoked successfully"
}
```

#### POST /auth/token/revoke-all (NEW)

**Logout from all devices:**

```bash
curl -X POST http://localhost:13390/auth/token/revoke-all \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**Response:**
```json
{
  "success": true,
  "message": "Revoked 3 refresh tokens",
  "tokens_revoked": 3
}
```

---

### Frontend Integration (Developer A)

#### Token Storage

**Implementation:** `frontend-nextjs-customer/utils/tokenStorage.ts`

```typescript
export class TokenStorage {
  private static readonly TOKEN_KEY = 'access_token';
  private static readonly REFRESH_KEY = 'refresh_token';
  private static readonly EXPIRY_KEY = 'token_expires';

  // Store both tokens after login
  static saveTokens(accessToken: string, refreshToken: string): void {
    localStorage.setItem(this.TOKEN_KEY, accessToken);
    localStorage.setItem(this.REFRESH_KEY, refreshToken);

    const payload = this.decodeToken(accessToken);
    if (payload?.exp) {
      localStorage.setItem(this.EXPIRY_KEY, payload.exp.toString());
    }
  }

  // Check if token is valid (not expired)
  static hasValidToken(): boolean {
    const token = localStorage.getItem(this.TOKEN_KEY);
    if (!token) return false;

    const expires = localStorage.getItem(this.EXPIRY_KEY);
    if (expires && Date.now() / 1000 > parseInt(expires)) {
      return false;
    }

    return true;
  }

  // Clear all tokens on logout
  static clearTokens(): void {
    localStorage.removeItem(this.TOKEN_KEY);
    localStorage.removeItem(this.REFRESH_KEY);
    localStorage.removeItem(this.EXPIRY_KEY);
  }
}
```

#### Automatic Token Refresh

**Recommended implementation:**

```typescript
async function ensureValidToken() {
  const accessToken = localStorage.getItem('access_token');
  const refreshToken = localStorage.getItem('refresh_token');

  if (!accessToken || !refreshToken) {
    return null;
  }

  // Check if token expires soon (< 5 minutes)
  const payload = JSON.parse(atob(accessToken.split('.')[1]));
  const expiresAt = payload.exp * 1000;
  const now = Date.now();

  if (expiresAt - now < 5 * 60 * 1000) {
    // Refresh the token
    try {
      const response = await fetch('/auth/token/refresh', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: refreshToken })
      });

      const data = await response.json();
      localStorage.setItem('access_token', data.access_token);
      return data.access_token;
    } catch (error) {
      // Refresh failed, user needs to re-login
      TokenStorage.clearTokens();
      window.location.href = '/login';
      return null;
    }
  }

  return accessToken;
}
```

---

### Integration with Intelligent Sessions

#### How They Work Together

**Intelligent Session Timeouts (Part 1)** determine **WHEN** to prompt renewal:
- Adaptive timeouts based on user activity
- Context-aware session management
- Behavioral learning

**Refresh Tokens (Part 2)** enable **seamless** renewal:
- No re-login required
- Automatic background refresh
- Device-specific revocation

**Combined Benefits:**
1. **Better UX:** Intelligent sessions + seamless refresh = no interruptions
2. **Better Security:** Short access tokens + revocable refresh tokens
3. **Better Control:** Logout all devices, track active sessions
4. **Better Insights:** Device tracking + session analytics

#### Example Flow

```
1. User logs in
   → Access token (24h) + Refresh token (30d) created
   → Intelligent session starts tracking behavior

2. User is actively working
   → Intelligent timeout increases (activity multiplier)
   → Access token automatically refreshes before expiry

3. User goes idle for 2 weeks
   → Access token expires
   → Refresh token still valid
   → User returns, token auto-refreshes seamlessly

4. Security event detected
   → Admin revokes all user's refresh tokens
   → User must re-authenticate next time
```

---

### Backend Implementation

#### Key Functions

**File:** `server/auth.py` (lines 613-769)

```python
def generate_refresh_token() -> str:
    """Generate cryptographically secure 64-character token"""
    return secrets.token_urlsafe(48)

def hash_token(token: str) -> str:
    """SHA256 hash for secure storage"""
    return hashlib.sha256(token.encode()).hexdigest()

def create_refresh_token(user_id, device_info, ip, user_agent):
    """Create and store refresh token (30-day expiry)"""
    token = generate_refresh_token()
    token_hash = hash_token(token)
    expires_at = datetime.utcnow() + timedelta(days=30)

    refresh_token = RefreshToken(
        user_id=user_id,
        token_hash=token_hash,
        expires_at=expires_at,
        device_info=device_info,
        ip_address=ip,
        user_agent=user_agent
    )
    session.add(refresh_token)
    session.commit()

    return token, expires_at

def validate_refresh_token(token: str) -> str | None:
    """Validate token, return user_id if valid"""
    token_hash = hash_token(token)
    refresh_token = session.query(RefreshToken).filter_by(
        token_hash=token_hash
    ).first()

    if not refresh_token or refresh_token.revoked_at:
        return None
    if refresh_token.expires_at < datetime.utcnow():
        return None

    return str(refresh_token.user_id)

def revoke_refresh_token(token: str, revoked_by: str) -> bool:
    """Revoke single refresh token"""
    token_hash = hash_token(token)
    refresh_token = session.query(RefreshToken).filter_by(
        token_hash=token_hash
    ).first()

    if not refresh_token:
        return False

    refresh_token.revoked_at = datetime.utcnow()
    refresh_token.revoked_by = revoked_by
    session.commit()
    return True

def revoke_all_user_tokens(user_id: str) -> int:
    """Revoke all refresh tokens for user (logout all devices)"""
    tokens = session.query(RefreshToken).filter_by(
        user_id=user_id,
        revoked_at=None
    ).all()

    count = 0
    for token in tokens:
        token.revoked_at = datetime.utcnow()
        token.revoked_by = user_id
        count += 1

    session.commit()
    return count
```

---

### Testing

#### Manual Testing

```bash
# 1. Login and get tokens
curl -X POST http://localhost:13390/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password123"}'

# 2. Test refresh
curl -X POST http://localhost:13390/auth/token/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token":"YOUR_REFRESH_TOKEN"}'

# 3. Test revocation
curl -X POST http://localhost:13390/auth/token/revoke \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"refresh_token":"YOUR_REFRESH_TOKEN"}'

# 4. Verify revoked token fails
curl -X POST http://localhost:13390/auth/token/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token":"YOUR_REFRESH_TOKEN"}'
# Should return 401
```

---

### Monitoring

#### Key Metrics

- Refresh token usage rate
- Failed refresh attempts
- Token revocations (individual vs all)
- Active sessions per user
- Device diversity per user

#### Security Alerts

- Multiple failed refresh attempts from same IP
- Refresh token used from unusual location
- Excessive revocations
- Token reuse attempts (if rotation enabled)

---

### Future Enhancements

#### Token Rotation (Planned)

Each refresh generates new refresh token and revokes old one:

**Benefits:**
- Stolen tokens become useless after next refresh
- Reduces attack window
- Industry best practice

#### Active Sessions UI (Planned)

User can view and manage all logged-in devices:

**Features:**
- See all active sessions
- View device info, IP, last activity
- Revoke individual sessions
- "Logout all other devices" button

---

