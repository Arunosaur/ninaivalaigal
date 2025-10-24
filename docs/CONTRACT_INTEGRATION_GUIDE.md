# Shared Contracts Integration Guide

**Task:** US #79 - Phase 3: Service Integration
**Date:** October 21, 2025
**Status:** In Progress

---

## 🎯 Objective

Refactor all services to import models from `shared.contracts.*` instead of defining duplicated models locally. This ensures:
- Single source of truth for API contracts
- Automatic synchronization across services
- Type safety and validation consistency
- Easier contract evolution

---

## 📦 Package Structure

```
shared/contracts/
├── setup.py                    # Python package configuration
├── __init__.py                 # Package root
├── auth/                       # Authentication contracts
│   └── v1/
│       ├── __init__.py
│       ├── models.py           # Pydantic models
│       ├── auth.proto          # gRPC definitions
│       └── auth_pb2.py         # Generated Python stubs
├── common/                     # Shared/common contracts
│   └── v1/
│       ├── __init__.py
│       └── models.py
├── memory/                     # Memory service contracts
│   └── v1/
│       ├── __init__.py
│       └── models.py
├── business/                   # Business service contracts
│   └── v1/
│       ├── __init__.py
│       └── models.py
├── admin/                      # Admin service contracts
│   └── v1/
│       ├── __init__.py
│       └── models.py
└── graph/                      # Graph service contracts
    └── v1/
        ├── __init__.py
        └── models.py
```

---

## 🔧 Integration Steps

### Step 1: Install Shared Contracts Package (Development Mode)

For local development, install the contracts package in editable mode:

```bash
# From repository root
cd shared/contracts
pip install -e .

# This makes contracts importable as:
# from contracts.auth.v1.models import LoginRequest
# from contracts.common.v1.models import ErrorResponse
```

### Step 2: Update Service Imports

**Before (Local Models):**
```python
# services/core-api/models/api_models.py
from pydantic import BaseModel

class LoginRequest(BaseModel):
    email: str
    password: str

class User(BaseModel):
    id: str
    email: str
    full_name: str
```

**After (Shared Contracts):**
```python
# services/core-api/routers/auth_full.py
from contracts.auth.v1.models import LoginRequest, User, AuthResponse
from contracts.common.v1.models import ErrorResponse

# Use the shared models directly
@router.post("/login", response_model=AuthResponse)
async def login(request: LoginRequest):
    # Implementation uses shared contract models
    pass
```

### Step 3: Remove Duplicate Local Models

```bash
# Identify duplicate models in each service
grep -r "class LoginRequest" services/

# Remove local definitions after verifying shared contracts exist
# Keep only service-specific models that aren't in shared contracts
```

### Step 4: Update Dockerfile

**Add shared/contracts to container build:**

```dockerfile
# services/core-api/Dockerfile (or any service Dockerfile)

FROM python:3.11-slim

WORKDIR /app

# Copy shared contracts FIRST
COPY shared/contracts /app/shared/contracts

# Install shared contracts in editable mode
RUN pip install -e /app/shared/contracts

# Copy service code
COPY services/core-api /app/core-api

# Install service dependencies
RUN pip install -r /app/core-api/requirements.txt

# Run service
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Step 5: Update requirements.txt

**Option A: Development (Editable Install)**
```txt
# services/core-api/requirements.txt
-e ../../shared/contracts
```

**Option B: Production (PyPI or Private Registry)**
```txt
# services/core-api/requirements.txt
ninaivalaigal-contracts==1.0.0
```

---

## 📋 Service-by-Service Integration Plan

### Service 1: Core API (Priority: Highest)

**Models to Replace:**
- ✅ Auth models → `contracts.auth.v1.models`
- ✅ User models → `contracts.auth.v1.models`
- ✅ Organization models → `contracts.auth.v1.models`
- ✅ Team models → `contracts.auth.v1.models`
- ⚠️ Memory models → Keep some local (service-specific logic)

**Files to Update:**
- `routers/auth_full.py`
- `routers/users.py`
- `routers/teams.py`
- `models/api_models.py` (remove duplicates)

**Timeline:** 2-3 days

---

### Service 2: Memory Service (Priority: High)

**Models to Replace:**
- ✅ Memory models → `contracts.memory.v1.models`
- ✅ Context models → `contracts.memory.v1.models`
- ✅ Common models → `contracts.common.v1.models`

**Notes:**
- Rust service - use Cargo.toml integration
- Generate Rust structs from proto files

**Timeline:** 1-2 days

---

### Service 3: Business Service (Priority: Medium)

**Models to Replace:**
- ✅ Billing models → `contracts.business.v1.models`
- ✅ Usage models → `contracts.business.v1.models`
- ✅ Invoice models → `contracts.business.v1.models`

**Timeline:** 1-2 days

---

### Service 4: Admin/Vendor Service (Priority: Medium)

**Models to Replace:**
- ✅ Admin models → `contracts.admin.v1.models`
- ✅ Analytics models → `contracts.admin.v1.models`

**Timeline:** 1 day

---

### Service 5: Graph/AI Service (Priority: Low)

**Models to Replace:**
- ✅ Graph models → `contracts.graph.v1.models`
- ✅ Intelligence models → `contracts.graph.v1.models`

**Timeline:** 1 day

---

## 🧪 Testing Strategy

### 1. Unit Tests

```python
# Test that shared contracts work correctly
import pytest
from contracts.auth.v1.models import LoginRequest, AuthResponse

def test_login_request_validation():
    """Ensure shared contract validation works"""
    request = LoginRequest(email="test@example.com", password="password123")
    assert request.email == "test@example.com"

def test_login_request_invalid_email():
    """Ensure validation fails for invalid data"""
    with pytest.raises(ValidationError):
        LoginRequest(email="invalid", password="pass")
```

### 2. Integration Tests

```bash
# Test that services can import and use shared contracts
python -c "from contracts.auth.v1.models import LoginRequest; print('✅ Import successful')"

# Test that API endpoints still work after refactoring
curl -X POST http://localhost:13390/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "password123"}'
```

### 3. Contract Validation

```bash
# Validate that all services use shared contracts
python ci/validate-contract-usage.py

# Check for duplicate model definitions
grep -r "class LoginRequest" services/ --exclude-dir=venv
```

---

## 🚨 Common Issues & Solutions

### Issue 1: Import Errors

**Problem:**
```python
ModuleNotFoundError: No module named 'contracts'
```

**Solution:**
```bash
# Install shared contracts in editable mode
pip install -e shared/contracts

# Or add to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:${PWD}/shared/contracts"
```

### Issue 2: Circular Imports

**Problem:**
```python
ImportError: cannot import name 'User' from 'contracts.auth.v1.models' (circular import)
```

**Solution:**
- Use `from __future__ import annotations`
- Use string type hints: `user: "User"`
- Restructure imports to avoid cycles

### Issue 3: Pydantic Version Conflicts

**Problem:**
```
pydantic.errors.PydanticUserError: Pydantic v2 required
```

**Solution:**
- Ensure all services use Pydantic v2+
- Update requirements.txt: `pydantic>=2.0.0`

### Issue 4: Docker Build Failures

**Problem:**
```
ERROR: Could not find a version that satisfies the requirement ninaivalaigal-contracts
```

**Solution:**
```dockerfile
# Use editable install in Dockerfile
COPY shared/contracts /app/shared/contracts
RUN pip install -e /app/shared/contracts
```

---

## 📊 Progress Tracking

### Core API Integration

- [ ] Install shared contracts package
- [ ] Update auth router imports
- [ ] Update users router imports
- [ ] Update teams router imports
- [ ] Remove duplicate models from api_models.py
- [ ] Update Dockerfile
- [ ] Test all endpoints
- [ ] Validate OpenAPI spec generation

### Memory Service Integration

- [ ] Add Cargo.toml dependencies
- [ ] Generate Rust structs from proto
- [ ] Update service imports
- [ ] Test gRPC endpoints
- [ ] Validate contract compliance

### All Services

- [ ] Core API
- [ ] Memory Service (Rust)
- [ ] Business Service
- [ ] Admin/Vendor Service
- [ ] Graph/AI Service

---

## ✅ Success Criteria

1. **Zero Duplicate Models:** No models defined in both services and shared/contracts
2. **All Imports from Contracts:** All services import from `contracts.*`
3. **Tests Pass:** All unit and integration tests pass
4. **OpenAPI Sync:** Generated OpenAPI matches stored contracts
5. **CI Validates:** GitHub Actions validates contract usage

---

## 🚀 Next Steps After Integration

1. **Publish Package:** Deploy to private PyPI or artifact registry
2. **Version Management:** Implement semantic versioning for contracts
3. **Breaking Change Process:** Document how to handle breaking changes
4. **Service Decomposition:** Proceed with US #88 (Core API decomposition)
5. **API Gateway:** Implement US #83 (Traefik gateway with contracts)

---

## 📚 References

- **SPEC-100:** specs/100-api-container-modularization/README.md
- **Task #79:** docs/TAIGA_TASK_TRACKING_OCT20.md
- **Contracts README:** shared/contracts/README.md
- **Integration Examples:** shared/contracts/INTEGRATION_EXAMPLE.md

---

**Last Updated:** October 21, 2025
**Phase 3 Status:** 0% (starting Core API integration)
**Timeline:** 7-10 days for all services
