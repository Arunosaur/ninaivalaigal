# Secure Database Setup for Ninaivalaigal

## Individual Database Users (Recommended)

### 1. Create Individual Database Users
```sql
-- For each team member
CREATE USER alice_ninaivalaigal WITH PASSWORD 'alice_secure_password  # pragma: allowlist secret';
CREATE USER bob_ninaivalaigal WITH PASSWORD 'bob_secure_password  # pragma: allowlist secret';
CREATE USER carol_ninaivalaigal WITH PASSWORD 'carol_secure_password  # pragma: allowlist secret';

-- Grant only necessary permissions
GRANT CONNECT ON DATABASE ninaivalaigal TO alice_ninaivalaigal;
GRANT USAGE ON SCHEMA public TO alice_ninaivalaigal;
GRANT SELECT, INSERT, UPDATE, DELETE ON memories TO alice_ninaivalaigal;
GRANT SELECT, INSERT, UPDATE, DELETE ON contexts TO alice_ninaivalaigal;

-- Add row-level security
ALTER TABLE memories ENABLE ROW LEVEL SECURITY;
CREATE POLICY user_memories ON memories FOR ALL TO alice_ninaivalaigal USING (user_id = 101);
```

### 2. Individual VS Code Configuration
```json
{
  "mcp.servers": {
    "e^m": {
      "command": "/opt/homebrew/anaconda3/bin/python",
      "args": ["/Users/asrajag/Workspace/mem0/server/mcp_server.py"],
      "env": {
        "NINAIVALAIGAL_DATABASE_URL": "postgresql://alice_ninaivalaigal:alice_secure_password  # pragma: allowlist secret@server:5432/ninaivalaigal",
        "NINAIVALAIGAL_JWT_SECRET": "${JWT_SECRET}",
        "NINAIVALAIGAL_USER_ID": "101"
      }
    }
  }
}
```

## Option 2: Connection Pooling with Authentication Service

### Architecture
```
User → Authentication Service → Connection Pool → Database
```

### Implementation
```python
# server/auth_service.py
class DatabaseAuthService:
    def get_connection(self, user_token  # pragma: allowlist secret):
        user = self.validate_jwt(user_token  # pragma: allowlist secret)
        if not user:
            raise AuthenticationError()

        # Return connection with user-specific credentials
        return psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=f"{user.username}_ninaivalaigal",
            password  # pragma: allowlist secret=self.get_user_db_password(user.id)
        )
```

### VS Code Configuration
```json
{
  "mcp.servers": {
    "e^m": {
      "command": "/opt/homebrew/anaconda3/bin/python",
      "args": ["/Users/asrajag/Workspace/mem0/server/mcp_server.py"],
      "env": {
        "NINAIVALAIGAL_AUTH_TOKEN": "${USER_JWT_TOKEN}",
        "NINAIVALAIGAL_SERVER_URL": "https://auth.company.com/ninaivalaigal",
        "NINAIVALAIGAL_USER_ID": "alice"
      }
    }
  }
}
```

## Option 3: Cloud-Native Security (AWS/GCP/Azure)

### AWS RDS with IAM Authentication
```json
{
  "env": {
    "NINAIVALAIGAL_DATABASE_URL": "postgresql://alice@rds-instance.amazonaws.com:5432/ninaivalaigal",
    "AWS_REGION": "us-east-1",
    "NINAIVALAIGAL_USE_IAM_AUTH": "true"
  }
}
```

### Implementation
```python
# Use AWS IAM token  # pragma: allowlist secrets instead of password  # pragma: allowlist secrets
import boto3

def get_db_connection(user_id):
    rds_client = boto3.client('rds')
    token  # pragma: allowlist secret = rds_client.generate_db_auth_token(
        DBHostname=DB_HOST,
        Port=5432,
        DBUsername=f"{user_id}_ninaivalaigal"
    )

    return psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=f"{user_id}_ninaivalaigal",
        password  # pragma: allowlist secret=token  # pragma: allowlist secret,
        sslmode='require'
    )
```

## Option 4: Vault-Based Secrets Management

### HashiCorp Vault Integration
```python
import hvac

class VaultDBCredentials:
    def __init__(self):
        self.vault_client = hvac.Client(url='https://vault.company.com')

    def get_db_credentials(self, user_id):
        # Get dynamic database credentials from Vault
        response = self.vault_client.secrets.database.generate_credentials(
            name=f'ninaivalaigal-{user_id}'
        )
        return response['data']['username'], response['data']['password  # pragma: allowlist secret']
```

### VS Code Configuration
```json
{
  "env": {
    "VAULT_ADDR": "https://vault.company.com",
    "VAULT_TOKEN": "${USER_VAULT_TOKEN}",
    "NINAIVALAIGAL_USER_ID": "alice"
  }
}
```

## Security Best Practices Summary

### ✅ Secure Approaches
1. **Individual DB users** with row-level security
2. **Authentication service** with connection pooling
3. **Cloud IAM authentication** (AWS/GCP/Azure)
4. **Vault dynamic credentials** with automatic rotation

### ❌ Avoid
1. Shared database credentials in configuration files
2. Hardcoded password  # pragma: allowlist secrets in VS Code settings
3. Database credentials in version control
4. Same credentials across environments (dev/staging/prod)

### Environment Variables Pattern
```bash
# Each user sets their own
export NINAIVALAIGAL_DB_USER="alice_ninaivalaigal"
export NINAIVALAIGAL_DB_PASSWORD="$(vault kv get -field=password  # pragma: allowlist secret secret/alice/db)"
export NINAIVALAIGAL_USER_ID="alice"
```

This ensures complete credential isolation while maintaining the same user experience.
