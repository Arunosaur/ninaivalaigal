# Tomorrow's Task - All Developers

**Date**: October 16, 2025
**Sprint**: SPEC-100 Stage 3 - Day 1
**Goal**: Get Core API service running so users can sign up
**Team**: All 3 developers working together
**Time**: 8-12 hours

---

## 🎯 Mission

**Create the Core API service in a container and make user signup work**

**Why**: Users can't even sign up right now. Everything is in a monolith that's not running.

**Success**: User can sign up via `POST http://localhost:8000/auth/signup`

---

## 👥 Team Assignments

### Developer C - Service Lead (10-12 hours)
**Focus**: Create, containerize, and deploy Core API service

**Tasks**:
1. Create service directory structure
2. Build Core API Dockerfile
3. Extract auth/user/team code from monolith
4. Get Core API running in container
5. Test signup/login endpoints

---

### Developer A - Integration Helper (6-8 hours)
**Focus**: Support Core API extraction and validate integration

**Tasks**:
1. Document current auth flow
2. Help extract code from monolith
3. Fix database connection issues
4. Write integration tests
5. Validate GraphOps can integrate later

---

### Developer B - Testing & Docs (4-6 hours)
**Focus**: Test Core API and document it

**Tasks**:
1. Verify OpenAPI contract matches code
2. Write endpoint tests
3. Test error handling
4. Document Core API service
5. Create usage examples

---

## 📋 Detailed Tasks

### Phase 1: Setup (Morning - 2 hours)

**Developer C**:
```bash
# Create service structure
mkdir -p services/core-api/{routers,models,middleware}
mkdir -p shared/{contracts,models,utils}

# Create Core API requirements
touch services/core-api/requirements.txt
touch services/core-api/Dockerfile
touch services/core-api/main.py
```

**Developer A**:
```bash
# Document current code
cd server
ls routers/  # List what needs to be extracted
cat routers/auth.py | head -50  # Review auth code
```

**Developer B**:
```bash
# Review contracts
cat shared/contracts/core-api/v1/openapi.yaml
# List endpoints we need to support
```

---

### Phase 2: Extract Code (Late Morning - 4 hours)

**Developer C** (Lead this phase):

1. **Move routers**:
```bash
cp server/routers/auth.py services/core-api/routers/
cp server/routers/users.py services/core-api/routers/
cp server/routers/teams.py services/core-api/routers/
cp server/routers/organizations.py services/core-api/routers/
cp server/routers/rbac.py services/core-api/routers/
```

2. **Move models**:
```bash
cp server/models/user.py services/core-api/models/
cp server/models/team.py services/core-api/models/
cp server/models/organization.py services/core-api/models/
```

3. **Create main.py**:
```python
# services/core-api/main.py
from fastapi import FastAPI
from .routers import auth, users, teams, organizations, rbac

app = FastAPI(title="Core API Service", version="1.0.0")

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(users.router, prefix="/users", tags=["users"])
app.include_router(teams.router, prefix="/teams", tags=["teams"])
app.include_router(organizations.router, prefix="/orgs", tags=["organizations"])
app.include_router(rbac.router, prefix="/rbac", tags=["rbac"])

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "core-api"}
```

4. **Fix imports** (This will take time!):
   - Change `from server.models` → `from .models`
   - Change `from server.utils` → `from shared.utils`
   - Change `from server.database` → `from shared.database`

**Developer A** (Pair with Developer C):
- Help fix import errors
- Resolve circular dependencies
- Fix database connection issues

**Developer B**:
- Write tests for each endpoint as they're extracted
- Document API changes

---

### Phase 3: Containerize (Early Afternoon - 3 hours)

**Developer C** (Lead):

1. **Create requirements.txt**:
```txt
# services/core-api/requirements.txt
fastapi==0.104.1
uvicorn==0.24.0
sqlalchemy==2.0.23
psycopg2-binary==2.9.9
redis==5.0.1
pyjwt==2.8.0
bcrypt==4.1.1
python-multipart==0.0.6
```

2. **Create Dockerfile**:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies
COPY services/core-api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy shared code
COPY shared/ ./shared/

# Copy service code
COPY services/core-api/ ./

# Non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

3. **Build container**:
```bash
# Try Docker first (DNS workaround)
docker build -t core-api:latest -f services/core-api/Dockerfile .

# Transfer to Apple Container CLI
docker save core-api:latest -o /tmp/core-api.tar
container image load --input /tmp/core-api.tar
rm /tmp/core-api.tar
```

**Developer A**:
- Help resolve Docker build errors
- Fix dependency issues
- Test container locally

**Developer B**:
- Document build process
- Create troubleshooting guide

---

### Phase 4: Run & Test (Afternoon - 3 hours)

**Developer C**:

1. **Create docker-compose.yml**:
```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: ninaivalaigal
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 5

  core-api:
    build:
      context: .
      dockerfile: services/core-api/Dockerfile
    container_name: core-api
    environment:
      DATABASE_URL: postgresql://postgres:postgres@postgres:5432/ninaivalaigal  # pragma: allowlist secret
      REDIS_URL: redis://redis:6379
      JWT_SECRET: development-secret-change-in-production  # pragma: allowlist secret
    ports:
      - "8000:8000"
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy

volumes:
  postgres_data:
```

2. **Start services**:
```bash
docker-compose up -d

# Check health
curl http://localhost:8000/health
```

3. **Run migrations**:
```bash
# Inside core-api container
docker-compose exec core-api alembic upgrade head
```

**Developer A**:
- Write integration tests
- Test signup flow
- Test login flow
- Test token refresh

**Developer B**:
- Test all endpoints against OpenAPI schema
- Document any contract mismatches
- Write usage examples

---

## ✅ End of Day Success Criteria

**Must Have**:
- [ ] Core API service builds successfully
- [ ] Core API runs in container
- [ ] PostgreSQL + Redis running
- [ ] Can signup: `curl -X POST http://localhost:8000/auth/signup -d '{"email":"test@test.com","password":"test123","name":"Test"}'`  # pragma: allowlist secret
- [ ] Can login: `curl -X POST http://localhost:8000/auth/login -d '{"email":"test@test.com","password":"test123"}'`  # pragma: allowlist secret
- [ ] JWT token returned and works

**Nice to Have**:
- [ ] Integration tests passing
- [ ] README documentation written
- [ ] Docker compose working smoothly

**NOT Required**:
- ❌ Memory service (that's Day 2-3)
- ❌ Other services
- ❌ Production deployment
- ❌ CI/CD workflows

---

## 🆘 If Things Go Wrong

### Build Fails
1. Check Dockerfile syntax
2. Verify all files exist
3. Check requirements.txt has correct versions
4. Try building without cache: `docker build --no-cache`

### Import Errors
1. Check `__init__.py` files exist
2. Verify relative imports: `from .models` not `from models`
3. Check shared/ is copied to container
4. Use `PYTHONPATH=/app` if needed

### Database Connection Fails
1. Check PostgreSQL is running: `docker-compose ps postgres`
2. Verify DATABASE_URL format
3. Check migrations ran: `docker-compose exec core-api alembic current`
4. Test direct connection: `psql postgresql://postgres:postgres@localhost:5432/ninaivalaigal`  # pragma: allowlist secret

### Container Won't Start
1. Check logs: `docker-compose logs core-api`
2. Verify health check works
3. Check ports aren't in use: `lsof -i :8000`
4. Try running locally first: `cd services/core-api && uvicorn main:app`

---

## 📊 Time Breakdown

| Phase | Time | Lead |
|-------|------|------|
| Setup | 2 hours | Developer C |
| Extract Code | 4 hours | All 3 |
| Containerize | 3 hours | Developer C |
| Run & Test | 3 hours | All 3 |
| **Total** | **12 hours** | **Team effort** |

---

## 🎯 Next Steps (Day 2)

Once Core API works:
1. Extract Memory Service
2. Get memories CRUD working
3. Test Core API → Memory Service communication

---

**Focus**: One service at a time. Get it working before moving on.

**Philosophy**: Working code > perfect code

**Goal**: Users sign up by end of day tomorrow!
