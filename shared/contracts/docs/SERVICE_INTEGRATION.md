# Service Integration Guide

**Purpose:** How to integrate contracts into a new service
**Audience:** Developers adding new microservices
**Prerequisites:** Contracts already created

---

## Quick Start

### 1. Install Contracts Package

```bash
cd your-service/
pip install -e ../shared/contracts
```

### 2. Import Contracts

```python
from ninaivalaigal_contracts.my_service.v1 import (
    CreateItemRequest,
    ItemResponse,
)
```

### 3. Use in FastAPI

```python
from fastapi import FastAPI, APIRouter
from ninaivalaigal_contracts.my_service.v1 import CreateItemRequest, ItemResponse

app = FastAPI()
router = APIRouter(prefix="/api/v1")

@router.post("/items", response_model=ItemResponse)
async def create_item(request: CreateItemRequest):
    return ItemResponse(**your_logic(request))

app.include_router(router)
```

---

## Complete Integration Example

### Directory Structure

```
services/
└── my-service/
    ├── api.py              # FastAPI routes
    ├── business_logic.py   # Business layer
    ├── database.py         # DB layer
    ├── requirements.txt
    └── Dockerfile
```

### requirements.txt

```txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
ninaivalaigal-contracts @ file:///app/shared/contracts
pydantic==2.4.2
```

### api.py - Full Example

```python
"""My Service API Routes"""
from fastapi import FastAPI, APIRouter, HTTPException, status, Depends
from ninaivalaigal_contracts.my_service.v1 import (
    CreateItemRequest,
    UpdateItemRequest,
    ItemResponse,
    ItemListResponse,
    ErrorResponse,
    HealthCheckResponse,
)
from ninaivalaigal_contracts.common.v1 import PaginationParams
from typing import List
from datetime import datetime
import uuid

app = FastAPI(
    title="My Service",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

router = APIRouter(prefix="/api/v1/items", tags=["items"])

# CREATE
@router.post("/", response_model=ItemResponse, status_code=status.HTTP_201_CREATED)
async def create_item(request: CreateItemRequest):
    """Create a new item"""
    # Business logic
    item_data = {
        "id": uuid.uuid4(),
        "name": request.name,
        "description": request.description,
        "tags": request.tags,
        "created_at": datetime.utcnow(),
        "updated_at": None,
    }
    # Save to DB
    saved_item = await save_to_db(item_data)
    return ItemResponse(**saved_item)

# READ
@router.get("/{item_id}", response_model=ItemResponse)
async def get_item(item_id: str):
    """Get item by ID"""
    item = await fetch_from_db(item_id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found"
        )
    return ItemResponse(**item)

# UPDATE
@router.put("/{item_id}", response_model=ItemResponse)
async def update_item(item_id: str, request: UpdateItemRequest):
    """Update an item"""
    updates = request.dict(exclude_unset=True)
    updates["updated_at"] = datetime.utcnow()

    updated_item = await update_in_db(item_id, updates)
    if not updated_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found"
        )
    return ItemResponse(**updated_item)

# DELETE
@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_item(item_id: str):
    """Delete an item"""
    deleted = await delete_from_db(item_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found"
        )
    return None

# LIST
@router.get("/", response_model=ItemListResponse)
async def list_items(
    page: int = 1,
    page_size: int = 20,
):
    """List all items"""
    items, total = await fetch_many_from_db(page, page_size)
    return ItemListResponse(
        items=[ItemResponse(**item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
    )

# HEALTH
@router.get("/health", response_model=HealthCheckResponse, tags=["health"])
async def health_check():
    """Service health check"""
    return HealthCheckResponse(
        status="healthy",
        version="1.0.0",
        timestamp=datetime.utcnow(),
    )

app.include_router(router)

# Error handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    return ErrorResponse(
        error=str(exc),
        code="INTERNAL_ERROR",
        trace_id=request.headers.get("X-Trace-ID"),
    )
```

---

## CI/CD Integration

### .github/workflows/validate.yml

```yaml
name: Validate Contracts

on: [push, pull_request]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Install contracts
        run: |
          cd shared/contracts
          pip install -e .

      - name: Validate service imports
        run: |
          python -c "from ninaivalaigal_contracts.my_service.v1 import *"

      - name: Run contract tests
        run: pytest shared/contracts/tests/
```

---

## Troubleshooting

### Issue: Import Error
**Solution:** `pip install -e ../shared/contracts`

### Issue: Validation Error
**Solution:** Check request matches contract schema exactly

### Issue: Version Mismatch
**Solution:** Reinstall contracts: `pip install --force-reinstall -e ../shared/contracts`

---

## References

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [DEVELOPER_GUIDE.md](./DEVELOPER_GUIDE.md)
- [PYTHON_INTEGRATION.md](./PYTHON_INTEGRATION.md)
