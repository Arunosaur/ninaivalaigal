# Service Integration Example

**How to integrate shared contracts in your service**

---

## Example: Core API Service

### Before (Scattered Models)

```python
# services/core-api/models.py
from pydantic import BaseModel

class User(BaseModel):
    id: str
    email: str
    full_name: str
    # ... repeated in every service

class PageRequest(BaseModel):
    page: int = 1
    page_size: int = 20
    # ... repeated everywhere
```

### After (Centralized Contracts)

```python
# services/core-api/routers/auth.py
from fastapi import APIRouter, HTTPException
from shared.contracts.auth.v1.models import (
    User,
    LoginRequest,
    RegisterRequest,
    AuthResponse,
)
from shared.contracts.common.v1.models import Error

router = APIRouter()

@router.post("/auth/login", response_model=AuthResponse)
async def login(request: LoginRequest):
    """
    Login endpoint using shared contracts.

    - Type-safe request: LoginRequest validates email format
    - Type-safe response: AuthResponse guarantees structure
    - IDE autocomplete works out of the box
    """
    user = await authenticate_user(request.email, request.password)

    if not user:
        raise HTTPException(
            status_code=401,
            detail=Error(
                code="UNAUTHORIZED",
                message="Invalid credentials"
            ).dict()
        )

    return AuthResponse(
        access_token=create_token(user),
        refresh_token=create_refresh_token(user),
        expires_in=3600,
        token_type="Bearer",
        user=User(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            roles=user.roles,
            is_active=user.is_active,
            created_at=user.created_at.isoformat()
        )
    )
```

---

## Benefits Demonstrated

### 1. Type Safety
```python
# ✅ IDE catches this immediately
login_req = LoginRequest(
    email="not-an-email",  # ❌ Pydantic validation error
    password="short"       # ❌ Too short (min 8 chars)  # pragma: allowlist secret
)
```

### 2. API Documentation
```python
# FastAPI auto-generates OpenAPI spec from contracts
# Visit /docs to see beautiful, accurate documentation
```

### 3. Consistency
```python
# Same User model used everywhere
from shared.contracts.auth.v1.models import User

# In core-api
def get_user() -> User: ...

# In business-service
def charge_user(user: User): ...

# In admin-service
def suspend_user(user: User): ...

# All services speak the same language!
```

### 4. Validation
```python
from shared.contracts.common.v1.models import PageRequest

@router.get("/memories")
async def list_memories(page: PageRequest):
    # ✅ page.page is guaranteed to be >= 1
    # ✅ page.page_size is guaranteed to be 1-100
    # ✅ No manual validation needed!
    return get_memories(page.page, page.page_size)
```

---

## Integration Checklist

### For Existing Service

- [ ] Add contracts to PYTHONPATH or use relative imports
- [ ] Replace local models with contract imports
- [ ] Update API route signatures
- [ ] Test all endpoints still work
- [ ] Update tests to use contract models
- [ ] Remove old duplicate models
- [ ] Deploy and verify

### For New Service

- [ ] Import contracts from day 1
- [ ] No need to define your own models
- [ ] Just use what's in contracts
- [ ] Add new models to contracts if needed
- [ ] Follow versioning strategy (v1, v2)

---

## Real-World Example: Memory Service

```python
# services/core-api/routers/memory_api.py
from typing import List
from fastapi import APIRouter, Depends
from shared.contracts.memory.v1.models import (
    Memory,
    CreateMemoryRequest,
    UpdateMemoryRequest,
    MemoryList,
)
from shared.contracts.common.v1.models import PageRequest
from shared.contracts.auth.v1.models import User
from .auth import get_current_user

router = APIRouter()

@router.post("/memories", response_model=Memory)
async def create_memory(
    request: CreateMemoryRequest,
    user: User = Depends(get_current_user)
):
    """Create a new memory using shared contracts."""
    return await memory_service.create(
        user_id=user.id,
        content=request.content,
        metadata=request.metadata,
        tags=request.tags
    )

@router.get("/memories", response_model=MemoryList)
async def list_memories(
    page: PageRequest = Depends(),
    user: User = Depends(get_current_user)
):
    """List user's memories with pagination."""
    memories, total = await memory_service.list_user_memories(
        user_id=user.id,
        page=page.page,
        page_size=page.page_size
    )

    return MemoryList(
        memories=memories,
        total=total,
        page=page.page,
        page_size=page.page_size
    )

@router.patch("/memories/{memory_id}", response_model=Memory)
async def update_memory(
    memory_id: str,
    request: UpdateMemoryRequest,
    user: User = Depends(get_current_user)
):
    """Update a memory."""
    return await memory_service.update(
        memory_id=memory_id,
        user_id=user.id,
        content=request.content,
        metadata=request.metadata,
        tags=request.tags
    )
```

---

## Testing with Contracts

```python
# tests/test_memory_api.py
import pytest
from shared.contracts.memory.v1.models import CreateMemoryRequest, Memory

def test_create_memory():
    """Test memory creation with contract models."""
    # Arrange
    request = CreateMemoryRequest(
        user_id="user-123",
        content="Test memory",
        tags=["test", "demo"]
    )

    # Act
    response = client.post("/memories", json=request.dict())

    # Assert
    assert response.status_code == 200
    memory = Memory(**response.json())
    assert memory.content == "Test memory"
    assert "test" in memory.tags
```

---

## Success Metrics

After integration, you should see:

✅ **Reduced Code:** No duplicate model definitions
✅ **Type Safety:** IDE catches errors before runtime
✅ **Better Docs:** Auto-generated OpenAPI specs
✅ **Consistency:** All services use same models
✅ **Easier Refactoring:** Change once, update everywhere

---

## Need Help?

- Read: `/shared/contracts/USAGE_GUIDE.md`
- Check: `/shared/contracts/README_CONTRACTS.md`
- Ask: Post in project discussions
