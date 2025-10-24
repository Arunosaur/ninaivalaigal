# Service Contracts - API Specifications

**SPEC-100: API Container Modularization & Runtime-Agnostic Federation**

This directory contains both gRPC service contracts (Protocol Buffers) and REST API specifications (OpenAPI 3.0) that define the interfaces between federated microservices in the Ninaivalaigal platform.

## 📋 Purpose

- **Runtime-agnostic interfaces:** Python and Rust services implement the same contracts
- **Schema validation:** CI enforces contract compatibility before deployment
- **Type safety:** Generated client/server code in both languages
- **Versioning:** Explicit version paths (v1, v2, etc.) for breaking changes
- **Documentation:** Self-documenting service APIs

## 📁 Directory Structure

```
shared/contracts/
├── README.md                     # This file
├── setup.py                      # Python package configuration
├── graphops/                     # GraphOps gRPC service (SPEC-099)
│   └── v1/
│       └── graphops.proto        # GraphOps Cypher execution service
├── core-api/                     # Core API REST service
│   └── v1/
│       └── openapi.yaml          # Auth, Users, Teams, RBAC
├── memory-service/               # Memory Service REST API
│   └── v1/
│       └── openapi.yaml          # Memory CRUD, Context, Recording
├── graph-ai-service/             # Graph/AI Service REST API
│   └── v1/
│       └── openapi.yaml          # Intelligence, Insights, Feedback
├── business-service/             # Business Service REST API
│   └── v1/
│       └── openapi.yaml          # Billing, Usage, Invoices
└── admin-vendor-service/         # Admin/Vendor Service REST API
    └── v1/
        └── openapi.yaml          # Analytics, Dashboard, Workflows
```

## 🚀 Quick Start

### 1. Generate Code for Rust

```bash
# From rust-services/graphops/
cargo build

# Generated files appear in:
# target/debug/build/graphops-service-*/out/
```

### 2. Generate Code for Python

```bash
# Install tools
pip install grpcio-tools

# Generate Python stubs
python -m grpc_tools.protoc \
  -I./shared/contracts \
  --python_out=./server/contracts \
  --grpc_python_out=./server/contracts \
  shared/contracts/graphops/v1/graphops.proto
```

### 3. Validate Contracts (CI)

```bash
# Run contract validation
./scripts/validate-contracts.sh

# Check for breaking changes
./scripts/check-breaking-changes.sh
```

## 📝 Contract Guidelines

### 1. Versioning

- **Major versions** in path: `graphops/v1/`, `graphops/v2/`
- **Breaking changes** require new version
- **Backward-compatible changes** stay in same version

### 2. Naming Conventions

- **Services:** `PascalCase` + `Service` suffix (e.g., `GraphOpsService`)
- **RPCs:** `PascalCase` verbs (e.g., `ExecuteQuery`, `HealthCheck`)
- **Messages:** `PascalCase` (e.g., `CypherRequest`, `CypherResponse`)
- **Fields:** `snake_case` (e.g., `query_text`, `execution_time_ms`)

### 3. Required Fields

Every service contract must include:
- Health check RPC
- Error handling messages
- Tracing fields (`trace_id`, `span_id`)
- Performance metrics

### 4. Documentation

- Every service, RPC, message, and field must have comments
- Include usage examples in service-level comments
- Document error codes and status values

## 🔧 Adding a New Contract

### Step 1: Create Proto File

```bash
mkdir -p shared/contracts/myservice/v1
touch shared/contracts/myservice/v1/myservice.proto
```

### Step 2: Define Service

```protobuf
syntax = "proto3";

package ninaivalaigal.myservice.v1;

service MyService {
  rpc DoSomething(DoSomethingRequest) returns (DoSomethingResponse);
  rpc HealthCheck(HealthCheckRequest) returns (HealthCheckResponse);
}

message DoSomethingRequest {
  string input = 1;
  string trace_id = 2;
}

message DoSomethingResponse {
  string output = 1;
  int32 execution_time_ms = 2;
}
```

### Step 3: Update Build Files

**Rust (`build.rs`):**
```rust
fn main() {
    tonic_build::compile_protos("../../shared/contracts/myservice/v1/myservice.proto")
        .unwrap();
}
```

**Python (add to `scripts/generate-python-contracts.sh`):**
```bash
python -m grpc_tools.protoc \
  -I./shared/contracts \
  --python_out=./server/contracts \
  --grpc_python_out=./server/contracts \
  shared/contracts/myservice/v1/myservice.proto
```

### Step 4: Validate

```bash
# Check syntax
buf lint shared/contracts/

# Generate code
cd rust-services/myservice && cargo build
cd server && python scripts/generate-python-contracts.sh

# Run contract tests
pytest tests/contracts/test_myservice_contract.py
```

## 📊 Contract Compliance (SPEC-100)

### CI Validation

Every PR must pass:
1. **Syntax validation:** `buf lint`
2. **Breaking change detection:** `buf breaking --against .git/main`
3. **Code generation:** Rust + Python stubs compile without errors
4. **Contract tests:** Mock implementations pass

### Breaking Changes

**Allowed (backward-compatible):**
- Adding new RPCs
- Adding new optional fields
- Adding new enum values
- Adding new messages

**Not allowed (breaking):**
- Removing or renaming RPCs
- Removing or renaming fields
- Changing field numbers
- Changing field types
- Removing enum values

### Deployment Strategy

1. **New version:** Create `v2/` directory for breaking changes
2. **Parallel deployment:** Run v1 and v2 services side-by-side
3. **Client migration:** Update clients to v2 gradually
4. **Deprecation:** Mark v1 as deprecated after 6 months
5. **Removal:** Remove v1 after 12 months

## 🧪 Testing Contracts

### Unit Tests (Mock)

```python
# tests/contracts/test_graphops_contract.py
import grpc
from contracts.graphops.v1 import graphops_pb2, graphops_pb2_grpc

def test_execute_query_request():
    request = graphops_pb2.CypherRequest(
        query="MATCH (n) RETURN n LIMIT 10",
        timeout_ms=5000,
        trace_id="test-trace-123"
    )
    assert request.query == "MATCH (n) RETURN n LIMIT 10"
```

### Integration Tests (Live)

```bash
# Start test services
docker-compose -f deployment/dev/docker-compose.contracts.yml up -d

# Run integration tests
pytest tests/integration/test_graphops_contract_integration.py

# Cleanup
docker-compose -f deployment/dev/docker-compose.contracts.yml down
```

## 📚 Documentation

### 🚀 Getting Started
- **[Onboarding Guide](docs/ONBOARDING.md)** - Quick start for new developers (30 min)
- **[Developer Guide](docs/DEVELOPER_GUIDE.md)** - Creating service contracts
- **[Service Integration](docs/SERVICE_INTEGRATION.md)** - Integrating contracts into services

### 🔧 Development Guides
- **[Python Integration](docs/PYTHON_INTEGRATION.md)** - FastAPI + Pydantic examples
- **[Rust Integration](docs/RUST_INTEGRATION.md)** - Tonic + Protobuf (future-ready)
- **[Go Integration](docs/GO_INTEGRATION.md)** - gRPC in Go (future-ready)
- **[Validation](docs/VALIDATION.md)** - Testing contracts locally and in CI

### 📋 Policies & Workflows
- **[Versioning](docs/VERSIONING.md)** - Version management workflow
- **[Versioning Strategy](docs/VERSIONING_STRATEGY.md)** - Version numbering and support policy
- **[Breaking Changes](docs/BREAKING_CHANGES.md)** - When and how to make breaking changes
- **[Compatibility](docs/COMPATIBILITY.md)** - Backward compatibility rules
- **[Deprecation](docs/DEPRECATION.md)** - How to deprecate contracts

### 🎯 Best Practices
- **[Best Practices](docs/BEST_PRACTICES.md)** - Design patterns and anti-patterns
- **[CI/CD Integration](docs/CICD_INTEGRATION.md)** - Contract validation in CI
- **[Troubleshooting](docs/TROUBLESHOOTING.md)** - Common issues and solutions

### 📖 External References
- [SPEC-099: Rust Migration Strategy](../../specs/099-rust-migration-strategy/README.md)
- [SPEC-100: API Modularization](../../specs/100-api-container-modularization/README.md)
- [Protocol Buffers Language Guide](https://protobuf.dev/programming-guides/proto3/)
- [gRPC Best Practices](https://grpc.io/docs/guides/performance/)

## 🔍 Tools

- **buf:** Protocol Buffer linting and breaking change detection
- **grpcurl:** CLI for testing gRPC services
- **grpcui:** Web UI for gRPC services
- **BloomRPC:** GUI client for gRPC

```bash
# Install buf
brew install bufbuild/buf/buf

# Install grpcurl
brew install grpcurl

# Test GraphOps service
grpcurl -plaintext \
  -d '{"query": "MATCH (n) RETURN n LIMIT 1"}' \
  localhost:50051 \
  ninaivalaigal.graphops.v1.GraphOpsService/ExecuteQuery
```

## 👥 Ownership

- **Protocol Definitions:** Developer C
- **Rust Implementation:** Developer A
- **Python Implementation:** Developer B
- **CI Validation:** Developer C

---

**Last Updated:** 2025-10-22 (Phase 4 Documentation Complete)
**Status:** Production Ready
**Version:** v1
**Documentation:** 15 guides available in [docs/](docs/)
