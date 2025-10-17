# Developer C - Python Services Extraction (Week 1)

**Date**: October 16-20, 2025
**Mission**: Extract & containerize 3 Python services from monolith
**Why You**: SPEC-100 lead, container expert
**Time**: 10-12 hours/day for Week 1

---

## 🎯 Your Mission

**Extract from monolith and containerize:**
1. **Core API** (Day 1-2) - Auth, users, teams, RBAC
2. **Business Service** (Day 3-4) - Billing, subscriptions, invoices
3. **Admin/Vendor Service** (Day 5) - Dashboards, analytics, vendor mgmt

**Goal**: Users can sign up by end of Day 2

---

## 📅 Day 1 (Oct 16) - Core API Service

### Morning (4 hours): Code Extraction

**Already done**: ✅ `services/core-api/` directory exists

1. **Identify routers to extract**:
```bash
cd server/routers
ls -la
# Extract these for Core API:
# - auth.py
# - users.py
# - teams.py
# - organizations.py
# - rbac.py
# - tokens.py
```

2. **Copy routers**:
```bash
cp server/routers/auth.py services/core-api/routers/
cp server/routers/users.py services/core-api/routers/
cp server/routers/teams.py services/core-api/routers/
cp server/routers/organizations.py services/core-api/routers/
cp server/routers/rbac.py services/core-api/routers/
cp server/routers/tokens.py services/core-api/routers/
```

3. **Copy models**:
```bash
cp server/models/user.py services/core-api/models/
cp server/models/team.py services/core-api/models/
cp server/models/organization.py services/core-api/models/
cp server/models/token.py services/core-api/models/
cp server/models/role.py services/core-api/models/
```

4. **Create shared utilities**:
```bash
mkdir -p shared/database
mkdir -p shared/middleware
mkdir -p shared/utils

# Copy shared code
cp server/database/operations.py shared/database/
cp server/database/connection.py shared/database/
cp server/middleware/* shared/middleware/
cp server/auth.py shared/utils/
```

### Afternoon (6 hours): Fix Imports & Create Main

5. **Create `services/core-api/main.py`**:
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import sys
from pathlib import Path

# Add shared to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "shared"))

from routers import auth, users, teams, organizations, rbac, tokens
from middleware.json_auth import JSONAuthMiddleware
from middleware.rbac_middleware import RBACMiddleware

app = FastAPI(
    title="Core API Service",
    version="1.0.0",
    description="Authentication and user management"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom middleware
app.add_middleware(JSONAuthMiddleware)
app.add_middleware(RBACMiddleware)

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(users.router, prefix="/users", tags=["users"])
app.include_router(teams.router, prefix="/teams", tags=["teams"])
app.include_router(organizations.router, prefix="/orgs", tags=["organizations"])
app.include_router(rbac.router, prefix="/rbac", tags=["rbac"])
app.include_router(tokens.router, prefix="/tokens", tags=["tokens"])

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "core-api",
        "version": "1.0.0"
    }

@app.get("/")
async def root():
    return {"message": "Core API Service - See /docs for API documentation"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

6. **Fix all imports in routers**:
```python
# OLD (in monolith):
from server.models import User
from server.database import get_database

# NEW (in service):
from ..models import User
from shared.database import get_database
```

**Tool to help**:
```bash
# Find all imports to fix
grep -r "from server\." services/core-api/routers/
grep -r "import server\." services/core-api/routers/

# Replace with sed
find services/core-api -name "*.py" -exec sed -i '' 's/from server\./from shared./g' {} \;
```

7. **Test locally**:
```bash
cd services/core-api
python main.py
# Should start on http://localhost:8000

# Test health
curl http://localhost:8000/health
```

**End of Day 1 Morning Deliverable**: Core API code extracted

---

### Day 1 Afternoon: Requirements & Dockerfile

8. **Create `services/core-api/requirements.txt`**:
```txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
sqlalchemy==2.0.23
psycopg2-binary==2.9.9
redis==5.0.1
pyjwt==2.8.0
bcrypt==4.1.1
python-multipart==0.0.6
pydantic==2.5.0
pydantic-settings==2.1.0
python-dotenv==1.0.0
passlib==1.7.4
email-validator==2.1.0
```

9. **Create `services/core-api/Dockerfile`**:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy shared code first (for caching)
COPY shared/ /app/shared/

# Python dependencies
COPY services/core-api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy service code
COPY services/core-api/ /app/

# Non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

10. **Build container**:
```bash
# From project root
docker build -t core-api:latest -f services/core-api/Dockerfile .

# Transfer to Apple Container CLI
docker save core-api:latest -o /tmp/core-api.tar
container image load --input /tmp/core-api.tar
rm /tmp/core-api.tar
```

**End of Day 1 Deliverable**: Core API containerized

---

## 📅 Day 2 (Oct 17) - Core API Testing & Docker Compose

### Morning (4 hours): Integration Testing

1. **Create `docker-compose.dev.yml`** (project root):
```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    container_name: ninaivalaigal-postgres
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres  # pragma: allowlist secret
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
    container_name: ninaivalaigal-redis
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
    container_name: ninaivalaigal-core-api
    environment:
      DATABASE_URL: postgresql://postgres:postgres@postgres:5432/ninaivalaigal  # pragma: allowlist secret
      REDIS_URL: redis://redis:6379
      JWT_SECRET: development-secret-change-in-production  # pragma: allowlist secret
      SERVICE_NAME: core-api
      SERVICE_PORT: 8000
    ports:
      - "8000:8000"
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

volumes:
  postgres_data:
```

2. **Start services**:
```bash
docker-compose -f docker-compose.dev.yml up -d

# Check status
docker-compose -f docker-compose.dev.yml ps

# Check logs
docker-compose -f docker-compose.dev.yml logs core-api
```

3. **Run migrations**:
```bash
docker-compose -f docker-compose.dev.yml exec core-api \
  alembic upgrade head
```

### Afternoon (6 hours): End-to-End Testing

4. **Test signup**:
```bash
curl -X POST http://localhost:8000/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "TestPass123!",  # pragma: allowlist secret
    "name": "Test User"
  }'
```

5. **Test login**:
```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "TestPass123!"  # pragma: allowlist secret
  }'
```

6. **Test authenticated endpoints**:
```bash
# Save token from login
TOKEN="<token from login response>"

# Get user profile
curl http://localhost:8000/users/me \
  -H "Authorization: Bearer $TOKEN"

# Create team
curl -X POST http://localhost:8000/teams \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "My Team"}'
```

7. **Verify database**:
```bash
docker-compose -f docker-compose.dev.yml exec postgres \
  psql -U postgres -d ninaivalaigal -c "SELECT * FROM users;"
```

**End of Day 2 Deliverable**: **USERS CAN SIGN UP!** 🎉

---

## 📅 Day 3 (Oct 19) - Business Service

### Morning (4 hours): Code Extraction

1. **Extract business routers**:
```bash
cp server/routers/billing.py services/business-service/routers/
cp server/routers/subscriptions.py services/business-service/routers/
cp server/routers/invoices.py services/business-service/routers/
cp server/routers/usage.py services/business-service/routers/
cp server/routers/providers.py services/business-service/routers/
```

2. **Extract business models**:
```bash
cp server/models/billing.py services/business-service/models/
cp server/models/subscription.py services/business-service/models/
cp server/models/invoice.py services/business-service/models/
```

3. **Create `services/business-service/main.py`**:
```python
from fastapi import FastAPI
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "shared"))

from routers import billing, subscriptions, invoices, usage, providers

app = FastAPI(
    title="Business Service",
    version="1.0.0",
    description="Billing, subscriptions, and business operations"
)

app.include_router(billing.router, prefix="/billing", tags=["billing"])
app.include_router(subscriptions.router, prefix="/subscriptions", tags=["subscriptions"])
app.include_router(invoices.router, prefix="/invoices", tags=["invoices"])
app.include_router(usage.router, prefix="/usage", tags=["usage"])
app.include_router(providers.router, prefix="/providers", tags=["providers"])

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "business-service"}
```

### Afternoon (6 hours): Containerization

4. **Create requirements.txt & Dockerfile** (similar to Core API)

5. **Add to docker-compose.dev.yml**:
```yaml
  business-service:
    build:
      context: .
      dockerfile: services/business-service/Dockerfile
    container_name: ninaivalaigal-business
    environment:
      DATABASE_URL: postgresql://postgres:postgres@postgres:5432/ninaivalaigal  # pragma: allowlist secret
      REDIS_URL: redis://redis:6379
      STRIPE_SECRET_KEY: ${STRIPE_SECRET_KEY}
      SERVICE_NAME: business-service
      SERVICE_PORT: 8003
    ports:
      - "8003:8003"
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
```

6. **Test Business Service**:
```bash
docker-compose -f docker-compose.dev.yml up -d business-service
curl http://localhost:8003/health
```

**End of Day 3 Deliverable**: Business Service containerized

---

## 📅 Day 4 (Oct 20) - Admin/Vendor Service

### All Day (10 hours): Extract & Containerize

**Same process as Business Service:**
1. Extract admin/vendor routers
2. Extract analytics models
3. Create main.py
4. Create Dockerfile
5. Add to docker-compose.dev.yml
6. Test

**Routers to extract**:
- admin_analytics.py
- vendor_management.py
- discussion.py
- approval.py
- dashboard.py

**End of Day 4 Deliverable**: All 3 Python services running

---

## 📅 Day 5 (Oct 21) - Integration & Documentation

### Morning (4 hours): Service-to-Service Communication

1. **Test Core API → Business Service**:
```bash
# User signs up in Core API
# Core API calls Business Service to create subscription
```

2. **Add service discovery**:
```python
# In services, use environment variables for other services
CORE_API_URL = os.getenv("CORE_API_URL", "http://core-api:8000")
BUSINESS_SERVICE_URL = os.getenv("BUSINESS_SERVICE_URL", "http://business-service:8003")
```

### Afternoon (6 hours): Documentation

3. **Create service READMEs**:
- `services/core-api/README.md`
- `services/business-service/README.md`
- `services/admin-vendor-service/README.md`

4. **Update main README**:
```markdown
## Running Services

### Start all services:
\`\`\`bash
docker-compose -f docker-compose.dev.yml up -d
\`\`\`

### Check health:
\`\`\`bash
curl http://localhost:8000/health  # Core API
curl http://localhost:8003/health  # Business Service
curl http://localhost:8004/health  # Admin/Vendor Service
\`\`\`
```

**End of Week 1 Deliverable**: 3 Python services fully operational

---

## 🤝 Coordination with Other Developers

### With Developer A (Rust services):
- **Day 5**: Help containerize Memory Service (Rust)
- **Week 2**: Help containerize Graph/AI Service (Rust)
- **Integration**: Add Memory + Graph/AI to docker-compose when ready

### With Developer B (Testing):
- Pair with them on testing each service
- Review their integration tests
- Fix bugs they find

---

## ✅ Success Criteria

**By End of Week 1**:
- [ ] Core API service running (users can sign up)
- [ ] Business Service running (billing works)
- [ ] Admin/Vendor Service running (dashboards work)
- [ ] All services in docker-compose.dev.yml
- [ ] End-to-end user flow working
- [ ] Service-to-service communication working
- [ ] Documentation complete

---

## 🆘 If You Get Stuck

### Import Errors
```bash
# Check Python path
python -c "import sys; print(sys.path)"

# Add __init__.py files
touch services/core-api/__init__.py
touch services/core-api/routers/__init__.py
touch services/core-api/models/__init__.py
```

### Docker Build Fails
```bash
# Build without cache
docker build --no-cache -f services/core-api/Dockerfile .

# Check Dockerfile syntax
docker build -f services/core-api/Dockerfile . 2>&1 | less
```

### Services Can't Connect
```bash
# Check network
docker network ls
docker network inspect ninaivalaigal_default

# Check service names in docker-compose
# Use service name (e.g., "postgres") not "localhost"
```

---

**Focus**: Get services working one at a time. Test before moving on.

**Philosophy**: Working code > perfect code

**Goal**: Users signing up by end of Day 2!
