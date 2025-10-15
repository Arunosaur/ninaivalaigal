# SPEC-100: Runtime-Agnostic Contract Layer

**Status:** PLANNED (Critical for SPEC-099)
**Priority:** CRITICAL
**Category:** Architecture / Service Integration
**Owner:** Developer C + Architecture Team
**Dependencies:** None (Foundation for SPEC-099 Rust migration)

---

## Executive Summary

Define a **language-agnostic contract layer** that enables Python and Rust services to communicate seamlessly through shared interfaces, ensuring the hybrid architecture (SPEC-099) can evolve without breaking integrations.

**Key Principle:** Services communicate through versioned contracts (gRPC/REST), not direct code dependencies.

---

## 1. 🎯 Purpose

### Problem Statement

As ninaivalaigal transitions to a hybrid Python-Rust architecture (SPEC-099), we need:
- **Polyglot communication:** Python ↔ Rust service calls
- **Contract enforcement:** Automated validation prevents breaking changes
- **Version management:** Safe schema evolution without downtime
- **Developer experience:** Easy-to-use client libraries in both languages

### Solution

Implement a **shared contracts repository** using:
1. **Protocol Buffers** (protobuf) for gRPC services
2. **Pydantic models** for shared data structures
3. **OpenAPI schemas** for REST APIs
4. **Automated CI validation** to prevent contract drift

---

## 2. 📋 Contract Types

### 2.1 Protocol Buffer Contracts (gRPC)

**Use Cases:** High-performance service-to-service communication

**Example:** GraphOps Service Contract

```protobuf
// shared/contracts/graphops/v1/graphops.proto
syntax = "proto3";

package graphops.v1;

service GraphOpsService {
  // Execute Cypher query on graph database
  rpc ExecuteQuery(CypherRequest) returns (GraphResult);

  // Health check
  rpc HealthCheck(HealthCheckRequest) returns (HealthCheckResponse);
}

message CypherRequest {
  string query = 1;
  map<string, string> parameters = 2;
  int32 timeout_ms = 3 [default = 5000];
  optional string trace_id = 4;  // OpenTelemetry tracing
}

message GraphResult {
  repeated GraphNode nodes = 1;
  repeated GraphEdge edges = 2;
  optional QueryMetrics metrics = 3;
  optional ErrorDetails error = 4;
}

message ErrorDetails {
  string code = 1;        // "INVALID_QUERY", "TIMEOUT", etc.
  string message = 2;
  map<string, string> context = 3;
}
```

**Benefits:**
- Type-safe code generation for both Python and Rust
- Built-in backward compatibility checks
- High performance (binary protocol)
- Streaming support for large datasets

---

### 2.2 Pydantic Shared Models (Python)

**Use Cases:** Data validation, FastAPI integration, shared types

**Example:** Shared Memory Models

```python
# shared/contracts/memory/models.py
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class MemoryStatus(str, Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"


class MemoryMetadata(BaseModel):
    """Shared memory metadata structure"""
    created_at: datetime
    updated_at: datetime
    author_id: str
    tags: List[str] = Field(default_factory=list)
    context_id: Optional[str] = None


class MemoryRecord(BaseModel):
    """Core memory data structure shared across services"""
    id: str = Field(..., description="UUID of the memory")
    content: str = Field(..., min_length=1, max_length=10000)
    status: MemoryStatus = Field(default=MemoryStatus.ACTIVE)
    metadata: MemoryMetadata
    embedding: Optional[List[float]] = Field(
        None,
        description="Vector embedding for similarity search"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "content": "User preference for dark mode",
                "status": "active",
                "metadata": {
                    "created_at": "2025-10-15T00:00:00Z",
                    "updated_at": "2025-10-15T00:00:00Z",
                    "author_id": "user123",
                    "tags": ["preference", "ui"]
                }
            }
        }
```

**Benefits:**
- Runtime validation in Python services
- Automatic OpenAPI schema generation
- IDE autocomplete and type checking
- FastAPI integration

---

### 2.3 OpenAPI Schemas (REST APIs)

**Use Cases:** External API documentation, REST endpoints

**Example:** Generated from Pydantic models

```yaml
# shared/contracts/openapi/memory-api.yaml
openapi: 3.0.0
info:
  title: Memory Service API
  version: 1.0.0

paths:
  /memory/{memory_id}:
    get:
      summary: Retrieve memory by ID
      parameters:
        - name: memory_id
          in: path
          required: true
          schema:
            type: string
            format: uuid
      responses:
        '200':
          description: Memory retrieved successfully
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/MemoryRecord'
        '404':
          description: Memory not found

components:
  schemas:
    MemoryRecord:
      $ref: './models.yaml#/MemoryRecord'
```

**Benefits:**
- External API documentation
- Client SDK generation
- Contract testing tools (Pact, Dredd)

---

## 3. 🏗️ Repository Structure

```
shared/
├── contracts/
│   ├── README.md                           # Contract documentation
│   │
│   ├── graphops/
│   │   ├── v1/
│   │   │   ├── graphops.proto              # gRPC contract
│   │   │   ├── models.py                   # Pydantic models
│   │   │   └── openapi.yaml                # REST contract
│   │   └── v2/                             # Future version
│   │
│   ├── memory/
│   │   ├── v1/
│   │   │   ├── memory.proto
│   │   │   ├── models.py
│   │   │   └── openapi.yaml
│   │   └── README.md
│   │
│   ├── feedback/
│   │   └── v1/
│   │       ├── feedback.proto
│   │       └── models.py
│   │
│   └── common/
│       ├── errors.proto                    # Shared error types
│       ├── pagination.proto                # Shared pagination
│       └── types.py                        # Common Pydantic types
│
├── clients/
│   ├── python/                             # Generated Python clients
│   │   ├── graphops_client/
│   │   ├── memory_client/
│   │   └── setup.py
│   │
│   └── rust/                               # Generated Rust clients
│       ├── graphops_client/
│       ├── memory_client/
│       └── Cargo.toml
│
└── scripts/
    ├── generate-proto.sh                   # Generate code from proto
    ├── generate-openapi.sh                 # Generate OpenAPI schemas
    └── validate-contracts.py               # CI validation script
```

---

## 4. 🔄 Contract Versioning Strategy

### Semantic Versioning for Contracts

**v1, v2, v3** format for major contract versions

| Change Type | Version Bump | Example |
|-------------|--------------|---------|
| Add optional field | Patch (v1.0.1) | Add `trace_id` to request |
| Add new RPC method | Minor (v1.1.0) | Add `AnalyzePatterns` method |
| Remove field | Major (v2.0.0) | Remove deprecated `legacy_id` |
| Change field type | Major (v2.0.0) | Change `id: string` → `id: int` |

### Backward Compatibility Rules

**✅ Safe Changes:**
- Add new optional fields (with defaults)
- Add new RPC methods
- Add new enum values (if handled as unknown)
- Increase field numbers (protobuf)

**❌ Breaking Changes:**
- Remove or rename fields
- Change field types
- Change field numbers (protobuf)
- Remove RPC methods
- Change RPC signatures

### Version Coexistence

**Services must support N and N-1 versions simultaneously:**

```rust
// Rust service supporting v1 and v2
impl GraphOpsService for GraphOpsHandler {
    // v1 implementation
    async fn execute_query_v1(
        &self,
        request: v1::CypherRequest
    ) -> Result<v1::GraphResult, Status> {
        // Implementation
    }

    // v2 implementation (new features)
    async fn execute_query_v2(
        &self,
        request: v2::CypherRequest
    ) -> Result<v2::GraphResult, Status> {
        // Enhanced implementation
    }
}
```

---

## 5. 🤖 Code Generation

### 5.1 Protocol Buffer Code Generation

**For Rust:**
```bash
# Generate Rust gRPC code
protoc --rust_out=rust-services/graphops/src/proto \
       --tonic_out=rust-services/graphops/src/proto \
       shared/contracts/graphops/v1/graphops.proto

# Generated files:
# - graphops.rs (message types)
# - graphops.tonic.rs (gRPC service/client)
```

**For Python:**
```bash
# Generate Python gRPC code
python -m grpc_tools.protoc \
  --python_out=python-clients/graphops/graphops_client/proto \
  --grpc_python_out=python-clients/graphops/graphops_client/proto \
  --proto_path=shared/contracts \
  graphops/v1/graphops.proto

# Generated files:
# - graphops_pb2.py (message types)
# - graphops_pb2_grpc.py (gRPC service/client)
```

### 5.2 OpenAPI Code Generation

**From Pydantic → OpenAPI:**
```python
# scripts/generate-openapi.py
from fastapi import FastAPI
from shared.contracts.memory.models import MemoryRecord
import json

app = FastAPI()

@app.get("/memory/{memory_id}", response_model=MemoryRecord)
async def get_memory(memory_id: str):
    pass  # Stub for schema generation

# Export OpenAPI schema
with open("shared/contracts/openapi/memory-api.yaml", "w") as f:
    f.write(app.openapi())
```

---

## 6. ✅ Contract Validation (CI/CD)

### 6.1 Automated CI Checks

**File:** `ci/validate-contracts.py`

```python
#!/usr/bin/env python3
"""
Contract validation CI script
Prevents breaking changes from being committed
"""

import sys
from pathlib import Path
from typing import List, Tuple


class ContractValidator:
    def __init__(self, contracts_dir: Path):
        self.contracts_dir = contracts_dir
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def validate_protobuf_syntax(self) -> bool:
        """Compile all .proto files"""
        # Implementation in DEVELOPER_C_MORNING_TASKS.md
        pass

    def check_breaking_changes(self) -> bool:
        """Compare with previous contract version"""
        # Use buf: https://buf.build/
        # or protolock: https://github.com/nilslice/protolock
        pass

    def validate_pydantic_models(self) -> bool:
        """Ensure Pydantic models are valid"""
        try:
            # Import all model files
            from shared.contracts.memory.models import MemoryRecord
            from shared.contracts.graphops.models import GraphResult

            # Validate example data
            MemoryRecord.model_validate({
                "id": "test-id",
                "content": "test",
                # ... full example
            })

            return True
        except Exception as e:
            self.errors.append(f"Pydantic validation failed: {e}")
            return False

    def validate_openapi_schemas(self) -> bool:
        """Validate OpenAPI schemas"""
        # Use openapi-spec-validator
        pass
```

### 6.2 Pre-commit Hook

**File:** `.pre-commit-config.yaml`

```yaml
  # Contract Validation
  - repo: local
    hooks:
      - id: validate-contracts
        name: Validate API Contracts
        entry: python3 ci/validate-contracts.py
        language: system
        pass_filenames: false
        files: '^shared/contracts/.*\.(proto|py|yaml)$'
```

### 6.3 GitHub Actions CI

**File:** `.github/workflows/contract-validation.yml`

```yaml
name: Contract Validation

on:
  pull_request:
    paths:
      - 'shared/contracts/**'

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup protobuf compiler
        run: |
          sudo apt-get update
          sudo apt-get install -y protobuf-compiler

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install grpcio-tools pydantic fastapi

      - name: Validate contracts
        run: python3 ci/validate-contracts.py

      - name: Generate code (test)
        run: ./shared/scripts/generate-proto.sh

      - name: Check for breaking changes
        run: |
          # Use buf or protolock
          buf breaking --against '.git#branch=main'
```

---

## 7. 📦 Client Library Distribution

### 7.1 Python Package

**File:** `shared/clients/python/setup.py`

```python
from setuptools import setup, find_packages

setup(
    name="ninaivalaigal-contracts",
    version="1.0.0",
    description="Shared contracts for ninaivalaigal services",
    packages=find_packages(),
    install_requires=[
        "grpcio>=1.50.0",
        "grpcio-tools>=1.50.0",
        "pydantic>=2.0.0",
        "protobuf>=4.21.0",
    ],
    python_requires=">=3.11",
)
```

**Install in services:**
```bash
# Install shared contracts in Python services
pip install -e /path/to/shared/clients/python
```

### 7.2 Rust Crate

**File:** `shared/clients/rust/Cargo.toml`

```toml
[package]
name = "ninaivalaigal-contracts"
version = "1.0.0"
edition = "2021"

[dependencies]
prost = "0.12"
tonic = "0.10"
serde = { version = "1.0", features = ["derive"] }
```

**Use in Rust services:**
```toml
# In rust-services/graphops/Cargo.toml
[dependencies]
ninaivalaigal-contracts = { path = "../../shared/clients/rust" }
```

---

## 8. 🔍 Contract Testing

### 8.1 Unit Tests

**Python Example:**
```python
# tests/contracts/test_memory_models.py
from shared.contracts.memory.models import MemoryRecord, MemoryStatus
import pytest

def test_memory_record_validation():
    """Ensure MemoryRecord validates correctly"""
    record = MemoryRecord(
        id="550e8400-e29b-41d4-a716-446655440000",
        content="Test memory",
        status=MemoryStatus.ACTIVE,
        metadata={
            "created_at": "2025-10-15T00:00:00Z",
            "updated_at": "2025-10-15T00:00:00Z",
            "author_id": "user123",
            "tags": []
        }
    )
    assert record.id == "550e8400-e29b-41d4-a716-446655440000"
    assert record.status == MemoryStatus.ACTIVE

def test_memory_record_validation_fails_on_invalid_data():
    """Ensure validation catches invalid data"""
    with pytest.raises(ValidationError):
        MemoryRecord(
            id="invalid-uuid",  # Not a valid UUID
            content="",          # Empty content not allowed
            status="invalid",    # Invalid status
            metadata={}          # Missing required fields
        )
```

### 8.2 Contract Tests (Pact)

**Consumer-driven contract testing:**
```python
# tests/contracts/test_graphops_pact.py
from pact import Consumer, Provider

pact = Consumer('PythonAPI').has_pact_with(Provider('GraphOpsRust'))

def test_graphops_execute_query_contract():
    """Define expected contract for GraphOps service"""
    expected = {
        "query": "MATCH (n) RETURN n LIMIT 10",
        "timeout_ms": 5000
    }

    (pact
     .given('graph database is available')
     .upon_receiving('a request to execute Cypher query')
     .with_request('post', '/graphops/v1/query')
     .will_respond_with(200, body={
         "nodes": [],
         "edges": [],
         "metrics": {
             "execution_time_ms": 12.5,
             "nodes_returned": 0
         }
     }))

    with pact:
        # Make actual request
        client = GraphOpsClient()
        result = client.execute_query(expected)
        assert result.metrics.execution_time_ms > 0
```

---

## 9. 📊 Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Contract compilation success** | 100% | All `.proto` files compile without errors |
| **Breaking change detection** | 0 unintended breaks | buf/protolock catches all breaking changes |
| **Code generation time** | <30s | Time to generate all client code |
| **Client library size** | <5MB Python, <2MB Rust | Package size after compression |
| **Contract test coverage** | >90% | Pact tests cover all service interactions |

---

## 10. 🚦 Implementation Phases

### Phase 0: Foundation (Week 1)
- [ ] Create `shared/contracts/` directory structure
- [ ] Define GraphOps protobuf schema (SPEC-062)
- [ ] Create contract validation CI script
- [ ] Set up code generation scripts

### Phase 1: Core Contracts (Weeks 2-3)
- [ ] Memory service contracts
- [ ] Feedback service contracts
- [ ] Common error types and pagination
- [ ] Python client library package

### Phase 2: Validation & Testing (Week 4)
- [ ] Implement breaking change detection (buf)
- [ ] Add contract unit tests
- [ ] Set up Pact consumer-driven testing
- [ ] Rust client library package

### Phase 3: CI/CD Integration (Week 5)
- [ ] GitHub Actions contract validation
- [ ] Automated client library publishing
- [ ] Contract versioning enforcement
- [ ] Documentation generation

---

## 11. 📚 References

- [Protocol Buffers Guide](https://protobuf.dev/)
- [gRPC Best Practices](https://grpc.io/docs/guides/performance/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [Buf Schema Registry](https://buf.build/)
- [Contract Testing with Pact](https://docs.pact.io/)
- SPEC-099: Rust Migration Strategy

---

## Acceptance Criteria

- [ ] Protobuf schemas defined for all Rust services (GraphOps, Memory, Feedback)
- [ ] Pydantic models shared across Python services
- [ ] Code generation scripts working for both languages
- [ ] Contract validation CI passing
- [ ] Pre-commit hook preventing contract drift
- [ ] Client libraries installable as packages
- [ ] Contract tests covering all service integrations
- [ ] Documentation complete

---

**Last Updated:** 2025-10-15
**Next Review:** After Phase 0 completion (Week 1)
**Critical for:** SPEC-099 Rust Migration Strategy
