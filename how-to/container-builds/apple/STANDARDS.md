# Apple Container CLI - Standards
**Mandatory naming and configuration standards**

---

## Container Naming Convention

### Pattern
```
ninaivalaigal-{environment}-{service}
```

### Environments
- `dev` - Development (local Mac)
- `test` - Testing/CI
- `staging` - Staging environment
- `prod` - Production

### Services
- `db` - PostgreSQL database
- `redis` - Redis cache
- `pgbouncer` - PgBouncer connection pooler
- `api` - FastAPI backend
- `em` - Enhanced Memory service
- `workers` - Background workers
- `ui-admin` - Admin console UI
- `ui-customer` - Customer UI

### Examples
```bash
✅ ninaivalaigal-dev-db
✅ ninaivalaigal-dev-redis
✅ ninaivalaigal-prod-api
✅ ninaivalaigal-test-workers

❌ nv-db                    # Legacy naming
❌ nina-intelligence-db     # Inconsistent
❌ db                       # Too generic
❌ ninaivalaigal_dev_db     # Wrong separator
```

---

## Image Naming Convention

### Development Images
```
{service}:arm64
{service}:latest
```

### Production Images
```
ghcr.io/arunosaur/ninaivalaigal-{service}:latest
ghcr.io/arunosaur/ninaivalaigal-{service}:{version}
ghcr.io/arunosaur/ninaivalaigal-{service}:latest-arm64
```

### Examples
```bash
# Local development
nina-intelligence-db:arm64
nina-api:arm64
nina-pgbouncer:arm64

# Registry (multi-arch)
ghcr.io/arunosaur/ninaivalaigal-db:latest
ghcr.io/arunosaur/ninaivalaigal-api:v1.2.3
ghcr.io/arunosaur/ninaivalaigal-api:latest-arm64
```

---

## Port Allocation

### Development Ports (+20 offset from production)
```
Service      Prod   Dev    Container
────────────────────────────────────
PostgreSQL   5432   5452   5432
PgBouncer    6432   6452   6432
Redis        6379   6389   6379
API          8000   8020   8000 → Host: 13390 (special)
EM           8001   8021   8001
Workers      -      -      -
UI-Admin     3000   3020   3000
UI-Customer  3001   3021   3001
```

### Port Mapping Pattern
```bash
# Development
container run -p {dev_port}:{container_port}

# Production
container run -p {prod_port}:{container_port}
```

---

## Environment Variables

### Standard Variables
**ALL containers MUST support**:
```bash
ENVIRONMENT=dev|test|staging|prod
LOG_LEVEL=debug|info|warning|error
```

### Database Containers
```bash
POSTGRES_DB=nina
POSTGRES_USER=nina
POSTGRES_PASSWORD={secure_password}
```

### Redis Containers
```bash
REDIS_PASSWORD={secure_password}
REDIS_MAXMEMORY=256mb|512mb|1gb
REDIS_MAXMEMORY_POLICY=allkeys-lru
```

### API Containers
```bash
DATABASE_URL=postgresql://{user}:{pass}@{host}:{port}/{db}  # pragma: allowlist secret
NINAIVALAIGAL_DATABASE_URL={same_as_DATABASE_URL}
REDIS_URL=redis://:{password}@{host}:{port}/0
NINAIVALAIGAL_JWT_SECRET={secure_secret}
PYTHONPATH=/app:/app/server
```

---

## Volume Naming

### Pattern
```
ninaivalaigal_{environment}_{service}_data
```

### Examples
```bash
ninaivalaigal_dev_db_data
ninaivalaigal_dev_redis_data
ninaivalaigal_prod_db_data
```

### Usage
```bash
container run -d \
  -v ninaivalaigal_dev_db_data:/var/lib/postgresql/data \
  ninaivalaigal-dev-db
```

---

## Build Standards

### Always Use --no-cache After:
- Dockerfile changes
- Dependency updates (requirements.txt, package.json, etc.)
- Base image updates
- COPY/ADD instruction changes

```bash
# Correct
container build --no-cache -t {service}:arm64 .

# Wrong (after changes)
container build -t {service}:arm64 .
```

### Build Context
```bash
# Specify context clearly
container build -t {service}:arm64 -f {dockerfile} {context_dir}

# Examples
container build -t nina-api:arm64 -f Dockerfile.api .
container build -t nina-db:arm64 -f scripts/consolidation/Dockerfile.nv-db-age scripts/consolidation/
```

### Verification After Build
```bash
# 1. Verify image exists
container image list | grep {service}

# 2. Verify dependencies
container run --rm {service}:arm64 {health_check}

# Examples
container run --rm nina-api:arm64 pip list | grep structlog
container run --rm nina-db:arm64 psql --version
```

---

## Container Lifecycle

### Startup Order
**MUST start in this order**:
1. Database (`ninaivalaigal-dev-db`)
2. Redis (`ninaivalaigal-dev-redis`)
3. PgBouncer (`ninaivalaigal-dev-pgbouncer`)
4. API (`ninaivalaigal-dev-api`)
5. EM (`ninaivalaigal-dev-em`)
6. Workers (`ninaivalaigal-dev-workers`)
7. UI containers

### Shutdown Order
**MUST stop in reverse order**:
1. UI containers
2. Workers
3. EM
4. API
5. PgBouncer
6. Redis
7. Database (last)

### Wait Times
```bash
# After starting database
sleep 15  # Wait for init scripts

# After starting Redis
sleep 3

# After starting PgBouncer
sleep 5

# After starting API
sleep 10
```

---

## Networking

### Container-to-Container Communication
**ALWAYS use IP addresses**, not hostnames:

```bash
# Get container IP
DB_IP=$(container inspect ninaivalaigal-dev-db | jq -r '.[0].networks[0].address' | cut -d'/' -f1)

# Use in connection string
DATABASE_URL="postgresql://nina:password@${DB_IP}:5432/nina"  # pragma: allowlist secret
```

### Network Inspection
```bash
# Standard command
container inspect {name} | jq -r '.[0].networks[0].address' | cut -d'/' -f1

# Store in variable
export DB_IP=$(container inspect ninaivalaigal-dev-db | jq -r '.[0].networks[0].address' | cut -d'/' -f1)
```

---

## Health Checks

### Database
```bash
container exec ninaivalaigal-dev-db pg_isready -U nina
container exec ninaivalaigal-dev-db psql -U nina -d nina -c "SELECT 1;"
```

### Redis
```bash
container exec ninaivalaigal-dev-redis redis-cli ping
container exec ninaivalaigal-dev-redis redis-cli -a {password} ping
```

### API
```bash
curl -f http://localhost:13390/health
curl -f http://localhost:13390/docs
```

### PgBouncer
```bash
container run --rm pgvector/pgvector:pg15 \
  psql "postgresql://nina:password@${PGB_IP}:6432/nina" -c "SELECT 1;"  # pragma: allowlist secret
```

---

## Logging

### Log Location
```bash
# View logs
container logs {name}

# Follow logs
container logs -f {name}

# Last N lines
container logs --tail 100 {name}

# With timestamps
container logs -t {name}
```

### Log Levels
```bash
# Development
LOG_LEVEL=debug

# Production
LOG_LEVEL=info
```

---

## Security

### Passwords
**NEVER hardcode in**:
- Dockerfiles
- Source code
- Git repositories

**ALWAYS use**:
- Environment variables
- Secrets management
- `.env` files (git-ignored)

### User Permissions
```bash
# Run as non-root when possible
USER {non-root-user}

# Example in Dockerfile
RUN useradd -m -u 1000 appuser
USER appuser
```

---

## Documentation

### Required Documentation
Each container MUST have:
1. **Build guide** (`0X-{service}.md`)
2. **Environment variables** documented
3. **Port mappings** documented
4. **Health check** command
5. **Common issues** and solutions

### Update Frequency
- Update after ANY container changes
- Update after debugging sessions
- Update when fixing issues

---

## Version Control

### Git Commits
```bash
# Good commit messages
git commit -m "build(db): add AGE extension to database container"
git commit -m "fix(api): resolve structlog dependency issue"
git commit -m "docs(containers): update Redis build instructions"

# Bad commit messages
git commit -m "update"
git commit -m "fix stuff"
git commit -m "wip"
```

### Tagging
```bash
# Tag stable builds
git tag -a v1.2.3 -m "Release 1.2.3: Database with AGE + pgvector"
git push origin v1.2.3

# Tag images
container tag {service}:arm64 {service}:v1.2.3
```

---

## Testing

### Pre-Deployment Checklist
- [ ] Image builds successfully
- [ ] Container starts without errors
- [ ] Health check passes
- [ ] Dependencies verified
- [ ] Extensions installed (if applicable)
- [ ] Environment variables work
- [ ] Port mapping correct
- [ ] Volume persistence works
- [ ] Logs show expected output
- [ ] Can connect from other containers

---

## Compliance

### Must Follow
- ✅ Use standard naming convention
- ✅ Use standard ports
- ✅ Document all changes
- ✅ Use `--no-cache` after changes
- ✅ Verify after build
- ✅ Test health checks

### Must Not Do
- ❌ Use legacy `nv-*` naming
- ❌ Hardcode secrets
- ❌ Skip documentation
- ❌ Skip verification
- ❌ Mix architectures
- ❌ Use cached builds after changes

---

## Review Process

Before committing container changes:
1. Build with `--no-cache`
2. Verify dependencies
3. Test health checks
4. Update documentation
5. Test full stack integration
6. Commit with clear message
7. Tag if stable release
