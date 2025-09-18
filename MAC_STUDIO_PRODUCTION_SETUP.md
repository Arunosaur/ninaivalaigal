# Mac Studio Production Setup - Recommended Configuration

## 🎯 **Architecture Overview**

**Mac Studio (128GB + 20-core M2 Ultra):**
- Heavy services (Postgres + pgvector, PgBouncer, API server)
- All CI/CD workloads
- Build artifacts & caches
- Database backups & observability

**Laptop (Development):**
- Code editing & quick tests
- CLI pointing to Studio API/DB
- Local development with InMemory store

## 🚀 **One-Time Mac Studio Setup**

### 1. System Accounts & Directories
```bash
# Service account for better security
sudo dscl . -create /Users/medhasys
sudo dscl . -create /Users/medhasys UserShell /bin/zsh
sudo dscl . -create /Users/medhasys RealName "Medhasys Service"
sudo dscl . -create /Users/medhasys UniqueID 510
sudo dscl . -create /Users/medhasys PrimaryGroupID 20
sudo dscl . -create /Users/medhasys NFSHomeDirectory /Users/medhasys
sudo mkdir -p /Users/medhasys && sudo chown -R medhasys:staff /Users/medhasys

# Service directories
sudo mkdir -p /srv/medhasys/{volumes/db,logs,artifacts,caches,backups}
sudo chown -R medhasys:staff /srv/medhasys
```

### 2. Container Runtime
```bash
# Docker Desktop (recommended for orchestration)
brew install --cask docker
# Start Docker Desktop once, then configure for auto-start
```

### 3. GitHub Actions Runner
```bash
sudo mkdir -p /opt/actions-runner && sudo chown -R $(whoami) /opt/actions-runner
cd /opt/actions-runner

# Download latest macOS ARM64 runner
curl -o actions.tar.gz -L https://github.com/actions/runner/releases/latest/download/actions-runner-osx-arm64-2.319.1.tar.gz
tar xzf actions.tar.gz

# Configure runner (replace TOKEN with actual token)
./config.sh --url https://github.com/Arunosaur/ninaivalaigal --token <RUNNER_TOKEN> --labels macstudio,arm64,self-hosted --name "mac-studio-runner"

# Install as service
sudo ./svc.sh install
sudo ./svc.sh start
```

### 4. Repository Setup
```bash
# Clone to service user directory
sudo -u medhasys git clone https://github.com/Arunosaur/ninaivalaigal.git /Users/medhasys/ninaivalaigal
sudo chown -R medhasys:staff /Users/medhasys/ninaivalaigal
```

## 🐳 **Production Docker Compose Stack**

### Enhanced `docker-compose.prod.yml`
```yaml
name: medhasys-production
services:
  # PostgreSQL with pgvector
  postgres:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_USER: medhasys
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-secure_password_here}
      POSTGRES_DB: medhasys
      POSTGRES_INITDB_ARGS: "--encoding=UTF-8 --locale=en_US.UTF-8"
    ports: ["5433:5432"]
    volumes:
      - /srv/medhasys/volumes/db:/var/lib/postgresql/data
      - /srv/medhasys/backups:/backups
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U medhasys -d medhasys"]
      interval: 5s
      timeout: 5s
      retries: 20
    restart: unless-stopped
    shm_size: 1gb  # For better Postgres performance

  # PgBouncer for connection pooling
  pgbouncer:
    image: bitnami/pgbouncer:latest
    depends_on: 
      postgres: { condition: service_healthy }
    environment:
      POSTGRESQL_HOST: postgres
      POSTGRESQL_PORT_NUMBER: "5432"
      POSTGRESQL_USERNAME: medhasys
      POSTGRESQL_PASSWORD: ${POSTGRES_PASSWORD:-secure_password_here}
      PGBOUNCER_DATABASE: medhasys
      PGBOUNCER_POOL_MODE: transaction
      PGBOUNCER_MAX_CLIENT_CONN: 1000
      PGBOUNCER_DEFAULT_POOL_SIZE: 25
    ports: ["6432:6432"]
    restart: unless-stopped

  # Ninaivalaigal API Server
  api:
    build:
      context: /Users/medhasys/ninaivalaigal
      dockerfile: Dockerfile
    environment:
      DATABASE_URL: postgresql://medhasys:${POSTGRES_PASSWORD:-secure_password_here}@pgbouncer:6432/medhasys
      NINAIVALAIGAL_JWT_SECRET: ${JWT_SECRET}
      NINAIVALAIGAL_JWT_EXPIRATION_HOURS: "168"
      PYTHONUNBUFFERED: "1"
      ENVIRONMENT: production
    command: >
      bash -c "
        echo 'Waiting for database...' &&
        sleep 10 &&
        echo 'Running migrations...' &&
        alembic upgrade head &&
        echo 'Starting API server...' &&
        uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
      "
    ports: ["13370:8000"]
    depends_on:
      pgbouncer: { condition: service_started }
    volumes:
      - /Users/medhasys/ninaivalaigal:/app:ro  # Read-only for security
      - /srv/medhasys/logs:/app/logs:rw
    healthcheck:
      test: ["CMD", "curl", "-fsS", "http://localhost:8000/healthz"]
      interval: 10s
      timeout: 3s
      retries: 12
    restart: unless-stopped

  # Redis for caching (optional but recommended)
  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]
    volumes:
      - /srv/medhasys/volumes/redis:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 20
    restart: unless-stopped

volumes:
  postgres_data:
    driver: local
  redis_data:
    driver: local
```

### Environment Configuration
```bash
# Create .env file
cat > /srv/medhasys/.env << 'EOF'
POSTGRES_PASSWORD=your_secure_postgres_password_here
JWT_SECRET=your_super_secure_jwt_secret_min_32_chars_here
ENVIRONMENT=production
EOF

# Secure the environment file
chmod 600 /srv/medhasys/.env
chown medhasys:staff /srv/medhasys/.env
```

## 🚀 **Deployment Commands**

### Start the Stack
```bash
cd /srv/medhasys
docker compose -f docker-compose.prod.yml --env-file .env up -d --build
```

### Monitor Services
```bash
# Check service status
docker compose -f docker-compose.prod.yml ps

# View logs
docker compose -f docker-compose.prod.yml logs -f api
docker compose -f docker-compose.prod.yml logs -f postgres

# Health checks
curl http://localhost:13370/healthz
curl http://localhost:13370/healthz/memory
```

## 📊 **Data Migration Strategy**

### From Laptop to Mac Studio
```bash
# 1. On laptop (export data)
pg_dump -Fc "postgresql://mem0user:mem0pass@localhost:5432/mem0db" > ninaivalaigal-export.dump

# 2. Transfer to Mac Studio
scp ninaivalaigal-export.dump medhasys@mac-studio:/srv/medhasys/backups/

# 3. On Mac Studio (import data)
pg_restore -d "postgresql://medhasys:password@localhost:5433/medhasys" \
  --clean --if-exists /srv/medhasys/backups/ninaivalaigal-export.dump
```

## 🔧 **GitHub Actions Integration**

### Update `.github/workflows/memory-store-ci-new.yml`
```yaml
name: memory-store-ci
on:
  push:
    paths:
      - 'server/**'
      - 'alembic/**'
      - 'docker-compose.ci.yml'
      - '.github/workflows/memory-store-ci.yml'
      - 'tests/**'
      - 'scripts/**'
  pull_request:
  schedule:
    - cron: '15 3 * * *'

jobs:
  test-memory-store:
    runs-on: [self-hosted, macstudio]  # Use Mac Studio runner
    timeout-minutes: 30
    strategy:
      fail-fast: false
      matrix: 
        python-version: ['3.10','3.11','3.12']
    
    env:
      DATABASE_URL: postgresql://medhasys:${{ secrets.POSTGRES_PASSWORD }}@localhost:5433/medhasys_test
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
          cache: 'pip'
          
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements-dev.txt
          
      - name: Start test database
        run: |
          docker run -d --name postgres-test \
            -e POSTGRES_USER=medhasys \
            -e POSTGRES_PASSWORD=${{ secrets.POSTGRES_PASSWORD }} \
            -e POSTGRES_DB=medhasys_test \
            -p 5433:5432 \
            pgvector/pgvector:pg16
          
      - name: Wait for database
        run: |
          timeout 30 bash -c 'until pg_isready -h localhost -p 5433 -U medhasys; do sleep 1; done'
          
      - name: Run migrations
        run: alembic upgrade head
        
      - name: Run tests
        run: |
          pytest tests/test_factory_switch_smoke.py -v
          pytest tests/test_security_basic.py -v
          pytest tests/test_auto_recording.py -v
          
      - name: Cleanup
        if: always()
        run: docker rm -f postgres-test || true
```

## 🎯 **Performance Optimizations**

### PostgreSQL Configuration
```bash
# Add to postgres service in docker-compose
environment:
  # Memory settings for 128GB system
  - POSTGRES_SHARED_BUFFERS=32GB
  - POSTGRES_EFFECTIVE_CACHE_SIZE=96GB
  - POSTGRES_WORK_MEM=256MB
  - POSTGRES_MAINTENANCE_WORK_MEM=2GB
  - POSTGRES_MAX_CONNECTIONS=1000
  - POSTGRES_RANDOM_PAGE_COST=1.1  # For SSD
```

### Docker Resource Limits
```yaml
# Add to each service
deploy:
  resources:
    limits:
      memory: 16G  # Adjust per service
      cpus: '4.0'
    reservations:
      memory: 8G
      cpus: '2.0'
```

## 📈 **Monitoring & Observability**

### Health Check Endpoints
- API Health: `http://localhost:13370/healthz`
- Memory Health: `http://localhost:13370/healthz/memory`
- Database: `pg_isready -h localhost -p 5433 -U medhasys`

### Log Management
```bash
# Centralized logging
docker compose -f docker-compose.prod.yml logs -f > /srv/medhasys/logs/combined.log 2>&1 &

# Log rotation
sudo tee /etc/logrotate.d/medhasys << 'EOF'
/srv/medhasys/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 644 medhasys staff
}
EOF
```

## 🔐 **Security Considerations**

1. **Service User**: All services run under `medhasys` user
2. **File Permissions**: Strict permissions on config files
3. **Network**: Services only expose necessary ports
4. **Secrets**: Environment variables, not hardcoded
5. **Updates**: Regular security updates via automated scripts

## 🎉 **Benefits of This Setup**

- **Performance**: 128GB RAM + 20 cores for heavy workloads
- **Reliability**: Always-on services, proper health checks
- **Scalability**: Connection pooling, multi-worker API
- **Development**: Fast local development with remote services
- **CI/CD**: Blazing fast tests on dedicated hardware
- **Observability**: Comprehensive monitoring and logging

This setup gives you the best of both worlds: powerful dedicated infrastructure for heavy lifting, while keeping development agile and responsive!
