# Team Deployment Guide for Ninaivalaigal e^M Recordingsal AI Integration

**Version:** 1.0.0
**Date:** 2025-09-12
**Status:** Production Ready

## Deployment Options for Teams

### Option 1: Centralized Server Deployment (Recommended)

**Architecture:**
```
{{ ... }}
Team Members (IDEs) → Central Ninaivalaigal Server → Shared PostgreSQL Database
```

#### Quick Setup Commands

```bash
# Clone and setup
git clone <your-Ninaivalaigal-repo>
cd Ninaivalaigal

# Install dependencies
pip install -r server/requirements.txt

# Configure environment
export NINAIVALAIGAL_DATABASE_URL="postgresql://user:pass@  # pragma: allowlist secretdb.company.com:5432/Ninaivalaigal_team"
export NINAIVALAIGAL_JWT_SECRET="team-shared-secret"
export NINAIVALAIGAL_HOST="0.0.0.0"
export NINAIVALAIGAL_PORT="13370"

# Start servers
python server/main.py &        # FastAPI server
./scripts/start_mcp_server.sh start  # MCP server with process management

# Test deployment
curl http://localhost:13370/health
./scripts/start_mcp_server.sh test   # Test MCP functionality
```

#### Team Member IDE Configuration

**VS Code/Windsurf** (`.vscode/settings.json`) - **VERIFIED WORKING**:
```json
{
  "mcp.servers": {
    "Ninaivalaigal": {
      "command": "/opt/homebrew/anaconda3/bin/python3.11",
      "args": ["/path/to/Ninaivalaigal/server/mcp_server.py"],
      "cwd": "/path/to/Ninaivalaigal",
      "env": {
        "NINAIVALAIGAL_DATABASE_URL": "postgresql://user:pass@  # pragma: allowlist secretserver.company.com:5432/Ninaivalaigal_team",
        "NINAIVALAIGAL_JWT_SECRET": "team-shared-secret",
        "PYTHONPATH": "/path/to/Ninaivalaigal/server"
      }
    }
  }
}
```

**Note**: Use Anaconda Python path as it includes all required MCP dependencies. System Python may lack necessary packages.

### Option 2: Docker Deployment (Easiest)

#### Docker Compose Setup
```yaml
# docker-compose.yml
version: '3.8'
services:
  Ninaivalaigal-mcp:
    build:
      context: .
      dockerfile: deploy/Dockerfile
    ports:
      - "13371:13371"
    environment:
      - NINAIVALAIGAL_DATABASE_URL=postgresql://postgres:password@db:5432/Ninaivalaigal
      - NINAIVALAIGAL_JWT_SECRET=${NINAIVALAIGAL_JWT_SECRET}
    depends_on:
      - db
    volumes:
      - ./server:/app/server
    command: python server/mcp_server.py --host 0.0.0.0 --port 13371

  Ninaivalaigal-api:
    build:
      context: .
      dockerfile: deploy/Dockerfile
    ports:
      - "13370:13370"
    environment:
      - NINAIVALAIGAL_DATABASE_URL=postgresql://postgres:password@db:5432/Ninaivalaigal
      - NINAIVALAIGAL_JWT_SECRET=${NINAIVALAIGAL_JWT_SECRET}
    depends_on:
      - db
    command: python server/main.py --host 0.0.0.0 --port 13370

  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=Ninaivalaigal
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./scripts/create-postgresql-schema.sql:/docker-entrypoint-initdb.d/init.sql

volumes:
  postgres_data:
```

#### Team Member Configuration
```json
{
  "servers": {
    "Ninaivalaigal": {
      "command": "docker",
      "args": ["run", "--rm", "-i", "Ninaivalaigal/mcp-client", "server.company.com", "13371"],
      "type": "stdio"
    }
  }
}
```

### Option 3: Cloud Deployment (Scalable)

#### Kubernetes Deployment
```yaml
# k8s/Ninaivalaigal-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: Ninaivalaigal-mcp
spec:
  replicas: 3
  selector:
    matchLabels:
      app: Ninaivalaigal-mcp
  template:
    metadata:
      labels:
        app: Ninaivalaigal-mcp
    spec:
      containers:
      - name: Ninaivalaigal-mcp
        image: Ninaivalaigal/server:latest
        ports:
        - containerPort: 13371
        env:
        - name: NINAIVALAIGAL_DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: Ninaivalaigal-secrets
              key: database-url
        command: ["python", "server/mcp_server.py", "--host", "0.0.0.0", "--port", "13371"]
---
apiVersion: v1
kind: Service
metadata:
  name: Ninaivalaigal-mcp-service
spec:
  selector:
    app: Ninaivalaigal-mcp
  ports:
  - port: 13371
    targetPort: 13371
  type: LoadBalancer
```

#### Team Configuration
```json
{
  "servers": {
    "Ninaivalaigal": {
      "command": "kubectl",
      "args": ["exec", "-i", "deployment/Ninaivalaigal-mcp", "--", "python", "-c", "import sys; sys.stdin.read()"],
      "type": "stdio"
    }
  }
}
```

## Environment-Agnostic Configuration

### Universal MCP Client Script
```python
#!/usr/bin/env python3
# scripts/mcp_client.py
import os
import sys
import socket
import json
import subprocess

def get_Ninaivalaigal_server():
    # Priority order: ENV -> Config file -> Discovery -> Default

    # 1. Environment variables
    host = os.getenv('NINAIVALAIGAL_SERVER_HOST')
    port = os.getenv('NINAIVALAIGAL_SERVER_PORT', '13371')

    if host:
        return host, int(port)

    # 2. Config file
    config_paths = [
        os.path.expanduser('~/.Ninaivalaigal/config.json'),
        os.path.join(os.getcwd(), '.Ninaivalaigal.json'),
        '/etc/Ninaivalaigal/config.json'
    ]

    for config_path in config_paths:
        if os.path.exists(config_path):
            with open(config_path) as f:
                config = json.load(f)
                return config.get('host', 'localhost'), config.get('port', 13371)

    # 3. Service discovery (Docker/K8s)
    if os.getenv('KUBERNETES_SERVICE_HOST'):
        return 'Ninaivalaigal-mcp-service', 13371

    if os.path.exists('/.dockerenv'):
        return 'Ninaivalaigal-mcp', 13371

    # 4. Default local
    return 'localhost', 13371

def main():
    host, port = get_Ninaivalaigal_server()

    try:
        # Connect to Ninaivalaigal MCP server
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((host, port))

        # Proxy stdin/stdout
        while True:
            data = sys.stdin.readline()
            if not data:
                break
            sock.send(data.encode())
            response = sock.recv(4096)
            sys.stdout.write(response.decode())
            sys.stdout.flush()

    except Exception as e:
        print(f"Error connecting to Ninaivalaigal server at {host}:{port}: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        sock.close()

if __name__ == "__main__":
    main()
```

### Universal IDE Configuration
```json
{
  "servers": {
    "Ninaivalaigal": {
      "command": "python",
      "args": ["/path/to/Ninaivalaigal/scripts/mcp_client.py"],
      "type": "stdio",
      "env": {
        "NINAIVALAIGAL_SERVER_HOST": "${NINAIVALAIGAL_SERVER_HOST:-localhost}",
        "NINAIVALAIGAL_SERVER_PORT": "${NINAIVALAIGAL_SERVER_PORT:-13371}"
      }
    }
  }
}
```

## Team Configuration Examples

### Small Team (2-10 developers)
```bash
# Single server deployment
export NINAIVALAIGAL_SERVER_HOST="Ninaivalaigal.team.local"
export NINAIVALAIGAL_DATABASE_URL="postgresql://Ninaivalaigal:password@db.team.local/Ninaivalaigal"

# Each developer's ~/.bashrc or ~/.zshrc
echo 'export NINAIVALAIGAL_SERVER_HOST="Ninaivalaigal.team.local"' >> ~/.bashrc
```

### Medium Team (10-50 developers)
```yaml
# Docker Swarm or Kubernetes
# Load balanced with Redis caching
services:
  Ninaivalaigal-mcp:
    deploy:
      replicas: 3
    environment:
      - NINAIVALAIGAL_REDIS_URL=redis://redis:6379
      - NINAIVALAIGAL_DATABASE_URL=postgresql://Ninaivalaigal:password@postgres-cluster/Ninaivalaigal
```

### Large Organization (50+ developers)
```yaml
# Multi-region deployment with CDN
# Separate databases per region/team
apiVersion: v1
kind: ConfigMap
metadata:
  name: Ninaivalaigal-config
data:
  regions: |
    us-east: Ninaivalaigal-us-east.company.com:13371
    us-west: Ninaivalaigal-us-west.company.com:13371
    eu: Ninaivalaigal-eu.company.com:13371
```

## Security Considerations

### Authentication
```bash
# JWT tokens for team @e^Mbers
export NINAIVALAIGAL_JWT_TOKEN="eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."

# Or OAuth integration
export NINAIVALAIGAL_OAUTH_PROVIDER="google"
export NINAIVALAIGAL_OAUTH_CLIENT_ID="your-client-id"
```

### Network Security
```yaml
# Firewall rules
- allow port 13371 from team network only
- require TLS for external connections
- VPN access for remote developers

# nginx proxy with SSL
server {
    listen 443 ssl;
    server_name Ninaivalaigal.company.com;

    location /mcp {
        proxy_pass http://localhost:13371;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

## Deployment Scripts

### Automated Team Setup
```bash
#!/bin/bash
# deploy/setup-team.sh

# 1. Deploy server
docker-compose up -d

# 2. Initialize database
docker-compose exec Ninaivalaigal-api python -c "
from database import DatabaseManager
db = DatabaseManager()
db.create_tables()
"

# 3. Create team admin user
docker-compose exec Ninaivalaigal-api python -c "
from auth import create_user
create_user('admin@company.com', 'secure-password', role='admin')
"

# 4. Generate team configuration
cat > team-config.json << EOF
{
  "server_host": "$(hostname -f)",
  "server_port": 13371,
  "database_url": "$NINAIVALAIGAL_DATABASE_URL",
  "team_id": 1,
  "organization_id": 1
}
EOF

echo "Team deployment complete!"
echo "Share this configuration with team @e^Mbers:"
echo "export NINAIVALAIGAL_SERVER_HOST=$(hostname -f)"
echo "export NINAIVALAIGAL_SERVER_PORT=13371"
```

### Developer Onboarding
```bash
#!/bin/bash
# scripts/onboard-developer.sh

DEVELOPER_EMAIL=$1
NINAIVALAIGAL_SERVER_HOST=${2:-"Ninaivalaigal.company.com"}

# 1. Create user account
curl -X POST "http://$NINAIVALAIGAL_SERVER_HOST:13370/users" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$DEVELOPER_EMAIL\",\"password\":\"temp-password\"}"

# 2. Generate IDE configuration
mkdir -p ~/.Ninaivalaigal
cat > ~/.Ninaivalaigal/config.json << EOF
{
  "host": "$NINAIVALAIGAL_SERVER_HOST",
  "port": 13371,
  "user_email": "$DEVELOPER_EMAIL"
}
EOF

# 3. Create IDE configuration
mkdir -p .vscode
cat > .vscode/mcp.json << EOF
{
  "servers": {
    "Ninaivalaigal": {
      "command": "python",
      "args": ["$(pwd)/scripts/mcp_client.py"],
      "type": "stdio"
    }
  }
}
EOF

echo "Developer onboarding complete for $DEVELOPER_EMAIL"
echo "IDE configuration created in .vscode/mcp.json"
```

## Monitoring and Maintenance

### Health Checks
```bash
# Check server status
curl http://Ninaivalaigal.company.com:13370/health

# Check MCP connectivity
echo '{"jsonrpc":"2.0","id":1,"method":"ping"}' | python scripts/mcp_client.py
```

### Backup Strategy
```bash
# Database backup
pg_dump $NINAIVALAIGAL_DATABASE_URL > backups/Ninaivalaigal-$(date +%Y%m%d).sql

# Configuration backup
tar -czf backups/Ninaivalaigal-config-$(date +%Y%m%d).tar.gz \
  server/ scripts/ deploy/ docs/
```

This approach eliminates hardcoded local paths and provides flexible deployment options for teams of any size!
