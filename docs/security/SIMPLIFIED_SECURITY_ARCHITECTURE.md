# Simplified Security Architecture for Ninaivalaigal

## Problem with Individual DB Users
- Password expiration management
- User provisioning/deprovisioning
- Multiple passwords to remember (app + database)
- Complex credential rotation
- Database administration overhead

## Solution: Single DB Connection + JWT Authentication

### Architecture
```
User → JWT Token → Application Server → Single DB Connection → Row-Level Security
```

### Benefits
- ✅ One database credential (managed by admin)
- ✅ Users only need to remember one password (application login)
- ✅ JWT tokens handle authentication
- ✅ Automatic token expiration
- ✅ Easy user management through web interface

## Implementation

### 1. Database Setup (One Time)
```sql
-- Single application database user
CREATE USER ninaivalaigal_app WITH PASSWORD 'secure_app_password';
GRANT ALL PRIVILEGES ON DATABASE ninaivalaigal TO ninaivalaigal_app;

-- Row-level security ensures data isolation
ALTER TABLE memories ENABLE ROW LEVEL SECURITY;
CREATE POLICY user_isolation ON memories FOR ALL USING (user_id = current_setting('app.current_user_id')::integer);
```

### 2. User Registration/Login System
```python
# server/user_management.py
class UserManager:
    def register_user(self, email, password):
        # Hash password and store in users table
        user_id = self.create_user_record(email, password_hash)
        return user_id

    def login_user(self, email, password):
        # Validate credentials and return JWT
        if self.validate_password(email, password):
            token = self.generate_jwt(user_id, expires_in='7d')
            return token
        return None

    def validate_jwt(self, token):
        # Decode JWT and return user info
        return jwt.decode(token, JWT_SECRET)
```

### 3. Connection Management
```python
# server/database.py
class SecureDatabaseManager:
    def __init__(self):
        # Single connection pool for application
        self.connection_pool = psycopg2.pool.ThreadedConnectionPool(
            1, 20,
            host=DB_HOST,
            database=DB_NAME,
            user='ninaivalaigal_app',
            password=APP_DB_PASSWORD
        )

    def get_connection(self, user_id):
        conn = self.connection_pool.getconn()
        # Set user context for row-level security
        with conn.cursor() as cur:
            cur.execute("SET app.current_user_id = %s", (user_id,))
        return conn
```

### 4. User Configuration (Simple)
```json
{
  "mcp.servers": {
    "e^m": {
      "command": "/opt/homebrew/anaconda3/bin/python",
      "args": ["/Users/asrajag/Workspace/mem0/server/mcp_server.py"],
      "env": {
        "NINAIVALAIGAL_SERVER_URL": "https://ninaivalaigal.company.com",
        "NINAIVALAIGAL_USER_TOKEN": "${USER_JWT_TOKEN}"
      }
    }
  }
}
```

### 5. Token Management
```bash
# User gets token once after login
curl -X POST "https://ninaivalaigal.company.com/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "alice@company.com", "password": "user_password"}'

# Response: {"token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...", "expires": "2024-01-20"}

# User sets token in environment
export NINAIVALAIGAL_USER_TOKEN="eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
```

## User Experience Flow

### Initial Setup (Admin)
1. Deploy Ninaivalaigal server
2. Create single database connection
3. Set up user registration endpoint

### User Onboarding
1. User visits registration page: `https://ninaivalaigal.company.com/register`
2. User creates account with email/password
3. System generates JWT token
4. User adds token to VS Code configuration
5. Done! No database credentials needed

### Daily Usage
1. User opens VS Code
2. Uses `@e^M` - token automatically validates
3. If token expires, user logs in again to get new token
4. All data automatically isolated by user ID

## Security Features

### Automatic Token Expiration
```python
# Tokens expire automatically (e.g., 7 days)
def generate_jwt(self, user_id, expires_in='7d'):
    payload = {
        'user_id': user_id,
        'exp': datetime.utcnow() + timedelta(days=7),
        'iat': datetime.utcnow()
    }
    return jwt.encode(payload, JWT_SECRET, algorithm='HS256')
```

### Row-Level Security
```sql
-- Users can only see their own data
CREATE POLICY user_memories ON memories FOR ALL
USING (user_id = current_setting('app.current_user_id')::integer);
```

### Token Refresh
```python
# Automatic token refresh before expiration
def refresh_token_if_needed(self, token):
    decoded = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
    if decoded['exp'] - time.time() < 86400:  # Less than 1 day
        return self.generate_jwt(decoded['user_id'])
    return token
```

## Deployment Configurations

### Development
```bash
export NINAIVALAIGAL_DATABASE_URL="postgresql://ninaivalaigal_app:dev_password@localhost:5432/ninaivalaigal"
export NINAIVALAIGAL_JWT_SECRET="dev-secret-key"
```

### Production
```bash
export NINAIVALAIGAL_DATABASE_URL="postgresql://ninaivalaigal_app:${DB_PASSWORD}@prod-db:5432/ninaivalaigal"
export NINAIVALAIGAL_JWT_SECRET="${JWT_SECRET}"
```

### Cloud (AWS/GCP/Azure)
```bash
# Use cloud secrets manager
export NINAIVALAIGAL_DATABASE_URL="$(aws secretsmanager get-secret-value --secret-id prod/ninaivalaigal/db --query SecretString --output text)"
export NINAIVALAIGAL_JWT_SECRET="$(aws secretsmanager get-secret-value --secret-id prod/ninaivalaigal/jwt --query SecretString --output text)"
```

## Summary

### What Users Manage
- ✅ One application password (for login)
- ✅ JWT token (automatically managed)

### What Admin Manages
- ✅ One database credential (secure, rotatable)
- ✅ JWT secret (secure, rotatable)
- ✅ User accounts through web interface

### Security Benefits
- ✅ Data isolation through row-level security
- ✅ Automatic token expiration
- ✅ No database credentials in user configurations
- ✅ Easy user provisioning/deprovisioning
- ✅ Audit trail through application logs

This approach gives you enterprise-grade security without the password management complexity!
