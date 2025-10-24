# Contract Versioning Workflow

**Purpose:** How to version contracts and manage breaking changes
**Audience:** Developers modifying existing contracts
**Prerequisites:** Understanding of semantic versioning

---

## Overview

Contract versioning ensures backward compatibility while allowing evolution. We use **path-based major versioning** (v1, v2, v3) where each major version is immutable once deployed.

**Key Principle:** Old clients must continue working when new versions are deployed.

---

## Version Structure

```
shared/contracts/
└── my-service/
    ├── v1/          # Version 1 (immutable after production)
    │   └── contracts.py
    ├── v2/          # Version 2 (new major version)
    │   └── contracts.py
    └── v3/          # Version 3 (future)
        └── contracts.py
```

---

## When to Increment Versions

### **Keep Same Version (v1)** ✅

**Backward-compatible changes:**
- ✅ Adding new optional fields
- ✅ Adding new endpoints
- ✅ Adding new enum values (append only)
- ✅ Relaxing validation (e.g., max_length 100 → 200)
- ✅ Adding new response fields
- ✅ Making required field optional

**Example:**
```python
# v1 - Original
class UserResponse(BaseModel):
    id: UUID
    name: str
    email: EmailStr

# v1 - After backward-compatible change ✅
class UserResponse(BaseModel):
    id: UUID
    name: str
    email: EmailStr
    phone: Optional[str] = None  # New optional field - OK!
    created_at: Optional[datetime] = None  # New optional field - OK!
```

---

### **Create New Version (v2)** ⚠️

**Breaking changes:**
- ❌ Removing fields
- ❌ Renaming fields
- ❌ Changing field types
- ❌ Making optional field required
- ❌ Changing validation rules (stricter)
- ❌ Removing endpoints
- ❌ Changing URL paths

**Example:**
```python
# v1 - Original
class UserResponse(BaseModel):
    id: UUID
    name: str
    email: EmailStr

# v2 - Breaking change ❌
class UserResponse(BaseModel):
    id: UUID
    full_name: str  # Renamed field - BREAKING!
    email: EmailStr
    age: int  # New required field - BREAKING!
```

---

## Semantic Versioning Rules

### Major Version (v1 → v2)

**When:** Breaking changes required

**Process:**
1. Create new version directory: `mkdir my-service/v2`
2. Copy v1 contracts: `cp -r my-service/v1/* my-service/v2/`
3. Make breaking changes in v2
4. Keep v1 unchanged (frozen)
5. Deploy both versions simultaneously
6. Migrate clients gradually
7. Deprecate v1 after migration period

**Example:**
```bash
# Create v2
mkdir -p my-service/v2
cp my-service/v1/contracts.py my-service/v2/contracts.py

# Edit v2/contracts.py with breaking changes
# v1 remains unchanged and operational
```

---

### Minor Changes (v1.1, v1.2)

**Not used in our system.** We only use major versions (v1, v2, v3).

**Rationale:**
- Simpler for clients (no version negotiation)
- Clear upgrade path
- Easier to deprecate old versions

---

## Version Migration Workflow

### Step 1: Analyze Change Impact

**Question checklist:**
- [ ] Will existing clients break? → If YES, create new version
- [ ] Are fields removed/renamed? → If YES, create new version
- [ ] Are types changed? → If YES, create new version
- [ ] Is validation stricter? → If YES, create new version
- [ ] Is it additive only? → If YES, keep same version

---

### Step 2: Create New Version

```bash
cd shared/contracts/
mkdir -p my-service/v2
touch my-service/v2/__init__.py
cp my-service/v1/contracts.py my-service/v2/contracts.py
```

Edit `my-service/v2/contracts.py` with your changes.

---

### Step 3: Update Exports

**my-service/v2/__init__.py:**
```python
"""My Service v2 Contracts"""
from .contracts import (
    CreateItemRequest,
    UpdateItemRequest,
    ItemResponse,  # Modified fields
    ItemListResponse,
)

__all__ = [
    "CreateItemRequest",
    "UpdateItemRequest",
    "ItemResponse",
    "ItemListResponse",
]
```

**my-service/__init__.py:**
```python
"""My Service Contracts"""
from . import v1, v2  # Export both versions

__all__ = ["v1", "v2"]
```

---

### Step 4: Update setup.py

```python
packages=[
    "common",
    "my_service",
    "my_service.v1",
    "my_service.v2",  # Add v2
],
```

---

### Step 5: Deploy Both Versions

**FastAPI service supports both:**
```python
from ninaivalaigal_contracts.my_service import v1, v2

# v1 endpoints
v1_router = APIRouter(prefix="/api/v1/items", tags=["items-v1"])

@v1_router.get("/", response_model=v1.ItemListResponse)
async def list_items_v1():
    # v1 implementation
    pass

# v2 endpoints
v2_router = APIRouter(prefix="/api/v2/items", tags=["items-v2"])

@v2_router.get("/", response_model=v2.ItemListResponse)
async def list_items_v2():
    # v2 implementation with new fields
    pass

# Register both
app.include_router(v1_router)
app.include_router(v2_router)
```

---

### Step 6: Communicate Changes

**Create migration guide:**
```markdown
# Migration Guide: v1 → v2

## Breaking Changes
- `name` field renamed to `full_name`
- `age` field now required

## Migration Steps
1. Update client code to use `/api/v2/` endpoints
2. Rename `name` to `full_name` in all requests/responses
3. Provide `age` field in all requests
4. Test thoroughly
5. Deploy client changes
6. Remove v1 usage

## Timeline
- **Oct 22:** v2 deployed
- **Nov 22:** v1 deprecated (1 month notice)
- **Dec 22:** v1 removed (2 months total)
```

---

### Step 7: Deprecate Old Version

**After migration period (30-90 days):**

1. Add deprecation warning to v1 endpoints:
```python
@v1_router.get("/", deprecated=True)
async def list_items_v1():
    """
    ⚠️ DEPRECATED: Use /api/v2/items instead
    This endpoint will be removed on Dec 22, 2025
    """
    pass
```

2. Monitor v1 usage (should be zero)

3. Remove v1 code:
```bash
rm -rf my-service/v1/
# Update __init__.py to remove v1 import
```

---

## Version Compatibility Matrix

| Change Type | Example | v1 → v1 | v1 → v2 |
|-------------|---------|---------|---------|
| Add optional field | `phone: Optional[str]` | ✅ | ❌ |
| Add required field | `age: int` | ❌ | ✅ |
| Remove field | Delete `email` | ❌ | ✅ |
| Rename field | `name` → `full_name` | ❌ | ✅ |
| Change type | `str` → `int` | ❌ | ✅ |
| Add endpoint | New `/items/bulk` | ✅ | ❌ |
| Remove endpoint | Delete `/items/bulk` | ❌ | ✅ |
| Relax validation | `max_length=100` → `200` | ✅ | ❌ |
| Strict validation | `max_length=200` → `100` | ❌ | ✅ |

---

## Protobuf Versioning (gRPC)

**Same principle, different syntax:**

```protobuf
// v1/graphops.proto
syntax = "proto3";

package ninaivalaigal.graphops.v1;

service GraphOpsService {
  rpc ExecuteQuery(CypherRequest) returns (CypherResponse);
}

message CypherRequest {
  string query = 1;
  map<string, string> parameters = 2;
}
```

**Breaking changes → create v2:**
```protobuf
// v2/graphops.proto
syntax = "proto3";

package ninaivalaigal.graphops.v2;  // New package

service GraphOpsService {
  rpc ExecuteQuery(CypherRequest) returns (CypherResponse);
}

message CypherRequest {
  string query_text = 1;  // Renamed field
  map<string, string> params = 2;  // Renamed field
  int32 timeout_ms = 3;  // New required field
}
```

---

## Best Practices

### DO ✅
- Keep v1 frozen after production deployment
- Create v2 for breaking changes
- Support multiple versions simultaneously (transition period)
- Document migration path
- Give 30+ days notice before deprecation
- Monitor version usage metrics

### DON'T ❌
- Don't modify v1 contracts after production (except additive changes)
- Don't skip versions (v1 → v3)
- Don't remove old versions immediately
- Don't make breaking changes without new version
- Don't surprise clients with breaking changes

---

## References

- [Semantic Versioning](https://semver.org/)
- [API Versioning Best Practices](https://stripe.com/blog/api-versioning)
- **Related Docs:**
  - [BREAKING_CHANGES.md](./BREAKING_CHANGES.md) - Breaking change policy
  - [DEPRECATION.md](./DEPRECATION.md) - Deprecation workflow
  - [COMPATIBILITY.md](./COMPATIBILITY.md) - Compatibility rules
