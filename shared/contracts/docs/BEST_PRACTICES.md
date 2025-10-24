# Contract Design Best Practices

**Purpose:** Design principles and patterns
**Audience:** Developers creating contracts

---

## Design Principles

### 1. Make Contracts Explicit ✅
```python
# ✅ GOOD: Explicit, self-documenting
class CreateUserRequest(BaseModel):
    email: EmailStr = Field(..., description="User email address")
    full_name: str = Field(..., min_length=1, max_length=255, description="Full name")
    age: int = Field(..., ge=0, le=150, description="Age in years")

# ❌ BAD: Vague, no validation
class CreateUserRequest(BaseModel):
    email: str
    name: str
    age: int
```

### 2. Use Field Descriptions ✅
```python
# ✅ GOOD
id: UUID = Field(..., description="Unique user identifier")

# ❌ BAD
id: UUID
```

### 3. Validate Input ✅
```python
# ✅ GOOD
age: int = Field(..., ge=0, le=150)
email: EmailStr  # Auto-validates email format

# ❌ BAD
age: int  # Could be negative
email: str  # Could be invalid
```

---

## Naming Conventions

### Models
```python
# ✅ GOOD
class CreateMemoryRequest(BaseModel): pass
class MemoryResponse(BaseModel): pass
class UpdateUserRequest(BaseModel): pass

# ❌ BAD
class MemoryCreate(BaseModel): pass  # Inconsistent
class Mem(BaseModel): pass  # Too short
class memory_response(BaseModel): pass  # Wrong case
```

### Fields
```python
# ✅ GOOD: snake_case
user_id: UUID
created_at: datetime
full_name: str

# ❌ BAD
userId: UUID  # camelCase
CreatedAt: datetime  # PascalCase
```

---

## Common Patterns

### Pattern 1: Base Response
```python
class BaseResponse(BaseModel):
    """Base class for all responses"""
    trace_id: Optional[str] = Field(None, description="Request trace ID")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class UserResponse(BaseResponse):
    id: UUID
    name: str
    email: EmailStr
```

### Pattern 2: Pagination
```python
class PaginationParams(BaseModel):
    page: int = Field(1, ge=1, description="Page number")
    page_size: int = Field(20, ge=1, le=100, description="Items per page")

class PaginatedResponse(BaseModel):
    items: List[Any]
    total: int
    page: int
    page_size: int
    has_next: bool
```

### Pattern 3: Error Response
```python
class ErrorResponse(BaseModel):
    error: str = Field(..., description="Error message")
    code: str = Field(..., description="Error code")
    details: Optional[dict] = None
    trace_id: Optional[str] = None
```

### Pattern 4: Enum for Status
```python
from enum import Enum

class StatusEnum(str, Enum):
    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"

class TaskResponse(BaseModel):
    status: StatusEnum
```

---

## Anti-Patterns (Avoid)

### ❌ Mutable Defaults
```python
# ❌ BAD: Mutable default
tags: List[str] = []  # All instances share same list!

# ✅ GOOD: Use default_factory
tags: List[str] = Field(default_factory=list)
```

### ❌ Too Generic Names
```python
# ❌ BAD
class Data(BaseModel): pass
class Info(BaseModel): pass

# ✅ GOOD
class UserProfileData(BaseModel): pass
class AccountInfo(BaseModel): pass
```

### ❌ No Validation
```python
# ❌ BAD: No constraints
email: str
age: int

# ✅ GOOD: Validated
email: EmailStr
age: int = Field(..., ge=0, le=150)
```

### ❌ Nested Too Deep
```python
# ❌ BAD: 5 levels deep
class Level1(BaseModel):
    level2: 'Level2'

class Level2(BaseModel):
    level3: 'Level3'
    # ... too deep

# ✅ GOOD: Flat structure
class User(BaseModel):
    id: UUID
    profile: UserProfile  # 1 level is fine
```

---

## Field Validation Guidelines

### Strings
```python
# Always set min/max length
name: str = Field(..., min_length=1, max_length=255)

# Use specific types
email: EmailStr
url: HttpUrl
```

### Numbers
```python
# Set min/max constraints
age: int = Field(..., ge=0, le=150)
price: float = Field(..., ge=0)
rating: float = Field(..., ge=0, le=5)
```

### Dates
```python
# Use datetime, not string
created_at: datetime
updated_at: Optional[datetime] = None
```

### Lists
```python
# Use default_factory
tags: List[str] = Field(default_factory=list)

# Set max items if needed
tags: List[str] = Field(default_factory=list, max_items=10)
```

---

## Code Review Checklist

**Before submitting contract PR:**

- [ ] All fields have descriptions
- [ ] Validation rules are appropriate
- [ ] No mutable defaults
- [ ] Names follow conventions (PascalCase models, snake_case fields)
- [ ] Examples provided in schema_extra
- [ ] Required vs optional fields clearly defined
- [ ] Breaking changes use new version
- [ ] Tests written for contract
- [ ] Documentation updated

---

## References

- [Pydantic Best Practices](https://docs.pydantic.dev/latest/concepts/models/)
- [DEVELOPER_GUIDE.md](./DEVELOPER_GUIDE.md)
- [VERSIONING.md](./VERSIONING.md)
