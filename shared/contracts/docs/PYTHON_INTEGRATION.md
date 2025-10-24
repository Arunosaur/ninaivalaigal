# Python Service Integration

**Purpose:** FastAPI + Pydantic integration examples
**Status:** Production Ready

---

## Quick Start

```python
from fastapi import FastAPI
from ninaivalaigal_contracts.my_service.v1 import CreateItemRequest, ItemResponse

app = FastAPI()

@app.post("/items", response_model=ItemResponse)
async def create(request: CreateItemRequest):
    return ItemResponse(**process(request))
```

---

## Complete Example

See [SERVICE_INTEGRATION.md](./SERVICE_INTEGRATION.md) for full working service example.

---

## Type Mappings

| Python Type | Pydantic Type | Validation |
|-------------|---------------|------------|
| str | str | min_length, max_length |
| int | int | ge, le |
| float | float | ge, le |
| bool | bool | - |
| datetime | datetime | - |
| UUID | UUID | - |
| Email | EmailStr | Valid email format |
| URL | HttpUrl | Valid HTTP/HTTPS URL |

---

## Validation Examples

```python
from pydantic import BaseModel, Field, EmailStr, HttpUrl

class User(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    email: EmailStr
    age: int = Field(..., ge=0, le=150)
    website: Optional[HttpUrl] = None
```

---

## References
- [Pydantic Docs](https://docs.pydantic.dev/)
- [FastAPI Docs](https://fastapi.tiangolo.com/)
