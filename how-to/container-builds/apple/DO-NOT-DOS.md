# Apple Container CLI - Do Not Dos
**Critical mistakes to avoid - Learn from pain**

---

## 🚫 NEVER Delete Working Containers Without Backup

### What NOT to do
```bash
# DON'T blindly delete containers that are stopped
container delete test-consolidated-db
container delete nina-intelligence-db

# DON'T assume stopped = broken
container list --all | grep Stopped | xargs container delete
```

### Why
- Stopped containers may contain valuable data
- They may just need to be restarted
- You might have spent hours building them
- **We lost AGE+pgvector data this way on Oct 10, 2025**

### What TO do instead
```bash
# 1. Try to start first
container start {name}

# 2. Check logs if it fails
container logs {name}

# 3. If truly broken, backup first
container export {name} > /tmp/{name}-backup.tar

# 4. Document what was wrong before deleting
echo "Deleted {name} because: {reason}" >> container-deletions.log

# 5. Then delete
container delete {name}
```

---

## 🚫 NEVER Use Cached Builds After Dependency Changes

### What NOT to do
```bash
# You updated requirements.txt
# DON'T do this:
container build -t nina-api:arm64 .
```

### Why
- Docker/container layer caching keeps old dependency layers
- New dependencies won't be installed
- Container will crash at runtime with "ModuleNotFoundError"
- **We wasted hours debugging this on multiple occasions**

### What TO do instead
```bash
# ALWAYS use --no-cache after:
# - requirements.txt changes
# - package.json changes
# - Dockerfile changes
# - Base image updates

container build --no-cache -t nina-api:arm64 .

# Then verify
container run --rm nina-api:arm64 pip list | grep {new_dependency}
```

---

## 🚫 NEVER Mix Container Runtimes in Same Stack

### What NOT to do
```bash
# DON'T run some containers in Docker, some in Apple Container CLI
docker run -d --name ninaivalaigal-dev-db ...
container run -d --name ninaivalaigal-dev-api ...
```

### Why
- Containers can't communicate across runtimes
- Different network namespaces
- Confusing to debug
- **This violated the multi-architecture goal**

### What TO do instead
```bash
# Pick ONE runtime for the entire stack
# For development on Mac: Use Apple Container CLI

container run -d --name ninaivalaigal-dev-db ...
container run -d --name ninaivalaigal-dev-redis ...
container run -d --name ninaivalaigal-dev-api ...

# Exception: Build with Docker, transfer to Apple
docker build -t {image}:arm64 .
docker save {image}:arm64 -o /tmp/{image}.tar
container image load --input /tmp/{image}.tar
# Then run ALL containers with Apple Container CLI
```

---

## 🚫 NEVER Keep Changing Approaches Mid-Session

### What NOT to do
```
Session flow:
1. Try Apple Container CLI → Fails
2. Try Docker → Works
3. Try Colima → Fails
4. Try mixed approach → Confusing
5. Try Apple again → Forgot what worked
6. Try rebuilding from scratch → Lost time
```

### Why
- Wastes time and tokens
- Loses track of what works
- Creates confusion
- **We went in circles for 3+ hours on Oct 10, 2025**

### What TO do instead
```
1. Pick an approach
2. Document why you chose it
3. Stick with it until you prove it doesn't work
4. Document what failed before switching
5. Only switch if you have a clear reason
6. Never go back to a previously failed approach without understanding why it failed
```

---

## 🚫 NEVER Use Legacy `nv-*` Naming

### What NOT to do
```bash
# DON'T use old naming
container run -d --name nv-db ...
container run -d --name nv-api ...
./scripts/nv-db-start.sh
```

### Why
- Violates naming standards
- Conflicts with new naming
- Hard to distinguish from new containers
- **We archived 31 scripts using this naming on Oct 10, 2025**

### What TO do instead
```bash
# ALWAYS use standard naming
container run -d --name ninaivalaigal-dev-db ...
container run -d --name ninaivalaigal-dev-api ...

# Update old scripts or use new ones
./scripts/stack-start-complete.sh
```

---

## 🚫 NEVER Skip Build Verification

### What NOT to do
```bash
# Build and immediately deploy without testing
container build -t nina-api:arm64 .
container run -d --name ninaivalaigal-dev-api nina-api:arm64

# Then discover it crashes
```

### Why
- Runtime failures are harder to debug
- Wastes time restarting/rebuilding
- May affect other services
- **API crashed multiple times due to missing dependencies**

### What TO do instead
```bash
# Build
container build --no-cache -t nina-api:arm64 .

# Verify dependencies
container run --rm nina-api:arm64 pip list | grep structlog
container run --rm nina-api:arm64 python -c "import structlog; print('OK')"

# Test startup
container run --rm nina-api:arm64 python -c "from server.main import app; print('OK')"

# THEN deploy
container run -d --name ninaivalaigal-dev-api nina-api:arm64

# Verify health
sleep 10
curl http://localhost:13390/health
```

---

## 🚫 NEVER Use Hostnames for Container-to-Container Communication

### What NOT to do
```bash
# DON'T use container names as hostnames
DATABASE_URL="postgresql://nina:password@ninaivalaigal-dev-db:5432/nina"  # pragma: allowlist secret
```

### Why
- Apple Container CLI doesn't support hostname resolution between containers
- Will get "Name or service not known" errors
- **This caused Redis connection failures**

### What TO do instead
```bash
# Get container IP address
DB_IP=$(container inspect ninaivalaigal-dev-db | jq -r '.[0].networks[0].address' | cut -d'/' -f1)

# Use IP in connection string
DATABASE_URL="postgresql://nina:password@${DB_IP}:5432/nina"  # pragma: allowlist secret
```

---

## 🚫 NEVER Rebuild Database Without Checking for Existing Data

### What NOT to do
```bash
# DON'T immediately rebuild
container stop ninaivalaigal-dev-db
container delete ninaivalaigal-dev-db
container build --no-cache -t nina-intelligence-db:arm64 .
```

### Why
- May lose valuable data
- May lose hours of setup work
- May lose tested configurations
- **We lost working AGE setup this way**

### What TO do instead
```bash
# 1. Backup existing data
container exec ninaivalaigal-dev-db pg_dump -U nina -d nina > /tmp/db-backup-$(date +%Y%m%d-%H%M%S).sql

# 2. Export container
container export ninaivalaigal-dev-db > /tmp/db-container-backup.tar

# 3. Document current state
container exec ninaivalaigal-dev-db psql -U nina -d nina -c "\dx" > /tmp/db-extensions.txt

# 4. THEN rebuild
container stop ninaivalaigal-dev-db
container delete ninaivalaigal-dev-db
container build --no-cache -t nina-intelligence-db:arm64 .

# 5. Restore data if needed
container run -d --name ninaivalaigal-dev-db nina-intelligence-db:arm64
sleep 15
container exec -i ninaivalaigal-dev-db psql -U nina -d nina < /tmp/db-backup-*.sql
```

---

## 🚫 NEVER Hardcode Secrets in Code or Dockerfiles

### What NOT to do
```dockerfile
# DON'T put secrets in Dockerfile
ENV POSTGRES_PASSWORD=change_me_securely
ENV REDIS_PASSWORD=nina_redis_dev_password
ENV JWT_SECRET=test-jwt-secret-for-ci
```

```python
# DON'T hardcode in Python
DATABASE_URL = "postgresql://nina:change_me_securely@localhost:5432/nina"  # pragma: allowlist secret
```

### Why
- Security risk
- Gets committed to git
- Hard to change per environment
- **Found 7 secret patterns across 47 files**

### What TO do instead
```dockerfile
# Use ARG with no default for build-time secrets
ARG POSTGRES_PASSWORD
ENV POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
```

```python
# Use environment variables
import os
DATABASE_URL = os.getenv("DATABASE_URL")
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")
```

```bash
# Pass at runtime
container run -d \
  -e POSTGRES_PASSWORD="${POSTGRES_PASSWORD}" \  # pragma: allowlist secret
  -e REDIS_PASSWORD="${REDIS_PASSWORD}" \  # pragma: allowlist secret
  ninaivalaigal-dev-db
```

---

## 🚫 NEVER Skip Documentation Updates

### What NOT to do
```bash
# Make changes
container build --no-cache -t nina-api:arm64 .

# Deploy
container run -d --name ninaivalaigal-dev-api nina-api:arm64

# Done! (No documentation)
```

### Why
- Future you forgets what you did
- Others can't understand changes
- Can't debug issues later
- **We repeated same mistakes because documentation was missing**

### What TO do instead
```bash
# After ANY container change:

# 1. Update the container's build document
vim how-to/container-builds/apple/04-api.md

# 2. Document what changed and why
git commit -m "build(api): add structlog dependency for logging

- Added structlog==23.2.0 to requirements.txt
- Rebuilt with --no-cache
- Verified import works
- Fixes logging issues in production"

# 3. Update LESSONS-LEARNED if you learned something
echo "$(date): structlog must be in requirements.txt" >> how-to/container-builds/apple/LESSONS-LEARNED.md
```

---

## 🚫 NEVER Ignore DNS/Network Errors During Build

### What NOT to do
```bash
# Build fails with DNS error
Error: Temporary failure resolving 'apt.postgresql.org'

# Try again immediately
container build -t nina-intelligence-db:arm64 .
# Fails again

# Try 10 more times
# Still fails
```

### Why
- Likely a systemic network issue
- Won't magically resolve
- Wastes time
- **We hit this on Oct 10, 2025 repeatedly**

### What TO do instead
```bash
# 1. Check network
ping apt.postgresql.org
ping deb.debian.org

# 2. If network is down, STOP and use workaround
docker build -t nina-intelligence-db:arm64 .  # Use Docker instead
docker save nina-intelligence-db:arm64 -o /tmp/db.tar
container image load --input /tmp/db.tar

# 3. Document the issue
echo "$(date): Apple Container CLI DNS issues, used Docker workaround" >> ISSUES.log

# 4. Try Apple Container CLI build later when network is stable
```

---

## 🚫 NEVER Start Containers Out of Order

### What NOT to do
```bash
# DON'T start API before database
container run -d --name ninaivalaigal-dev-api ...
container run -d --name ninaivalaigal-dev-db ...

# DON'T start PgBouncer before database
container run -d --name ninaivalaigal-dev-pgbouncer ...
```

### Why
- Services can't connect
- Will fail health checks
- May crash immediately
- **API failed because Redis wasn't ready**

### What TO do instead
```bash
# ALWAYS start in correct order with wait times

# 1. Database
container run -d --name ninaivalaigal-dev-db ...
sleep 15  # Wait for init

# 2. Redis
container run -d --name ninaivalaigal-dev-redis ...
sleep 3

# 3. PgBouncer
container run -d --name ninaivalaigal-dev-pgbouncer ...
sleep 5

# 4. API
container run -d --name ninaivalaigal-dev-api ...
sleep 10

# 5. Verify each service
curl http://localhost:13390/health
```

---

## 🚫 NEVER Assume Prebuilt Images Work on Your Architecture

### What NOT to do
```bash
# DON'T blindly use images from registry
container image pull ghcr.io/arunosaur/ninaivalaigal-db:latest
container run -d --name ninaivalaigal-dev-db ghcr.io/arunosaur/ninaivalaigal-db:latest

# Crashes with "Illegal instruction" or "Segmentation fault"
```

### Why
- Image may be built for different CPU architecture
- AGE/pgvector binaries may not be compatible
- **We hit this with prebuilt image on Oct 10, 2025**

### What TO do instead
```bash
# 1. Check image architecture
container image inspect ghcr.io/arunosaur/ninaivalaigal-db:latest | jq '.architecture'

# 2. If wrong arch, build locally
container build --no-cache -t nina-intelligence-db:arm64 -f Dockerfile.nv-db-age .

# 3. Test in disposable container first
container run --rm --name test-db nina-intelligence-db:arm64 postgres --version

# 4. If works, create permanent container
container run -d --name ninaivalaigal-dev-db nina-intelligence-db:arm64
```

---

## Summary: Critical Don'ts

1. ❌ **NEVER delete without backup**
2. ❌ **NEVER skip `--no-cache` after changes**
3. ❌ **NEVER mix container runtimes**
4. ❌ **NEVER keep switching approaches**
5. ❌ **NEVER use legacy `nv-*` naming**
6. ❌ **NEVER skip build verification**
7. ❌ **NEVER use hostnames for container communication**
8. ❌ **NEVER rebuild database without data backup**
9. ❌ **NEVER hardcode secrets**
10. ❌ **NEVER skip documentation**
11. ❌ **NEVER ignore network errors**
12. ❌ **NEVER start containers out of order**
13. ❌ **NEVER assume prebuilt images work**

**When in doubt, refer to this document. These are lessons learned the hard way.**
