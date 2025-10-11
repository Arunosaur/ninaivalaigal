# Apple Container CLI - Lessons Learned
**Real incidents, real solutions, real learning**

---

## October 10, 2025 - The Great Container Rebuild Incident

### What Happened
- **Duration**: 3+ hours
- **Objective**: Verify API container and fix naming
- **Result**: Lost working AGE+pgvector database, went in circles

### Timeline
1. **15:00**: Started session, found legacy `nv-db` container running
2. **15:30**: Decided to clean up and use proper naming
3. **16:00**: Deleted stopped `test-consolidated-db` (had AGE+pgvector data)
4. **16:30**: Tried to rebuild with Apple Container CLI → DNS failures
5. **17:00**: Switched to Docker build → Success
6. **17:30**: Tried `container image load` → Hung for 40+ minutes
7. **18:00**: User pointed out we're going in circles
8. **18:30**: Finally, fresh `docker save` + `container image load` → Success

### Root Causes
1. **Assumed stopped containers were broken** - They may have just needed restart
2. **No backup before deletion** - Lost hours of setup work
3. **Kept switching approaches** - Docker → Apple → Docker → Apple
4. **Didn't check for previous solutions** - We had done Docker→Apple transfer before

### What We Lost
- Working `test-consolidated-db` with AGE + pgvector extensions
- Working `nina-intelligence-db` with configured data
- 3+ hours of development time
- Significant token usage

### What We Learned
1. **Never delete stopped containers without investigation**
   ```bash
   # Bad
   container delete test-consolidated-db

   # Good
   container start test-consolidated-db
   container logs test-consolidated-db
   # Only delete if truly broken AND backed up
   ```

2. **Docker→Apple image transfer works, use it**
   ```bash
   docker build -t {image}:arm64 .
   docker save {image}:arm64 -o /tmp/{image}.tar
   container image load --input /tmp/{image}.tar  # This works!
   ```

3. **Stick with one approach until completion**
   - Pick: Apple Container CLI build OR Docker build+transfer
   - Complete it fully
   - Only switch if proven impossible

4. **Document working solutions immediately**
   - "It worked last time" should be in documentation
   - Don't rely on memory

### Prevention
- ✅ Created DO-NOT-DOS.md
- ✅ Created STANDARDS.md
- ✅ Archived legacy scripts
- ✅ Documented Docker→Apple transfer process

---

## September-October 2025 - Missing Dependencies in Containers

### What Happened
- API container built successfully
- Started without errors
- Crashed at runtime with `ModuleNotFoundError: No module named 'structlog'`
- Repeated with stripe, reportlab, and other dependencies

### Timeline
**First Occurrence**:
1. API crashed with missing structlog
2. Added structlog to requirements.txt
3. Rebuilt: `container build -t nina-api:arm64 .`
4. Still crashed - structlog not installed

**Second Occurrence**:
1. Used `--no-cache`: `container build --no-cache -t nina-api:arm64 .`
2. Worked! But then forgot about `--no-cache`
3. Later changes had same issue again

**Third+ Occurrences**:
- Repeated same mistake multiple times
- Finally documented the protocol

### Root Cause
- **Docker/Container layer caching**
- Without `--no-cache`, the `RUN pip install -r requirements.txt` layer is cached
- New dependencies in requirements.txt are ignored
- Build appears successful but dependencies not installed

### What We Learned
```bash
# MANDATORY after any dependency change:
container build --no-cache -t {service}:arm64 .

# Then VERIFY:
container run --rm {service}:arm64 pip list | grep {new_dependency}
```

### Prevention
- Created CRITICAL PROTOCOL memory
- Added to DO-NOT-DOS.md
- Added verification step to build process
- Always use `--no-cache` flag

---

## September 2025 - Runtime Approach Migrations

### What Happened
**The Cycle**:
1. Started with Docker
2. Recommended Colima → Migrated
3. Recommended Apple Container CLI → Migrated
4. Hit issues → Suggested mixed approach
5. User frustrated: "You keep changing approaches"

### Timeline
- **Week 1**: Docker-based stack
- **Week 2**: "Colima is better" → Migration work
- **Week 3**: "Apple Container CLI is native" → Migration work
- **Week 4**: Issues with Apple → "Let's use Docker for database"
- **User**: "This is going in circles"

### Root Cause
- Each approach had pros/cons
- Switching on first obstacle instead of solving it
- Not documenting limitations before switching
- Not having clear criteria for "this approach is best"

### What We Learned
1. **Pick based on requirements, not convenience**
   - Multi-architecture goal → Need pure container solution
   - Mac development → Apple Container CLI optimal
   - CI/CD → Docker with buildx

2. **Solve problems in current approach first**
   - DNS issues? Check network, use workarounds
   - Build issues? Investigate before switching
   - Only switch if fundamentally incompatible

3. **Document why before switching**
   ```
   Switching from X to Y because:
   - X cannot do Z (fundamental limitation)
   - Y solves Z without new problems
   - Migration path is clear
   - No plan to switch back
   ```

### Prevention
- Defined standard: Apple Container CLI for development
- Docker only for building when Apple has DNS issues
- Colima for specific use cases (if any)
- No more runtime migrations without user approval

---

## September 2025 - Redis Authentication Confusion

### What Happened
- API crashed: `Rate limiting error: Authentication required`
- Redis was running without password
- API expected password in URL
- Fixed → Then it crashed again with wrong password

### Timeline
1. Started Redis without password
2. API used `REDIS_URL=redis://redis:6379/0` (hostname)
3. Crashed: "Name or service not known"
4. Fixed to use IP: `REDIS_URL=redis://192.168.64.x:6379/0`
5. Crashed: "Authentication required"
6. Added password: `REDIS_URL=redis://:password@192.168.64.x:6379/0`  # pragma: allowlist secret
7. Crashed: "WRONGPASS invalid username-password pair"
8. Finally used correct password from scripts

### Root Causes
1. **Redis started without password** - Different from scripts
2. **Used hostname instead of IP** - Apple Container CLI doesn't resolve
3. **Wrong password** - Not checking what scripts use
4. **Middleware fails hard** - No graceful degradation

### What We Learned
1. **Always start Redis with password**
   ```bash
   container run -d --name ninaivalaigal-dev-redis \
     redis:7-alpine redis-server \
     --requirepass nina_redis_dev_password \  # pragma: allowlist secret
     --maxmemory 256mb \
     --maxmemory-policy allkeys-lru
   ```

2. **Use IP addresses, not hostnames**
   ```bash
   REDIS_IP=$(container inspect ninaivalaigal-dev-redis | jq -r '.[0].networks[0].address' | cut -d'/' -f1)
   REDIS_URL="redis://:nina_redis_dev_password@${REDIS_IP}:6379/0"
   ```

3. **Check existing scripts for passwords**
   ```bash
   grep -r "REDIS_PASSWORD" scripts/
   # Use what's already there!
   ```

### Prevention
- Documented Redis standard in STANDARDS.md
- Added to CONNECTIVITY.md
- Created template for Redis startup

---

## September 2025 - PgBouncer SCRAM Authentication

### What Happened
- PgBouncer started successfully
- API couldn't connect through it
- Direct DB connection worked
- PgBouncer logs: "Authentication failed"

### Timeline
1. Created userlist.txt with MD5 hash
2. PgBouncer rejected MD5
3. Switched to SCRAM-SHA-256
4. Generated SCRAM hash from macOS - didn't work
5. Discovered need to get hash from actual PostgreSQL
6. `SELECT rolpassword FROM pg_authid` → Success!

### Root Cause
- **PostgreSQL uses SCRAM-SHA-256** by default
- **PgBouncer needs exact hash from PostgreSQL**
- **Can't generate compatible hash externally**
- **Must extract from running database**

### What We Learned
```bash
# Get SCRAM password from database
SCRAM_PASSWORD=$(container exec ninaivalaigal-dev-db \
  psql -U nina -d nina -tAc \
  "SELECT rolpassword FROM pg_authid WHERE rolname = 'nina';" | \
  tr -d ' ')

# Use in userlist.txt
echo "\"nina\" \"${SCRAM_PASSWORD}\"" > /tmp/userlist.txt

# Start PgBouncer with it
container run -d --name ninaivalaigal-dev-pgbouncer \
  -v /tmp/userlist.txt:/etc/pgbouncer/userlist.txt \
  nina-pgbouncer:arm64
```

### Prevention
- Documented in 03-pgbouncer.md
- Added to CONNECTIVITY.md
- Created automated script

---

## Apache AGE Branch Name Change

### What Happened
- **Date**: October 10, 2025
- Dockerfile used: `git checkout PG15/stable`
- Build failed: `error: pathspec 'PG15/stable' did not match any file(s)`
- Actual branch: `PG15`

### Root Cause
- Apache AGE repository changed branch naming
- Was: `PG15/stable`
- Now: `PG15`, `release/PG15/1.4.0`, `release/PG15/1.5.0`

### Solution
```dockerfile
# Before
RUN git checkout PG15/stable

# After
RUN git checkout PG15
```

### Prevention
- Updated Dockerfile.nv-db-age
- Documented in 01-database.md
- Check branch existence before build

---

## Container Image Load Hangs

### What Happened
- **Date**: October 10, 2025
- `container image load --input /tmp/nina-intelligence-db-final.tar`
- Hung for 40+ minutes
- No progress, no errors
- User had to cancel

### Root Cause (Theories)
1. Corrupted tar file
2. Process already using the file
3. Large file size (2GB+)
4. Apple Container CLI limitation

### What Worked
```bash
# Create FRESH tar
docker save nina-intelligence-db:arm64 -o /tmp/nina-db-fresh.tar

# Load immediately (not reusing old tar)
container image load --input /tmp/nina-db-fresh.tar

# Success in ~2 minutes
```

### What We Learned
- Don't reuse old tar files
- Create fresh export each time
- Set timeout: `timeout 180 container image load ...`
- If hangs, kill and retry with fresh export

### Prevention
- Always create fresh tar
- Use timeout command
- Document in OVERVIEW.md

---

## DNS Resolution Failures During Build

### What Happened
- **Date**: October 10, 2025
- `container build` failed during `apt-get update`
- Error: `Temporary failure resolving 'apt.postgresql.org'`
- Error: `Temporary failure resolving 'deb.debian.org'`
- Retried multiple times - all failed

### Timeline
1. First attempt failed
2. Retried immediately - failed
3. Retried 5 more times - all failed
4. Finally switched to Docker - worked
5. Later attempts with Apple - still failed

### Root Cause
- Apple Container CLI build containers couldn't resolve DNS
- Not a temporary network issue
- Systemic problem with Apple Container CLI networking
- Host network was fine

### Solution
```bash
# Workaround: Build with Docker, transfer to Apple
docker build --no-cache -t nina-intelligence-db:arm64 -f Dockerfile.nv-db-age .
docker save nina-intelligence-db:arm64 -o /tmp/db.tar
container image load --input /tmp/db.tar
```

### What We Learned
- DNS in Apple Container CLI build containers is unreliable
- Don't retry indefinitely - use workaround after 2-3 failures
- Keep Docker as backup build tool
- This is a known limitation, not a bug we can fix

### Prevention
- Documented in DO-NOT-DOS.md
- Created Docker fallback procedure
- Added to troubleshooting guide

---

## Key Takeaways Across All Incidents

### Technical
1. **Always use `--no-cache`** after dependency changes
2. **Always backup** before deleting containers
3. **Get SCRAM passwords from PostgreSQL** directly
4. **Use IP addresses**, not hostnames
5. **Start containers in correct order** with wait times
6. **Fresh tar files** for image transfer
7. **Docker fallback** for Apple Container CLI DNS issues

### Process
1. **Don't switch approaches** without clear reason
2. **Document everything** immediately
3. **Check previous solutions** before trying new ones
4. **Stick with one approach** until completion
5. **Verify after every build** before deployment

### Standards
1. **Use `ninaivalaigal-{env}-{service}`** naming
2. **Use standard ports** from PORT_COMPLIANCE
3. **Follow startup order**: DB → Redis → PgBouncer → API
4. **Use environment variables** for secrets
5. **Document all changes** in appropriate guides

---

## Questions for Future Reference

### Before Deleting a Container
- Is it truly broken or just stopped?
- Have I tried starting it?
- Have I checked the logs?
- Have I backed up the data?
- Have I documented why it's being deleted?

### Before Switching Approaches
- Have I tried solving the problem in current approach?
- Is this a fundamental limitation or a solvable issue?
- Have we done this successfully before?
- Is there documentation on the solution?
- What will we lose by switching?

### Before Building
- Are there dependency changes?
- Am I using `--no-cache`?
- How will I verify the build?
- What's my rollback plan if it fails?

### After Building
- Did dependencies install correctly?
- Can I import required modules?
- Does a test container start?
- Is the health check passing?
- Have I documented what changed?

---

## Running Log of Issues

**Format**: `YYYY-MM-DD: Issue - Solution`

- `2025-10-10`: Deleted working containers - Documented backup procedures
- `2025-10-10`: DNS failures in build - Use Docker fallback
- `2025-10-10`: Image load hangs - Use fresh tar files
- `2025-10-10`: Legacy naming confusion - Archived nv-* scripts
- `2025-09-XX`: Missing structlog - Always use --no-cache
- `2025-09-XX`: Redis auth failures - Use IP + correct password
- `2025-09-XX`: PgBouncer auth - Get SCRAM from PostgreSQL
- `2025-09-XX`: Runtime migrations - Stick with Apple Container CLI

---

## Update This Document

**After every debugging session**:
1. Add new incident with date
2. Document what happened
3. Document root cause
4. Document solution
5. Document prevention measures

**This is a living document. Keep it updated!**
