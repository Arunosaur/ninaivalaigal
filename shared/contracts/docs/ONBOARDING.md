# Team Onboarding Guide

**Purpose:** Quick start for new developers
**Audience:** New team members
**Time:** 30 minutes

---

## Overview

The Shared Contracts Layer is the single source of truth for API specifications across all services (Python and Rust). It ensures type safety, contract compliance, and seamless service communication.

---

## Key Concepts

### 1. Runtime-Agnostic Contracts
Contracts are defined once and used by multiple languages:
- **Python services:** Use Pydantic models
- **Rust services:** Use Protobuf (future)
- **TypeScript clients:** Generated from OpenAPI

### 2. Version-Based Organization
```
shared/contracts/
└── my-service/
    ├── v1/          # Version 1 (stable)
    └── v2/          # Version 2 (breaking changes)
```

### 3. Contract Types
- **REST APIs:** Pydantic models → OpenAPI schema
- **gRPC:** Protobuf definitions

---

## Your First Contract (15 min)

### Step 1: Setup (3 min)
```bash
cd shared/contracts/
pip install -e .
```

### Step 2: Create Contract (5 min)
```python
# shared/contracts/demo/v1/contracts.py
from pydantic import BaseModel

class HelloRequest(BaseModel):
    name: str

class HelloResponse(BaseModel):
    message: str
```

### Step 3: Use in Service (5 min)
```python
# services/demo-service/api.py
from fastapi import FastAPI
from ninaivalaigal_contracts.demo.v1 import HelloRequest, HelloResponse

app = FastAPI()

@app.post("/hello", response_model=HelloResponse)
async def hello(request: HelloRequest):
    return HelloResponse(message=f"Hello, {request.name}!")
```

### Step 4: Test (2 min)
```bash
curl -X POST http://localhost:8000/hello \
  -H "Content-Type: application/json" \
  -d '{"name":"World"}'

# Response: {"message":"Hello, World!"}
```

---

## Common Tasks

### Import a Contract
```python
from ninaivalaigal_contracts.memory.v1 import CreateMemoryRequest
```

### Create New Contract
See [DEVELOPER_GUIDE.md](./DEVELOPER_GUIDE.md)

### Update Existing Contract
See [VERSIONING.md](./VERSIONING.md)

### Fix Import Error
```bash
pip install --force-reinstall -e shared/contracts/
```

---

## Workflow

### Making Changes
1. **Check:** Is this a breaking change?
2. **If NO:** Add to existing version (v1)
3. **If YES:** Create new version (v2)
4. **Test:** Run `pytest shared/contracts/tests/`
5. **Commit:** Submit PR with contract changes

### Using Contracts
1. **Import:** `from ninaivalaigal_contracts.X.v1 import Y`
2. **Use:** Apply as FastAPI `response_model` or request body
3. **Validate:** FastAPI auto-validates against contract

---

## Next Steps

**Read these guides:**
1. ✅ **This guide** (you're here!)
2. [DEVELOPER_GUIDE.md](./DEVELOPER_GUIDE.md) - Creating contracts
3. [SERVICE_INTEGRATION.md](./SERVICE_INTEGRATION.md) - Using in services
4. [BEST_PRACTICES.md](./BEST_PRACTICES.md) - Design patterns

**Try building:**
- Create a simple contract for a new endpoint
- Integrate it into an existing service
- Write a test for your contract

**Get help:**
- Check [TROUBLESHOOTING.md](./TROUBLESHOOTING.md)
- Ask in #backend-dev Slack channel
- Review existing contracts in `shared/contracts/memory/v1/`

---

## References

- Main README: [../README.md](../README.md)
- All documentation: [./](.)
- Example services: [../examples/](../examples/)

**Welcome to the team! 🚀**
