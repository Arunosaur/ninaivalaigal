# Developer Guide: Creating Service Contracts

**Purpose:** Step-by-step guide for creating new service contracts
**Audience:** Backend developers adding new services or endpoints
**Prerequisites:** Basic understanding of Python/Pydantic, REST APIs

---

## Overview

The Shared Contracts Layer provides runtime-agnostic API specifications that enable Python and Rust services to communicate seamlessly. Contracts are defined using:

- **Pydantic models** for Python services (FastAPI integration)
- **OpenAPI 3.0** schemas (auto-generated from Pydantic)
- **Protobuf** definitions for gRPC services (Rust/Go)

This guide shows you how to create a new contract from scratch.

---

## Step-by-Step Guide

### Step 1: Choose Contract Type

**REST API (most common):**
- Use Pydantic models
- Auto-generates OpenAPI schema
- Best for CRUD operations, HTTP endpoints

**gRPC (high performance):**
- Use Protobuf definitions
- Better for service-to-service calls
- Lower latency, binary protocol

**For this guide, we'll create a REST API contract.**

---

### Step 2: Create Service Directory

```bash
cd shared/contracts/
mkdir -p my-service/v1
touch my-service/__init__.py
touch my-service/v1/__init__.py
```

**Directory structure:**
```
shared/contracts/
└── my-service/
    ├── __init__.py
    └── v1/
        ├── __init__.py
        └── contracts.py      # Your contracts here
```

---

### Step 3: Define Pydantic Models

Create `my-service/v1/contracts.py`:

```python
"""
My Service API Contracts v1
"""
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import datetime
from uuid import UUID

# Request Models
class CreateItemRequest(BaseModel):
    """Request to create a new item"""
    name: str = Field(..., min_length=1, max_length=255, description="Item name")
    description: Optional[str] = Field(None, max_length=1000, description="Item description")
    tags: List[str] = Field(default_factory=list, description="Item tags")

    class Config:
        schema_extra = {
            "example": {
                "name": "Example Item",
                "description": "This is an example item",
                "tags": ["example", "demo"]
            }
        }

class UpdateItemRequest(BaseModel):
    """Request to update an existing item"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    tags: Optional[List[str]] = None

# Response Models
class ItemResponse(BaseModel):
    """Response containing item details"""
    id: UUID = Field(..., description="Unique item identifier")
    name: str = Field(..., description="Item name")
    description: Optional[str] = Field(None, description="Item description")
    tags: List[str] = Field(default_factory=list, description="Item tags")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")

    class Config:
        schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "name": "Example Item",
                "description": "This is an example item",
                "tags": ["example", "demo"],
                "created_at": "2025-10-22T20:00:00Z",
                "updated_at": "2025-10-22T21:00:00Z"
            }
        }

class ItemListResponse(BaseModel):
    """Response containing list of items"""
    items: List[ItemResponse] = Field(..., description="List of items")
    total: int = Field(..., description="Total count")
    page: int = Field(..., description="Current page")
    page_size: int = Field(..., description="Items per page")

# Common Models
class ErrorResponse(BaseModel):
    """Standard error response"""
    error: str = Field(..., description="Error message")
    code: str = Field(..., description="Error code")
    details: Optional[dict] = Field(None, description="Additional error details")
    trace_id: Optional[str] = Field(None, description="Request trace ID for debugging")

class HealthCheckResponse(BaseModel):
    """Health check response"""
    status: str = Field(..., description="Service status (healthy/unhealthy)")
    version: str = Field(..., description="Service version")
    timestamp: datetime = Field(..., description="Check timestamp")
```

---

### Step 4: Export Contracts

Update `my-service/v1/__init__.py`:

```python
"""My Service v1 Contracts"""
from .contracts import (
    CreateItemRequest,
    UpdateItemRequest,
    ItemResponse,
    ItemListResponse,
    ErrorResponse,
    HealthCheckResponse,
)

__all__ = [
    "CreateItemRequest",
    "UpdateItemRequest",
    "ItemResponse",
    "ItemListResponse",
    "ErrorResponse",
    "HealthCheckResponse",
]
```

Update `my-service/__init__.py`:

```python
"""My Service Contracts"""
from . import v1

__all__ = ["v1"]
```

---

### Step 5: Install as Package

Update `shared/contracts/setup.py` to include your service:

```python
# Add to packages list
packages=[
    "common",
    "auth",
    "memory",
    "graph",
    "business",
    "admin",
    "my_service",  # Add this
    "my_service.v1",  # And this
],
```

Install in development mode:

```bash
cd shared/contracts/
pip install -e .
```

---

### Step 6: Use in FastAPI Service

```python
# In your service (e.g., services/my-service/api.py)
from fastapi import APIRouter, HTTPException, status
from ninaivalaigal_contracts.my_service.v1 import (
    CreateItemRequest,
    UpdateItemRequest,
    ItemResponse,
    ItemListResponse,
    ErrorResponse,
)

router = APIRouter(prefix="/api/v1/items", tags=["items"])

@router.post("/", response_model=ItemResponse, status_code=status.HTTP_201_CREATED)
async def create_item(request: CreateItemRequest):
    """Create a new item"""
    # Your business logic here
    item = {
        "id": generate_uuid(),
        "name": request.name,
        "description": request.description,
        "tags": request.tags,
        "created_at": datetime.utcnow(),
        "updated_at": None,
    }
    return ItemResponse(**item)

@router.get("/{item_id}", response_model=ItemResponse)
async def get_item(item_id: str):
    """Get item by ID"""
    # Your business logic here
    item = fetch_item_from_db(item_id)
    if not item:
        raise HTTPException(404, "Item not found")
    return ItemResponse(**item)

@router.put("/{item_id}", response_model=ItemResponse)
async def update_item(item_id: str, request: UpdateItemRequest):
    """Update an item"""
    # Your business logic here
    updated_item = update_item_in_db(item_id, request.dict(exclude_unset=True))
    return ItemResponse(**updated_item)

@router.get("/", response_model=ItemListResponse)
async def list_items(page: int = 1, page_size: int = 20):
    """List all items"""
    items, total = fetch_items_from_db(page, page_size)
    return ItemListResponse(
        items=[ItemResponse(**item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
    )
```

---

## Common Patterns

### Pattern 1: Pagination

```python
class PaginationParams(BaseModel):
    page: int = Field(1, ge=1, description="Page number (1-indexed)")
    page_size: int = Field(20, ge=1, le=100, description="Items per page")

class PaginatedResponse(BaseModel):
    items: List[Any]  # Replace with your model
    total: int
    page: int
    page_size: int
    has_next: bool
    has_prev: bool
```

### Pattern 2: Filtering

```python
class FilterParams(BaseModel):
    status: Optional[str] = Field(None, description="Filter by status")
    tags: Optional[List[str]] = Field(None, description="Filter by tags")
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
```

### Pattern 3: Sorting

```python
from enum import Enum

class SortOrder(str, Enum):
    ASC = "asc"
    DESC = "desc"

class SortParams(BaseModel):
    sort_by: str = Field("created_at", description="Field to sort by")
    order: SortOrder = Field(SortOrder.DESC, description="Sort order")
```

---

## Field Validation Best Practices

### String Fields
```python
name: str = Field(..., min_length=1, max_length=255)
email: EmailStr = Field(..., description="Valid email address")
url: HttpUrl = Field(..., description="Valid HTTP/HTTPS URL")
```

### Numeric Fields
```python
age: int = Field(..., ge=0, le=150, description="Age in years")
price: float = Field(..., ge=0, description="Price (must be positive)")
```

### Optional vs Required
```python
required_field: str = Field(..., description="Required field")
optional_field: Optional[str] = Field(None, description="Optional field")
optional_with_default: str = Field("default", description="Optional with default")
```

### Lists and Nested Models
```python
tags: List[str] = Field(default_factory=list, description="List of tags")
metadata: dict = Field(default_factory=dict, description="Arbitrary metadata")
address: AddressModel = Field(..., description="Nested address model")
addresses: List[AddressModel] = Field(default_factory=list)
```

---

## Troubleshooting

### Issue 1: Import Error

**Symptom:** `ModuleNotFoundError: No module named 'ninaivalaigal_contracts'`

**Cause:** Package not installed

**Solution:**
```bash
cd shared/contracts/
pip install -e .
```

### Issue 2: Validation Error

**Symptom:** `ValidationError: field required`

**Cause:** Required field not provided in request

**Solution:**
- Mark field as optional: `Optional[str] = None`
- Provide default value: `str = Field("default")`
- Ensure client sends all required fields

### Issue 3: Circular Import

**Symptom:** `ImportError: cannot import name '...' from partially initialized module`

**Cause:** Circular dependency between contract files

**Solution:**
- Use `from __future__ import annotations` at top of file
- Use string type hints: `items: List["ItemResponse"]`
- Restructure contracts to avoid circular dependencies

---

## References

- [Pydantic Documentation](https://docs.pydantic.dev/)
- [FastAPI Request Body](https://fastapi.tiangolo.com/tutorial/body/)
- [OpenAPI 3.0 Specification](https://swagger.io/specification/)
- **Related Docs:**
  - [VERSIONING.md](./VERSIONING.md) - Version management
  - [SERVICE_INTEGRATION.md](./SERVICE_INTEGRATION.md) - Integrating contracts
  - [PYTHON_INTEGRATION.md](./PYTHON_INTEGRATION.md) - Python examples
