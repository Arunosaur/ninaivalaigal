# Backward Compatibility Rules

**Purpose:** What changes are safe vs breaking
**Audience:** All developers modifying contracts

---

## Quick Reference

| Change | v1 → v1 | v1 → v2 |
|--------|---------|---------|
| ✅ Add optional field | SAFE | N/A |
| ✅ Add new endpoint | SAFE | N/A |
| ✅ Relax validation | SAFE | N/A |
| ✅ Add enum value (end) | SAFE | N/A |
| ❌ Remove field | BREAKING | Required |
| ❌ Rename field | BREAKING | Required |
| ❌ Change type | BREAKING | Required |
| ❌ Make field required | BREAKING | Required |
| ❌ Stricter validation | BREAKING | Required |

---

## Safe Changes (Same Version) ✅

### 1. Add Optional Field
```python
# v1 - Before
class UserResponse(BaseModel):
    id: UUID
    name: str

# v1 - After (SAFE)
class UserResponse(BaseModel):
    id: UUID
    name: str
    email: Optional[EmailStr] = None  # New optional field ✅
```

**Why safe:** Old clients ignore new fields, new clients get extra data

---

### 2. Add New Endpoint
```python
# v1 - Before
@router.get("/users/{id}")
async def get_user(id: str): pass

# v1 - After (SAFE)
@router.get("/users/{id}")
async def get_user(id: str): pass

@router.get("/users/{id}/profile")  # New endpoint ✅
async def get_user_profile(id: str): pass
```

**Why safe:** Old clients don't use new endpoint

---

### 3. Relax Validation
```python
# v1 - Before
name: str = Field(..., max_length=50)

# v1 - After (SAFE)
name: str = Field(..., max_length=100)  # More permissive ✅
```

**Why safe:** Old valid data still valid

---

### 4. Add Enum Value (Append Only)
```python
# v1 - Before
class Status(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"

# v1 - After (SAFE)
class Status(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"  # Appended ✅
```

**Why safe:** Old clients handle unknown values gracefully

---

## Breaking Changes (New Version Required) ❌

### 1. Remove Field
```python
# v1 (keep unchanged)
class UserResponse(BaseModel):
    id: UUID
    name: str
    email: EmailStr  # Keep this

# v2 (new version)
class UserResponse(BaseModel):
    id: UUID
    name: str
    # email removed ❌
```

**Why breaking:** Old clients expect field, will error

---

### 2. Rename Field
```python
# v1 (frozen)
class UserResponse(BaseModel):
    name: str

# v2 (new version)
class UserResponse(BaseModel):
    full_name: str  # Renamed ❌
```

**Why breaking:** Old clients look for old field name

---

### 3. Change Field Type
```python
# v1
age: int

# v2
age: str  # Changed type ❌
```

**Why breaking:** Type mismatch causes errors

---

### 4. Make Optional Field Required
```python
# v1
email: Optional[EmailStr] = None

# v2
email: EmailStr  # Now required ❌
```

**Why breaking:** Old clients may not send field

---

### 5. Stricter Validation
```python
# v1
name: str = Field(..., max_length=100)

# v2
name: str = Field(..., max_length=50)  # Stricter ❌
```

**Why breaking:** Old valid data now invalid

---

## Gray Areas ⚠️

### Deprecate Field (Mark but don't remove)
```python
# v1 - Can deprecate without breaking
class UserResponse(BaseModel):
    name: str  # Deprecated: Use full_name instead
    full_name: str  # New field
```

**Process:**
1. Add new field (safe)
2. Mark old field deprecated (safe)
3. Wait 1-2 versions
4. Remove in v3 (breaking → new version)

---

### Change Default Value
```python
# v1
page_size: int = Field(20)

# v1 - Updated default
page_size: int = Field(50)  # ⚠️ Potentially breaking
```

**Evaluation:** Usually safe, but test client behavior

---

### Add Required Field with Default
```python
# v1
class Config(BaseModel):
    timeout: int

# v1 - New required field with default
class Config(BaseModel):
    timeout: int
    retry_count: int = 3  # New with default ✅
```

**Safe if:** Default provides backward-compatible behavior

---

## Testing Compatibility

### Backward Compatibility Test
```python
# tests/test_compatibility.py
def test_old_client_new_server():
    """Verify old request format still works"""
    # Old format (v1 client)
    old_request = {"name": "Test", "email": "test@example.com"}

    # New server (v1.1 with extra optional fields)
    response = client.post("/users", json=old_request)
    assert response.status_code == 201

def test_new_client_old_server():
    """Verify new client handles missing fields"""
    # Server returns old format
    response_data = {"id": "123", "name": "Test"}

    # New client expects optional email
    user = UserResponse(**response_data)
    assert user.email is None  # Handles missing gracefully
```

---

## Migration Strategy

### For Breaking Changes

1. **Create v2**
   ```bash
   mkdir shared/contracts/my-service/v2
   cp -r shared/contracts/my-service/v1/* shared/contracts/my-service/v2/
   ```

2. **Make changes in v2**
   - Edit v2 contracts
   - Keep v1 unchanged

3. **Deploy both versions**
   ```python
   app.include_router(v1_router, prefix="/api/v1")
   app.include_router(v2_router, prefix="/api/v2")
   ```

4. **Migrate clients**
   - Give 30+ days notice
   - Provide migration guide
   - Monitor v1 usage

5. **Deprecate v1**
   - Mark endpoints as deprecated
   - Remove after migration period

---

## References

- [VERSIONING.md](./VERSIONING.md) - Version workflow
- [BREAKING_CHANGES.md](./BREAKING_CHANGES.md) - Breaking change policy
- [DEPRECATION.md](./DEPRECATION.md) - Deprecation process
