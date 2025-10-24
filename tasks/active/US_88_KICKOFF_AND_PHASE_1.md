# US #88: Core API Decomposition - Phase 1 Kickoff

**Date:** October 22, 2025, 7:50 AM
**Status:** 🚀 Starting Phase 1
**Timeline:** 4 weeks (reduced from 6 weeks thanks to US #91)
**Owner:** Cascade AI + Developer A

---

## 🎯 **READINESS VALIDATION**

### **US #91 Prep Work: ✅ COMPLETE**

**Delivered by US #91:**
- ✅ 7 service boundaries identified and mapped
- ✅ 51+ APIs categorized
- ✅ Interface contracts created (`shared/models/service_interfaces.py`)
- ✅ Circular dependencies documented with solutions
- ✅ 4-phase migration plan complete
- ✅ Service communication patterns defined

**Impact:** Discovery phase eliminated, 2 weeks saved!

---

### **Dependency Check:**

| Dependency | Status | Notes |
|------------|--------|-------|
| **Task #79: Contracts** | ✅ | OpenAPI specs exist in `shared/contracts/` |
| **Task #83: Gateway** | ⚠️ | Go gRPC Gateway exists (port 13395), needs validation |
| **Memory Service (Rust)** | ✅ | Operational on port 13393 |
| **GraphOps (Rust)** | ✅ | Operational on port 13398 |
| **Interface Contracts** | ✅ | Created in US #91 |

**Status:** ✅ Ready to proceed with Phase 1

---

## 📋 **US #88 OVERVIEW**

### **Goal:**
Break monolithic Core API (49K lines, 54 routers) into independently deployable microservices.

### **Current Monolith:**
- **Location:** `services/core-api/`
- **Lines:** ~49,000
- **Routers:** 54 (19 currently loaded in main.py)
- **Port:** 13390

### **Target Architecture (From US #91):**

```
┌─────────────────────────────────────────────────────────────┐
│                     gRPC Gateway (Go)                       │
│                      Port: 13395                            │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌───────────────┐   ┌───────────────┐   ┌───────────────┐
│  Core API     │   │ Memory        │   │ GraphOps      │
│  (Auth/Users) │   │ Service (Rust)│   │ (Rust)        │
│  Port: 13390  │   │ Port: 13393   │   │ Port: 13398   │
└───────────────┘   └───────────────┘   └───────────────┘
        │                     │                     │
        └─────────────────────┼─────────────────────┘
                              │
                    ┌─────────────────┐
                    │   PostgreSQL    │
                    │   + pgvector    │
                    └─────────────────┘
```

---

## 🚀 **PHASE 1: EXTRACT CORE API SERVICE**

### **Timeline:** Week 1-2 (of 4-week plan)

### **Scope:**
Extract Core API service with authentication and user management.

**Routers to Keep in Core API:**
- ✅ `signup_api.py` - User registration
- ✅ `users.py` - User CRUD
- ✅ `rbac_api.py` - RBAC
- ✅ `token_api.py` - JWT tokens
- ✅ `session_api.py` - Sessions

**Routers to Remove (migrate later):**
- ⏭️ `teams.py` → Team Service (Phase 2)
- ⏭️ `organizations.py` → Team Service (Phase 2)
- ⏭️ `memory_api.py` → Memory Service (Rust)
- ⏭️ All other routers per US #91 mapping

---

## 📁 **PHASE 1 IMPLEMENTATION PLAN**

### **Step 1: Create Clean Core API Structure**

**Directory Structure:**
```
services/
├── core-api/                    # Existing (to clean up)
└── core-api-clean/              # New lightweight service
    ├── Dockerfile               # Independent container
    ├── requirements.txt         # Minimal dependencies
    ├── main.py                  # Clean FastAPI app
    ├── routers/
    │   ├── auth.py             # Authentication
    │   ├── users.py            # User management
    │   ├── rbac.py             # RBAC
    │   ├── tokens.py           # Token management
    │   └── sessions.py         # Session management
    ├── models/                 # Pydantic models
    ├── database/               # DB utilities
    └── tests/                  # Unit tests
```

---

### **Step 2: Create Dockerfile for Core API**

**File:** `services/core-api-clean/Dockerfile`

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Expose port
EXPOSE 13390

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:13390/health || exit 1

# Run application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "13390"]
```

---

### **Step 3: Create Minimal requirements.txt**

**File:** `services/core-api-clean/requirements.txt`

```
# Core FastAPI
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
pydantic-settings==2.1.0

# Database
sqlalchemy==2.0.23
alembic==1.12.1
asyncpg==0.29.0
psycopg2-binary==2.9.9

# Authentication
pyjwt==2.8.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6

# Redis (for sessions)
redis==5.0.1
aioredis==2.0.1

# Utilities
python-dotenv==1.0.0
structlog==23.2.0
```

---

### **Step 4: Create Clean main.py**

**File:** `services/core-api-clean/main.py`

```python
"""
Core API Service - Authentication & User Management

Extracted from monolithic Core API as part of US #88.
Handles: Auth, Users, RBAC, Tokens, Sessions
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import structlog

from routers import auth, users, rbac, tokens, sessions
from database import init_db

# Configure logging
structlog.configure(
    processors=[
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ]
)

logger = structlog.get_logger()

# Create FastAPI app
app = FastAPI(
    title="Core API Service",
    description="Authentication and User Management",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure per environment
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(users.router, prefix="/api/v1/users", tags=["users"])
app.include_router(rbac.router, prefix="/api/v1/rbac", tags=["rbac"])
app.include_router(tokens.router, prefix="/api/v1/tokens", tags=["tokens"])
app.include_router(sessions.router, prefix="/api/v1/sessions", tags=["sessions"])

# Health check
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "core-api",
        "version": "1.0.0"
    }

# Startup event
@app.on_event("startup")
async def startup():
    logger.info("starting_core_api_service")
    await init_db()

# Shutdown event
@app.on_event("shutdown")
async def shutdown():
    logger.info("shutting_down_core_api_service")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=13390)
```

---

## ⚙️ **PHASE 1 IMPLEMENTATION STEPS**

### **Day 1-2: Service Structure**

1. **Create directory structure:**
```bash
mkdir -p services/core-api-clean/{routers,models,database,tests}
touch services/core-api-clean/{Dockerfile,requirements.txt,main.py}
```

2. **Copy auth-related routers:**
```bash
# From existing core-api to core-api-clean
cp services/core-api/lib/signup_api.py services/core-api-clean/routers/auth.py
cp services/core-api/lib/users.py services/core-api-clean/routers/users.py
cp services/core-api/lib/rbac_api.py services/core-api-clean/routers/rbac.py
cp services/core-api/lib/token_api.py services/core-api-clean/routers/tokens.py
cp services/core-api/lib/session_api.py services/core-api-clean/routers/sessions.py
```

3. **Update imports in routers:**
```python
# Change from monolith imports:
from lib.database import get_db

# To clean service imports:
from database.connection import get_db
from shared.models.service_interfaces import CoreAPIInterface
```

---

### **Day 3-4: Containerization**

1. **Build Core API container:**
```bash
cd services/core-api-clean
container build -t ninaivalaigal-core-api:latest -f Dockerfile .
```

2. **Test locally:**
```bash
container run -d \
  --name ninaivalaigal-core-api \
  -p 13390:13390 \
  -e DATABASE_URL=postgresql://user:pass@host:5432/db \
  -e REDIS_URL=redis://host:6379 \
  ninaivalaigal-core-api:latest
```

3. **Verify health:**
```bash
curl http://localhost:13390/health
```

---

### **Day 5: CI/CD Pipeline**

**Create:** `.github/workflows/core-api-service.yml`

```yaml
name: Core API Service CI/CD

on:
  push:
    paths:
      - 'services/core-api-clean/**'
  pull_request:
    paths:
      - 'services/core-api-clean/**'

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          cd services/core-api-clean
          pip install -r requirements.txt

      - name: Run tests
        run: |
          cd services/core-api-clean
          pytest tests/

  build:
    runs-on: ubuntu-latest
    needs: test
    steps:
      - uses: actions/checkout@v4

      - name: Build container
        run: |
          cd services/core-api-clean
          docker build -t ninaivalaigal-core-api:${{ github.sha }} .
```

---

## 🎯 **PHASE 1 SUCCESS CRITERIA**

**Must Achieve:**
- [ ] Core API service directory structure created
- [ ] Dockerfile created and tested
- [ ] requirements.txt minimal and functional
- [ ] main.py with 5 core routers
- [ ] Container builds successfully
- [ ] Health check responds
- [ ] CI/CD pipeline created

**Should Achieve:**
- [ ] Unit tests for auth routers
- [ ] Integration tests with database
- [ ] Documentation updated
- [ ] Port conflicts resolved

---

## 📊 **TIMELINE**

### **Week 1 (Days 1-5): Core API Extraction**
- Days 1-2: Directory structure + router copying
- Days 3-4: Containerization + local testing
- Day 5: CI/CD pipeline

### **Week 2 (Days 6-10): Integration & Testing**
- Days 6-7: Memory Service integration
- Days 8-9: GraphOps integration
- Day 10: Gateway routing configuration

### **Week 3-4: See Phase 2 & 3**

---

## 🚀 **STARTING IMPLEMENTATION**

**Status:** Ready to begin Phase 1, Day 1

**Next Action:** Create `services/core-api-clean/` directory structure

---

**Let's begin! This is a multi-week effort, but with US #91 prep, we're starting strong.** 🎯
