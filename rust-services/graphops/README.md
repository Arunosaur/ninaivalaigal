# GraphOps Rust Service

High-performance Apache AGE graph query service built with Rust and Tokio.

## 🔐 Credential Management (No More Manual Exports!)

### Option 1: .env File (Recommended)

Create a `.env` file in this directory:

```bash
cp .env.example .env
```

The `.env` file is automatically loaded by:
- `cargo test`
- `cargo bench`
- Python baseline script (`benchmarks/python_graphops_baseline.py`)

**No manual exports needed!** ✅

---

### Option 2: Shell Script

Source the environment script:

```bash
source env.sh
# or
. env.sh
```

This loads credentials into your current shell session.

---

### Option 3: Manual Export (Old Way)

```bash
export DATABASE_URL="postgresql://nina:dev_password_change_in_production@192.168.64.137:6432/ninaivalaigal_dev"  # pragma: allowlist secret
export GRAPHOPS_GRAPH="ninaivalaigal_intelligence"
```

---

## 🚀 Quick Start

### 1. Setup Credentials

```bash
# Copy example and edit if needed
cp .env.example .env
```

### 2. Run Tests

```bash
cargo test -- --nocapture
```

### 3. Run the gRPC Service

```bash
cargo run --release --bin graphops-service
```

The server binds to `0.0.0.0:50051` for gRPC and `0.0.0.0:9090` for Prometheus metrics by default.

### 4. Run Benchmarks

```bash
# Rust benchmarks
cargo bench --bench graphops_benchmark

# Python baseline (for comparison)
conda run -n nina python benchmarks/python_graphops_baseline.py

# Compare results
./compare_performance.sh
```

---

## 📊 Expected Performance

| Metric | Python Baseline | Rust Target | Improvement |
|--------|----------------|-------------|-------------|
| Simple MATCH P95 | ~130ms | <15ms | **8-10x** |
| Graph Traversal P95 | ~480ms | <50ms | **9-10x** |
| Throughput | 50 req/sec | 500+ req/sec | **10x** |

---

## 🏗️ Project Structure

```
graphops/
├── .env.example          # Template for credentials
├── env.sh                # Shell script to source
├── src/
│   ├── lib.rs            # Public API exports
│   ├── main.rs           # gRPC + metrics entrypoint
│   ├── service.rs        # tonic service implementation
│   ├── metrics.rs        # Prometheus registry helpers
│   ├── db/
│   │   └── connection.rs # PgBouncer-aware connection factory
│   ├── handlers/
│   │   └── cypher.rs     # Apache AGE Cypher executor
│   └── bin/
│       └── graphops_cli.rs  # CLI client exercising all RPCs
├── benches/
│   └── graphops_benchmark.rs  # Criterion benchmarks
└── benchmarks/
    └── python_graphops_baseline.py  # Python comparison
```

---

## 🔧 Configuration

All configuration is via environment variables:

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | ✅ | - | PostgreSQL connection string (via PgBouncer) |
| `GRAPHOPS_GRAPH` | ✅ | `graph` | Apache AGE graph name |
| `GRAPHOPS_PY_ITERATIONS` | ❌ | `10` | Python benchmark iterations |
| `RUST_LOG` | ❌ | `info` | Rust logging level |

---

## 🧪 Testing

```bash
# All tests
cargo test

# With output
cargo test -- --nocapture

# Specific test
cargo test db_connection_test -- --nocapture
```

---

## 📈 Benchmarking

```bash
# Run Rust benchmarks
cargo bench

# Run Python baseline
conda run -n nina python benchmarks/python_graphops_baseline.py

# Generate comparison report
./compare_performance.sh
```

---

## 🔍 Troubleshooting

### "DATABASE_URL not set"
- Create `.env` file from `.env.example`
- Or source `env.sh`

### "database does not exist"
- Database name is `ninaivalaigal_dev` (not `nina`)
- Check `DATABASE_URL` in `.env`

### "function cypher(unknown, unknown) does not exist"
- Apache AGE extension needs initialization
- Handled automatically in `DbPool::get_client()`
- Graph name must be `ninaivalaigal_intelligence`

### Benchmark fails with AGE error
- Ensure `.env` has correct credentials
- Verify graph exists: `SELECT * FROM ag_catalog.ag_graph;`

---

## 📚 Dependencies

- **tokio-postgres**: Async PostgreSQL driver
- **tonic**: gRPC framework (for future gRPC service)
- **criterion**: Benchmarking framework
- **dotenvy**: Automatic .env file loading
- **serde_json**: JSON serialization for AGType results

---

## 🎯 Next Steps

1. ✅ Basic Cypher executor
2. ✅ Benchmark suite
3. ✅ Python baseline comparison
4. ✅ gRPC service layer
5. ✅ Contract integration (Protocol Buffers)
6. 🚧 Production deployment

---

**Part of SPEC-099: Rust Migration Strategy & ROI Analysis**

## 🔌 gRPC Endpoint Guide

Use the generated CLI or `grpcurl` to exercise the service.

```bash
# Health check
grpcurl -plaintext -import-path shared/contracts -proto graphops/v1/graphops.proto \
    localhost:50051 ninaivalaigal.graphops.v1.GraphOpsService/HealthCheck

# Execute a simple query
grpcurl -plaintext -d '{"query":"MATCH (n) RETURN n LIMIT 1"}' \
    localhost:50051 ninaivalaigal.graphops.v1.GraphOpsService/ExecuteQuery
```

`cargo run --bin graphops_cli -- --help` lists pre-baked flows that hit every RPC in one command.

## 📊 Metrics & Monitoring

- Scrape Prometheus metrics: `curl -s http://localhost:9090/metrics | grep graphops_`
- Live monitoring loop: `./scripts/monitor-query-performance.sh`
- Metrics include latency histogram, request totals, cache warmers, DB connection gauge, and memory usage.

Health probe is available at `http://localhost:9090/health` for container orchestration checks.

## 📘 Further Reading

- `ARCHITECTURE.md` — service topology, data flow, and observability design.
- `PERFORMANCE_FIXES.md` — current optimization state and benchmark methodology.
