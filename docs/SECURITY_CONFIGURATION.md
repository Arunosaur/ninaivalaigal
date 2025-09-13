# Security Configuration Guide for mem0

## Overview
This guide covers secure authentication methods for PostgreSQL and JWT secret management to avoid hardcoding credentials in configuration files.

## PostgreSQL Authentication Methods

### Option 1: Environment Variables (Recommended)
Set credentials in your shell environment instead of config files:

```bash
# Add to ~/.bashrc, ~/.zshrc, or ~/.profile
export MEM0_DB_HOST="localhost"
export MEM0_DB_PORT="5432"
export MEM0_DB_NAME="mem0db"
export MEM0_DB_USER="mem0user"
export MEM0_DB_PASSWORD="your_secure_password"

# Construct URL in application
export MEM0_DATABASE_URL="postgresql://${MEM0_DB_USER}:${MEM0_DB_PASSWORD}@${MEM0_DB_HOST}:${MEM0_DB_PORT}/${MEM0_DB_NAME}"
```

### Option 2: PostgreSQL Authentication Methods

#### A. Peer Authentication (Local Development)
Configure PostgreSQL to use system user authentication:

```bash
# Edit /opt/homebrew/var/postgresql@14/pg_hba.conf
local   mem0db    mem0user                     peer

# Create PostgreSQL user matching system user
sudo -u postgres createuser -s $(whoami)
createdb mem0db
```

Database URL becomes: `postgresql:///mem0db`

#### B. Certificate Authentication
```bash
# Generate client certificate
openssl req -new -x509 -days 365 -nodes -text -out client.crt -keyout client.key -subj "/CN=mem0user"

# Configure PostgreSQL for cert auth
# In pg_hba.conf:
hostssl mem0db mem0user 127.0.0.1/32 cert clientcert=1
```

Database URL: `postgresql://mem0user@localhost:5432/mem0db?sslmode=require&sslcert=client.crt&sslkey=client.key`

#### C. Connection Pooling with PgBouncer
```bash
# Install PgBouncer
brew install pgbouncer

# Configure /opt/homebrew/etc/pgbouncer.ini
[databases]
mem0db = host=localhost port=5432 dbname=mem0db

[pgbouncer]
listen_port = 6432
auth_type = trust  # Use with firewall rules
```

Database URL: `postgresql://localhost:6432/mem0db`

### Option 3: Docker Secrets (Production)
```yaml
# docker-compose.yml
version: '3.8'
services:
  mem0:
    image: mem0:latest
    secrets:
      - db_password
      - jwt_secret
    environment:
      - MEM0_DB_PASSWORD_FILE=/run/secrets/db_password
      - MEM0_JWT_SECRET_FILE=/run/secrets/jwt_secret

secrets:
  db_password:
    file: ./secrets/db_password.txt
  jwt_secret:
    file: ./secrets/jwt_secret.txt
```

## JWT Secret Management

### Option 1: Generate Secure JWT Secret
```bash
# Generate a secure random JWT secret
python -c "import secrets; print(secrets.token_urlsafe(32))"
# Example output: kV7x9mP3nQ8wR2tY6uI1oP4sA7dF0gH3jK9lM2nB5vC8xZ

# Store in environment
export MEM0_JWT_SECRET="kV7x9mP3nQ8wR2tY6uI1oP4sA7dF0gH3jK9lM2nB5vC8xZ"
```

### Option 2: Use System Keychain (macOS)
```bash
# Store JWT secret in keychain
security add-generic-password -a mem0 -s mem0-jwt -w "your-jwt-secret"

# Retrieve in application
security find-generic-password -a mem0 -s mem0-jwt -w
```

### Option 3: HashiCorp Vault (Enterprise)
```bash
# Store secret in Vault
vault kv put secret/mem0 jwt_secret="your-secure-jwt-secret"

# Retrieve in application
vault kv get -field=jwt_secret secret/mem0
```

## Updated Configuration Files

### mem0.config.json (No Secrets)
```json
{
  "server": {
    "host": "127.0.0.1",
    "port": 13370,
    "timeout": 10
  },
  "storage": {
    "type": "database",
    "auth_method": "environment",
    "backup_enabled": true,
    "max_memories_per_context": 1000
  },
  "security": {
    "jwt_secret_source": "environment",
    "database_auth_method": "peer"
  }
}
```

### VS Code Settings (Environment Variables)
```json
{
  "mcp.servers": {
    "mem0": {
      "command": "python",
      "args": ["/Users/asrajag/Workspace/mem0/server/mcp_server.py"],
      "env": {
        "MEM0_DATABASE_URL": "${env:MEM0_DATABASE_URL}",
        "MEM0_JWT_SECRET": "${env:MEM0_JWT_SECRET}"
      },
      "cwd": "/Users/asrajag/Workspace/mem0"
    }
  }
}
```

### Claude Desktop Config (Environment Variables)
```json
{
  "mcpServers": {
    "mem0": {
      "command": "python",
      "args": ["/Users/asrajag/Workspace/mem0/server/mcp_server.py"],
      "env": {
        "MEM0_DATABASE_URL": "${MEM0_DATABASE_URL}",
        "MEM0_JWT_SECRET": "${MEM0_JWT_SECRET}"
      },
      "cwd": "/Users/asrajag/Workspace/mem0"
    }
  }
}
```

## Implementation Steps

### Step 1: Set Up Environment Variables
```bash
# Generate JWT secret
JWT_SECRET=$(python -c "import secrets; print(secrets.token_urlsafe(32))")

# Add to your shell profile
echo "export MEM0_JWT_SECRET=\"$JWT_SECRET\"" >> ~/.zshrc
echo "export MEM0_DATABASE_URL=\"postgresql:///mem0db\"" >> ~/.zshrc

# Reload shell
source ~/.zshrc
```

### Step 2: Configure PostgreSQL Peer Authentication
```bash
# Edit PostgreSQL config
sudo vim /opt/homebrew/var/postgresql@14/pg_hba.conf

# Add line:
local   mem0db    $(whoami)                     peer

# Restart PostgreSQL
brew services restart postgresql@14

# Create database
createdb mem0db
```

### Step 3: Update Application Code
The application should read from environment variables with fallback to config file.

### Step 4: Update MCP Configurations
Remove hardcoded credentials from all MCP configuration files and use environment variable references.

## Security Best Practices

1. **Never commit secrets to version control**
2. **Use different secrets for different environments**
3. **Rotate JWT secrets regularly**
4. **Use least-privilege database users**
5. **Enable SSL/TLS for database connections**
6. **Monitor authentication attempts**
7. **Use secrets management systems in production**

## Troubleshooting

### Database Connection Issues
```bash
# Test PostgreSQL connection
psql postgresql:///mem0db -c "SELECT version();"

# Check authentication method
psql postgresql:///mem0db -c "SHOW hba_file;"
```

### JWT Secret Issues
```bash
# Verify JWT secret is loaded
echo $MEM0_JWT_SECRET

# Test JWT generation
python -c "
import os
from jose import jwt
secret = os.getenv('MEM0_JWT_SECRET')
token = jwt.encode({'test': 'data'}, secret, algorithm='HS256')
print('JWT test successful')
"
```

This configuration eliminates hardcoded credentials while maintaining security and usability.
