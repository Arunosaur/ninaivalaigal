# Developer C - Morning Tasks (October 15, 2025)

## 🎯 Today's Focus: SPEC-099 Phase 0 - Contract Definition & DevOps Infrastructure

**Priority:** HIGH
**Timeline:** Start of 2-3 week validation phase
**Goal:** Define gRPC contracts and prepare infrastructure for Rust microservices

---

## 📋 Task List (Priority Order)

### 1. 📜 Create Protocol Buffer Schema (gRPC Contracts) (2 hours)

```bash
cd /Users/swami/WorkSpace/ninaivalaigal
mkdir -p shared/contracts/graphops
cd shared/contracts/graphops
```

**File:** `graphops.proto`

```protobuf
syntax = "proto3";

package graphops.v1;

// GraphOps Service Definition
service GraphOpsService {
  // Execute Cypher query on graph database
  rpc ExecuteQuery(CypherRequest) returns (GraphResult);

  // Get memory relationship network
  rpc GetMemoryNetwork(NetworkRequest) returns (NetworkGraph);

  // Analyze graph patterns
  rpc AnalyzePatterns(PatternRequest) returns (PatternAnalysis);

  // Health check
  rpc HealthCheck(HealthCheckRequest) returns (HealthCheckResponse);
}

// Request Messages
message CypherRequest {
  string query = 1;
  map<string, string> parameters = 2;
  int32 timeout_ms = 3;
  optional string trace_id = 4;  // For distributed tracing
}

message NetworkRequest {
  string memory_id = 1;
  int32 max_depth = 2;
  repeated string relationship_types = 3;
}

message PatternRequest {
  string graph_name = 1;
  string pattern_type = 2;  // "hub", "community", "path"
  int32 limit = 3;
}

message HealthCheckRequest {
  optional string service = 1;
}

// Response Messages
message GraphResult {
  repeated GraphNode nodes = 1;
  repeated GraphEdge edges = 2;
  optional QueryMetrics metrics = 3;
  optional string error = 4;
}

message GraphNode {
  string id = 1;
  repeated string labels = 2;
  map<string, string> properties = 3;
}

message GraphEdge {
  string id = 1;
  string type = 2;
  string source = 3;
  string target = 4;
  map<string, string> properties = 5;
}

message QueryMetrics {
  double execution_time_ms = 1;
  int32 nodes_returned = 2;
  int32 edges_returned = 3;
  bool cache_hit = 4;
}

message NetworkGraph {
  repeated GraphNode nodes = 1;
  repeated GraphEdge edges = 2;
  string center_node_id = 3;
  int32 total_depth = 4;
}

message PatternAnalysis {
  string pattern_type = 1;
  repeated GraphNode hub_nodes = 2;
  repeated Community communities = 3;
  double confidence_score = 4;
}

message Community {
  string id = 1;
  repeated string node_ids = 2;
  int32 size = 3;
  double cohesion_score = 4;
}

message HealthCheckResponse {
  string status = 1;  // "SERVING", "NOT_SERVING", "UNKNOWN"
  int64 uptime_seconds = 2;
  string version = 3;
  bool database_connected = 4;
  optional string error_message = 5;
}
```

**Generate code for both languages:**
```bash
# Install protobuf compiler
# macOS:
brew install protobuf

# Generate Rust code
mkdir -p ../../rust-services/graphops/src/proto
protoc --rust_out=../../rust-services/graphops/src/proto \
       --tonic_out=../../rust-services/graphops/src/proto \
       graphops.proto

# Generate Python code
mkdir -p ../../python-clients/graphops/graphops_client/proto
python -m grpc_tools.protoc \
  --python_out=../../python-clients/graphops/graphops_client/proto \
  --grpc_python_out=../../python-clients/graphops/graphops_client/proto \
  --proto_path=. \
  graphops.proto
```

**Acceptance:** Protobuf schema compiles for both Rust and Python

---

### 2. 🔐 Create Contract Validation CI Script (1.5 hours)

**File:** `ci/validate-api-contracts.py`

```python
#!/usr/bin/env python3
"""
API Contract Validation Script
Ensures gRPC contracts remain compatible across versions
"""

import sys
import json
import subprocess
from pathlib import Path
from typing import Dict, List


class ContractValidator:
    def __init__(self, contracts_dir: Path):
        self.contracts_dir = contracts_dir
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def validate_protobuf_syntax(self) -> bool:
        """Validate all .proto files compile successfully"""
        proto_files = list(self.contracts_dir.rglob("*.proto"))

        if not proto_files:
            self.errors.append("No .proto files found")
            return False

        for proto_file in proto_files:
            try:
                result = subprocess.run(
                    ["protoc", "--descriptor_set_out=/dev/null", str(proto_file)],
                    capture_output=True,
                    text=True,
                    check=True
                )
                print(f"✅ {proto_file.name} compiles successfully")
            except subprocess.CalledProcessError as e:
                self.errors.append(f"❌ {proto_file.name} compilation failed: {e.stderr}")
                return False

        return True

    def check_breaking_changes(self) -> bool:
        """Check for breaking changes in proto schemas"""
        # TODO: Implement using buf or protolock
        # For now, just print warning
        self.warnings.append("Breaking change detection not yet implemented")
        return True

    def validate_naming_conventions(self) -> bool:
        """Ensure proto files follow naming conventions"""
        proto_files = list(self.contracts_dir.rglob("*.proto"))

        for proto_file in proto_files:
            content = proto_file.read_text()

            # Check package naming (should be service.v1 format)
            if "package" in content:
                package_line = [l for l in content.split("\n") if "package" in l][0]
                if ".v1" not in package_line:
                    self.warnings.append(f"⚠️  {proto_file.name} should use versioned package (e.g., graphops.v1)")

        return True

    def generate_report(self) -> Dict:
        """Generate validation report"""
        return {
            "passed": len(self.errors) == 0,
            "errors": self.errors,
            "warnings": self.warnings
        }


def main():
    contracts_dir = Path(__file__).parent.parent / "shared" / "contracts"

    validator = ContractValidator(contracts_dir)

    print("🔍 Validating API Contracts...\n")

    # Run validations
    syntax_ok = validator.validate_protobuf_syntax()
    breaking_ok = validator.check_breaking_changes()
    naming_ok = validator.validate_naming_conventions()

    # Generate report
    report = validator.generate_report()

    print("\n" + "="*50)
    if report["passed"]:
        print("✅ API Contract Validation PASSED")
    else:
        print("❌ API Contract Validation FAILED")
    print("="*50)

    if report["errors"]:
        print("\nErrors:")
        for error in report["errors"]:
            print(f"  {error}")

    if report["warnings"]:
        print("\nWarnings:")
        for warning in report["warnings"]:
            print(f"  {warning}")

    sys.exit(0 if report["passed"] else 1)


if __name__ == "__main__":
    main()
```

**Make executable:**
```bash
chmod +x ci/validate-api-contracts.py
```

**Test validation:**
```bash
python3 ci/validate-api-contracts.py
```

**Acceptance:** Contract validation script runs and passes

---

### 3. 🔄 Add Contract Validation to Pre-commit Hooks (30 min)

**File:** `.pre-commit-config.yaml` (append to existing)

```yaml
  # API Contract Validation
  - repo: local
    hooks:
      - id: validate-api-contracts
        name: Validate API Contracts
        entry: python3 ci/validate-api-contracts.py
        language: system
        pass_filenames: false
        files: '^shared/contracts/.*\.proto$'
```

**Test pre-commit hook:**
```bash
# Modify a proto file to test
echo "// Test change" >> shared/contracts/graphops/graphops.proto

# Run pre-commit
pre-commit run validate-api-contracts --all-files

# Revert test change
git checkout shared/contracts/graphops/graphops.proto
```

**Acceptance:** Contract validation runs on proto file changes

---

### 4. 🐳 Create Rust Service Dockerfile (1.5 hours)

**File:** `containers/graphops-rust/Dockerfile`

```dockerfile
# Multi-stage Dockerfile for Rust GraphOps service
FROM rust:1.75-alpine AS builder

# Install build dependencies
RUN apk add --no-cache \
    musl-dev \
    protobuf-dev \
    openssl-dev \
    pkgconfig

WORKDIR /app

# Copy dependency manifests
COPY rust-services/graphops/Cargo.toml rust-services/graphops/Cargo.lock ./

# Cache dependencies
RUN mkdir src && \
    echo "fn main() {}" > src/main.rs && \
    cargo build --release && \
    rm -rf src

# Copy source code
COPY rust-services/graphops/src ./src
COPY shared/contracts/graphops/graphops.proto ./proto/

# Build application
RUN cargo build --release --bin graphops-service

# Runtime stage
FROM alpine:latest

RUN apk add --no-cache \
    ca-certificates \
    libgcc

WORKDIR /app

# Copy binary from builder
COPY --from=builder /app/target/release/graphops-service .

# Create non-root user
RUN addgroup -g 1000 graphops && \
    adduser -D -u 1000 -G graphops graphops && \
    chown -R graphops:graphops /app

USER graphops

# Expose gRPC port
EXPOSE 50051

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD ["/app/graphops-service", "--health-check"]

ENTRYPOINT ["/app/graphops-service"]
```

**File:** `containers/graphops-rust/.dockerignore`

```
target/
Cargo.lock
*.swp
*.swo
.git/
```

**Build script:** `scripts/build-graphops-rust.sh`

```bash
#!/bin/bash
set -euo pipefail

echo "🏗️  Building GraphOps Rust Service..."

# Build for ARM64 (Apple Silicon)
container build \
  --platform linux/arm64 \
  -t graphops-rust:arm64 \
  -f containers/graphops-rust/Dockerfile \
  .

echo "✅ GraphOps Rust service built successfully"
echo "Run with: container run -p 50051:50051 graphops-rust:arm64"
```

**Make executable and test:**
```bash
chmod +x scripts/build-graphops-rust.sh
# Will test after Developer A creates src/main.rs
```

**Acceptance:** Dockerfile created and ready for build

---

### 5. 📊 Create Performance Monitoring Dashboard Config (1 hour)

**File:** `monitoring/grafana-dashboards/graphops-performance.json`

```json
{
  "dashboard": {
    "title": "GraphOps Performance (Python vs Rust)",
    "panels": [
      {
        "id": 1,
        "title": "Request Latency (P50/P95/P99)",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.50, rate(graphops_request_duration_seconds_bucket[5m]))",
            "legendFormat": "Rust P50"
          },
          {
            "expr": "histogram_quantile(0.95, rate(graphops_request_duration_seconds_bucket[5m]))",
            "legendFormat": "Rust P95"
          },
          {
            "expr": "histogram_quantile(0.99, rate(graphops_request_duration_seconds_bucket[5m]))",
            "legendFormat": "Rust P99"
          }
        ]
      },
      {
        "id": 2,
        "title": "Throughput (Requests/sec)",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(graphops_requests_total[1m])",
            "legendFormat": "Rust RPS"
          }
        ]
      },
      {
        "id": 3,
        "title": "Cache Hit Rate",
        "type": "stat",
        "targets": [
          {
            "expr": "rate(graphops_cache_hits_total[5m]) / rate(graphops_requests_total[5m]) * 100",
            "legendFormat": "Cache Hit %"
          }
        ]
      },
      {
        "id": 4,
        "title": "Database Connections",
        "type": "gauge",
        "targets": [
          {
            "expr": "graphops_db_connections_active",
            "legendFormat": "Active Connections"
          }
        ]
      }
    ]
  }
}
```

**Acceptance:** Dashboard config ready for Grafana import

---

### 6. 📝 Create Deployment Documentation (1 hour)

**File:** `docs/deployment/graphops-rust-deployment.md`

```markdown
# GraphOps Rust Service - Deployment Guide

## Prerequisites

- Container runtime (Docker or Apple Container CLI)
- PostgreSQL 15+ with Apache AGE extension
- Redis (optional, for caching)

## Configuration

### Environment Variables

```bash
# Database  # pragma: allowlist secret
DATABASE_URL="postgresql://user:pass@host:5432/database"  # pragma: allowlist secret

# Service
GRPC_PORT=50051
LOG_LEVEL=info

# Performance
DB_POOL_SIZE=10
QUERY_TIMEOUT_MS=5000
```

## Local Development

### Build

```bash
./scripts/build-graphops-rust.sh
```

### Run

```bash
container run -d \
  --name graphops-rust \
  -p 50051:50051 \
  -e DATABASE_URL="$DATABASE_URL" \
  graphops-rust:arm64
```

### Health Check

```bash
# gRPC health check
grpcurl -plaintext localhost:50051 graphops.v1.GraphOpsService/HealthCheck
```

## Performance Benchmarking

### Rust Benchmarks

```bash
cd rust-services/graphops
cargo bench
```

### Comparison with Python

```bash
# Run both benchmarks
python3 benchmarks/python_graphops_baseline.py
cd rust-services/graphops && cargo bench

# Compare results
./scripts/compare-performance.sh
```

## Monitoring

### Prometheus Metrics

Exposed at `http://localhost:50051/metrics`

Key metrics:
- `graphops_request_duration_seconds` - Request latency histogram
- `graphops_requests_total` - Total requests counter
- `graphops_cache_hits_total` - Cache hits counter
- `graphops_db_connections_active` - Active database connections

### Grafana Dashboard

Import dashboard from `monitoring/grafana-dashboards/graphops-performance.json`

## Troubleshooting

### Container won't start

```bash
# Check logs
container logs graphops-rust

# Verify database connection
psql $DATABASE_URL -c "SELECT version();"
```

### gRPC connection refused

```bash
# Verify port is exposed
netstat -an | grep 50051

# Test with grpcurl
grpcurl -plaintext localhost:50051 list
```

## Production Deployment

See [SPEC-099](../../specs/099-rust-migration-strategy/README.md) for production rollout strategy.
```

**Acceptance:** Deployment documentation complete

---

## 🎯 End-of-Day Goals

**By 5 PM Today:**
- [ ] gRPC contracts defined (protobuf schema)
- [ ] Contract validation CI script working
- [ ] Pre-commit hook integrated
- [ ] Rust Dockerfile created
- [ ] Monitoring dashboard configured
- [ ] Deployment documentation written

**Expected Output:**
- Protocol buffer schema for GraphOps service
- Automated contract validation in CI
- Docker build infrastructure ready
- Performance monitoring dashboards configured

---

## 📊 Progress Tracking

| Task | Status | Time Spent | Notes |
|------|--------|------------|-------|
| Protocol Buffer Schema | ⏳ | - | - |
| Contract Validation Script | ⏳ | - | - |
| Pre-commit Integration | ⏳ | - | - |
| Rust Dockerfile | ⏳ | - | - |
| Monitoring Dashboard | ⏳ | - | - |
| Deployment Docs | ⏳ | - | - |

---

## 🆘 If You Get Blocked

**Protobuf Compilation Issues:**
- Install protoc: `brew install protobuf`
- Check version: `protoc --version` (need 3.15+)
- Verify grpc_tools installed: `pip install grpcio-tools`

**Contract Validation Issues:**
- Ensure protoc in PATH
- Check proto syntax with: `protoc --descriptor_set_out=/dev/null file.proto`

**Docker Build Issues:**
- Clear build cache: `container system prune -a`
- Check Dockerfile syntax
- Verify base images available

---

## 💬 Standup Notes Template

**What I completed yesterday:**
- [Previous work]

**What I'm working on today:**
- Defining gRPC contracts for GraphOps service
- Setting up contract validation CI
- Preparing Docker infrastructure for Rust services
- Creating monitoring dashboards

**Blockers:**
- None / [Describe blocker]

**Key deliverables:**
- Contract schema: Ready/In Progress
- CI validation: Working/Not Working
- Docker build: Ready/Not Ready

---

**Questions for team:**
- gRPC port 50051 confirmed for GraphOps?
- Prometheus metrics format preferences?
- Contract versioning strategy (v1, v2, etc.)?

---

**Next Steps (Tomorrow):**
- Help Developer A integrate gRPC server
- Set up contract testing with Developer B
- Create CI workflow for contract validation
- Configure Prometheus scraping

---

**Last Updated:** 2025-10-15 01:15 AM
**Owner:** Developer C
**Sprint:** SPEC-099 Phase 0 (Week 1 of 3)
