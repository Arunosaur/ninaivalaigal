# Shared Contracts Layer

**Created:** October 19, 2025
**Developer:** C (Task #79)
**Status:** 🚧 60% Complete

---

## 📋 Overview

Centralized contract repository for all ninaivalaigal services. Prevents contract drift and enables automated validation.

**Key Benefits:**
- Single source of truth for all service contracts
- Version-controlled contracts (v1, v2, etc.)
- Automated code generation (Python, Go, Rust)
- CI validation prevents breaking changes
- Comprehensive documentation generation

---

## 📁 Directory Structure

```
shared/contracts/
├── auth/v1/
│   ├── auth.proto           ✅ Authentication & authorization
│   ├── models.py            ⏳ Pydantic models (TODO)
│   └── openapi.yaml         ⏳ REST API spec (TODO)
│
├── memory/v1/
│   ├── memory.proto         ✅ Memory CRUD operations
│   ├── models.py            ⏳ Pydantic models (TODO)
│   └── openapi.yaml         ⏳ REST API spec (TODO)
│
├── graph/v1/
│   ├── graphops.proto       ✅ Graph intelligence operations
│   ├── models.py            ⏳ Pydantic models (TODO)
│   └── openapi.yaml         ⏳ REST API spec (TODO)
│
├── business/v1/
│   ├── billing.proto        ✅ Billing & subscriptions
│   ├── analytics.proto      ✅ Analytics & metrics
│   ├── models.py            ⏳ Pydantic models (TODO)
│   └── openapi.yaml         ⏳ REST API spec (TODO)
│
├── admin/v1/
│   ├── admin.proto          ✅ Admin operations
│   ├── models.py            ⏳ Pydantic models (TODO)
│   └── openapi.yaml         ⏳ REST API spec (TODO)
│
└── common/v1/
    ├── errors.proto         ✅ Standard error types
    ├── pagination.proto     ✅ Pagination patterns
    └── types.py             ⏳ Shared Python types (TODO)
```

---

## 🔧 Proto Files Created

### ✅ Common (Foundational)
- `errors.proto` - Standard error responses, validation errors, error codes
- `pagination.proto` - Page-based and cursor-based pagination

### ✅ Auth Service
- `auth.proto` - Register, Login, Token validation, Logout

### ✅ Memory Service
- `memory.proto` - CRUD operations for memories (migrated from grpc-gateway)

### ✅ Graph Service
- `graphops.proto` - Graph intelligence operations (migrated)

### ✅ Business Service
- `billing.proto` - Subscriptions, invoices, usage tracking
- `analytics.proto` - User/org analytics, engagement, cohorts

### ✅ Admin Service
- `admin.proto` - User management, system metrics, audit logs

---

## 🚀 Code Generation

### Generate Python Bindings
```bash
# Generate all Python proto bindings
./scripts/generate-proto-python.sh

# Or manually
protoc --python_out=. --pyi_out=. \
  --proto_path=shared/contracts \
  shared/contracts/**/*.proto
```

### Generate Go Bindings
```bash
# Generate all Go proto bindings
./scripts/generate-proto-go.sh

# Or manually
protoc --go_out=. --go-grpc_out=. \
  --proto_path=shared/contracts \
  shared/contracts/**/*.proto
```

### Generate Rust Bindings
```bash
# Add to rust-services/*/build.rs
fn main() {
    tonic_build::configure()
        .build_server(true)
        .compile(
            &["../../shared/contracts/memory/v1/memory.proto"],
            &["../../shared/contracts"],
        )
        .unwrap();
}
```

---

## 📝 Versioning Strategy

### Version Format: `v1`, `v2`, etc.

**Rules:**
1. **Breaking changes** require new version (v1 → v2)
2. **Additive changes** can stay in same version
3. Keep old versions for backward compatibility
4. Deprecate gradually (6 month window)

**Breaking Changes:**
- Removing fields
- Changing field types
- Renaming fields/services
- Changing required/optional

**Non-Breaking Changes:**
- Adding new fields (optional)
- Adding new services
- Adding new methods
- Adding new enums values

### Example Migration:
```
# v1 (stable)
shared/contracts/memory/v1/memory.proto

# v2 (new version with breaking changes)
shared/contracts/memory/v2/memory.proto

# Both versions coexist during transition
```

---

## ✅ Completed (60%)

1. ✅ Directory structure created
2. ✅ All proto files created (7 files)
3. ✅ Common types defined (errors, pagination)
4. ✅ Service contracts defined (auth, memory, graph, business, admin)
5. ✅ Documentation created

---

## ⏳ TODO (40%)

1. ⏳ Generate Python bindings from proto
2. ⏳ Create Pydantic models for each service
3. ⏳ Generate OpenAPI schemas
4. ⏳ Add proto generation to CI/CD
5. ⏳ Add contract validation to pre-commit
6. ⏳ Update services to use centralized contracts
7. ⏳ Create breaking change detection
8. ⏳ Document migration guide

---

## 🔍 Contract Validation

### Pre-commit Hook (TODO)
```yaml
# .pre-commit-config.yaml
- repo: local
  hooks:
    - id: proto-lint
      name: Lint protocol buffers
      entry: buf lint
      language: system
      files: \.proto$

    - id: proto-breaking
      name: Check for breaking changes
      entry: buf breaking --against '.git#branch=main'
      language: system
      files: \.proto$
```

### CI Validation (TODO)
```yaml
# .github/workflows/contracts.yml
name: Contract Validation
on: [pull_request]
jobs:
  validate:
    steps:
      - uses: bufbuild/buf-setup-action@v1
      - run: buf lint
      - run: buf breaking --against ${{ github.base_ref }}
```

---

## 📚 Service Integration

### Python Service Example
```python
# Before (scattered models)
from services.core-api.models import User

# After (centralized contracts)
from shared.contracts.auth.v1.models import User
```

### Go Service Example
```go
// Before
import "github.com/Arunosaur/ninaivalaigal/go-services/grpc-gateway/proto"

// After
import authv1 "github.com/Arunosaur/ninaivalaigal/shared/contracts/auth/v1"
```

### Rust Service Example
```rust
// Before
pub mod proto {
    include!("./proto/memory.rs");
}

// After
use ninaivalaigal_contracts::memory::v1::{Memory, CreateMemoryRequest};
```

---

## 🎯 Next Steps

1. Create `generate-proto-python.sh` script
2. Create `generate-proto-go.sh` script
3. Generate all bindings
4. Extract Pydantic models from services
5. Add to CI/CD pipeline
6. Update all services to use contracts

---

## 📊 Progress: 60% Complete

**Remaining Work:** 8-10 hours to complete Task #79

**Target Completion:** Week 1 (Priority 1 task)
