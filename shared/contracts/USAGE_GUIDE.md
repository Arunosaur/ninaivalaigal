# Shared Contracts Usage Guide

**Quick Start Guide for Developers**

---

## 🚀 Quick Start

### Python Services

```python
# Import Pydantic models
from shared.contracts.auth.v1.models import User, LoginRequest, AuthResponse
from shared.contracts.common.v1.models import PageRequest, Error

# Use in your API
@app.post("/auth/login", response_model=AuthResponse)
async def login(request: LoginRequest):
    # Type-safe request handling
    user = authenticate_user(request.email, request.password)
    return AuthResponse(
        access_token=create_token(user),
        refresh_token=create_refresh_token(user),
        expires_in=3600,
        user=user
    )

# Pagination
@app.get("/memories", response_model=MemoryList)
async def list_memories(page: PageRequest):
    # Automatic validation: page >= 1, page_size <= 100
    return get_paginated_memories(page.page, page.page_size)
```

### Go Services

```go
// Import generated proto bindings
import (
    authv1 "github.com/Arunosaur/ninaivalaigal/shared/contracts/auth/v1"
    commonv1 "github.com/Arunosaur/ninaivalaigal/shared/contracts/common/v1"
)

// Use in gRPC service
func (s *server) Login(ctx context.Context, req *authv1.LoginRequest) (*authv1.AuthResponse, error) {
    user, err := s.auth.Authenticate(req.Email, req.Password)
    if err != nil {
        return nil, status.Error(codes.Unauthenticated, "Invalid credentials")
    }

    return &authv1.AuthResponse{
        AccessToken: createToken(user),
        User: &authv1.User{
            Id: user.ID,
            Email: user.Email,
            FullName: user.Name,
        },
    }, nil
}
```

---

## 📚 Available Contracts

### Common (shared.contracts.common.v1)
- `Error` - Standard error response
- `PageRequest`, `PageInfo` - Page-based pagination
- `CursorRequest`, `CursorInfo` - Cursor-based pagination

### Auth (shared.contracts.auth.v1)
- `User` - User entity
- `LoginRequest`, `RegisterRequest` - Auth requests
- `AuthResponse`, `ValidateResponse` - Auth responses

### Memory (shared.contracts.memory.v1)
- `Memory` - Memory entity
- `CreateMemoryRequest`, `UpdateMemoryRequest` - Memory operations
- `MemoryList` - Paginated memory list

### Graph (shared.contracts.graph.v1)
- GraphOps protocol buffers (gRPC only)

### Business (shared.contracts.business.v1)
- Billing and analytics protocol buffers (gRPC only)

### Admin (shared.contracts.admin.v1)
- Admin operations protocol buffers (gRPC only)

---

## 🔄 Migration Guide

### Migrating Existing Service

**Before:**
```python
# services/core-api/models.py
class User(BaseModel):
    id: str
    email: str
    # ... duplicated in every service
```

**After:**
```python
# Use centralized contract
from shared.contracts.auth.v1.models import User

# No need to redefine, just use it
@app.get("/users/{id}", response_model=User)
async def get_user(id: str):
    return User(...)
```

### Adding New Fields

1. Update proto file: `shared/contracts/auth/v1/auth.proto`
2. Regenerate bindings: `./scripts/generate-proto-python.sh`
3. Update Pydantic model: `shared/contracts/auth/v1/models.py`
4. Services automatically get new fields

---

## ✅ Best Practices

1. **Always import from contracts:**
   ```python
   # ✅ Good
   from shared.contracts.auth.v1.models import User

   # ❌ Bad
   from services.core_api.models import User  # Leads to drift
   ```

2. **Use version prefixes:**
   ```python
   # ✅ Explicit version
   from shared.contracts.auth.v1.models import User

   # When v2 comes out, both can coexist:
   from shared.contracts.auth.v2.models import User as UserV2
   ```

3. **Validate at boundaries:**
   ```python
   @app.post("/api/endpoint")
   async def endpoint(request: RequestModel):
       # Pydantic validates automatically
       # request.field is already validated
       pass
   ```

4. **Use proto for gRPC, Pydantic for REST:**
   - gRPC services: Import `*_pb2.py` files
   - REST APIs: Import `models.py` files
   - Both stay in sync via contracts

---

## 🔧 Generating Bindings

### Python
```bash
./scripts/generate-proto-python.sh
```

### Go
```bash
./scripts/generate-proto-go.sh
```

### Rust
Add to `build.rs`:
```rust
fn main() {
    tonic_build::configure()
        .compile(
            &["../../shared/contracts/memory/v1/memory.proto"],
            &["../../shared/contracts"],
        )
        .unwrap();
}
```

---

## 🎯 When to Update Contracts

### Breaking Changes (new version required)
- Removing fields
- Changing field types
- Renaming fields
- Making optional fields required

→ Create v2 in new directory

### Non-Breaking Changes (same version OK)
- Adding new optional fields
- Adding new endpoints/methods
- Adding new enum values
- Improving documentation

→ Update existing version

---

## 🐛 Troubleshooting

### Import errors
```bash
# Ensure contracts are in Python path
export PYTHONPATH=/Users/swami/WorkSpace/ninaivalaigal:$PYTHONPATH
```

### Proto compilation errors
```bash
# Regenerate all bindings
cd shared/contracts
python3 -m grpc_tools.protoc --proto_path=. --python_out=. --grpc_python_out=. **/*.proto
```

### Type hints not working
```bash
# Ensure .pyi files generated
ls shared/contracts/auth/v1/*.pyi
```

---

## 📖 Further Reading

- `/shared/contracts/README_CONTRACTS.md` - Full documentation
- `/docs/SPEC_099_100_GAP_ANALYSIS.md` - Architecture context
- Protocol Buffers Guide: https://protobuf.dev/
- Pydantic Documentation: https://docs.pydantic.dev/
