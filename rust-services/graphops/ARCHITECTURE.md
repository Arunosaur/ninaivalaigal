# GraphOps Rust Service Architecture

_Last updated: 2025-10-15_

## 1. Overview

The GraphOps Rust service is the production path for executing Apache AGE Cypher queries via a tonic-based gRPC API. A lightweight Hyper HTTP server exposes Prometheus metrics and a JSON health probe so the service can be scraped and monitored independently of the gRPC transport.

```
+------------------+        gRPC         +------------------+        PostgreSQL / AGE
| Client (gRPC/CLI)|  ───────────────▶   | GraphOps Service |  ────────────────▶  PgBouncer
+------------------+                    +------------------+                       │
        ▲                                         │                              │
        │            Prometheus scrape            │                              ▼
        └───────────────◀─────────────────────────┘                     PostgreSQL + AGE
```

Key properties:
- Runs as a single Tokio runtime handling both gRPC and metrics endpoints.
- Delegates connection pooling to PgBouncer; the service only opens short-lived logical clients.
- Instruments every request with Prometheus counters, histograms, and gauges required by the shared dashboards.

## 2. Runtime Topology

| Endpoint | Purpose | Implementation |
|----------|---------|----------------|
| `0.0.0.0:50051` | gRPC requests | `tonic::transport::Server` hosting `GraphOpsServiceServer` |
| `0.0.0.0:9090/metrics` | Prometheus scrape | `hyper::Server` with `handle_metrics_request` |
| `0.0.0.0:9090/health` | JSON health probe | Same Hyper server, distinct route |

Both servers are launched inside the `tokio::select!` block in `src/main.rs`, so either failure path will bubble out and terminate the process. Tracing logs are emitted through `tracing_subscriber::fmt` with `RUST_LOG` control.

## 3. Core Components

### 3.1 gRPC Service (`src/service.rs`)
- Implements all RPCs from `graphops.proto`: `ExecuteQuery`, `ExecuteQueryBatch`, `HealthCheck`, and `GetMetrics`.
- Each handler starts a `RequestTimer` to feed latency data into the `graphops_request_duration_seconds` histogram.
- Validates requests (empty query, unsupported parameters) up front and translates failures into protobuf `ErrorDetails`.
- Tracks active database clients via the `graphops_db_connections_active` gauge so PgBouncer load can be inspected in Grafana.
- Batches reuse `ExecuteQuery` internally, allowing consistent validation and metrics accounting.

### 3.2 Database Access (`src/db/connection.rs`)
- `DbPool` wraps a parsed `tokio_postgres::Config` so each request can clone it and open a fresh client.
- The driver task is spawned per connection to satisfy tokio-postgres contract without blocking the main thread.
- Every client lazily loads the AGE extension and adjusts the search_path so Cypher calls work out of the box.
- PgBouncer is expected to run in front of Postgres; application name tagging (`graphops-service`) ensures visibility in `pg_stat_activity`.

### 3.3 Cypher Execution (`src/handlers/cypher.rs`)
- `CypherExecutor` builds the AGE SQL wrapper and currently issues it with `simple_query`.
- Results are streamed row by row, trimmed of the `::vertex`/`::edge` suffix, deserialized into `serde_json::Value`, and surfaced as strings to clients.
- Phase 1 work will swap to the extended protocol (`Client::query`) to reduce wire overhead once PgBouncer compatibility improvements land.

### 3.4 Metrics Registry (`src/metrics.rs`)
- Registers six required Prometheus series:
  - `graphops_request_duration_seconds`
  - `graphops_requests_total`
  - `graphops_cache_hits_total`
  - `graphops_db_connections_active`
  - `graphops_errors_total`
  - `graphops_memory_bytes`
- Provides `RequestTimer` helper and `update_memory_metrics` hook called before every metrics scrape.
- Uses `sysinfo` to report resident set size so dashboards can alarm on memory growth.

## 4. Request Lifecycle

1. Client invokes gRPC method via tonic-generated stub.
2. Service clones the PgBouncer-backed config and obtains a short-lived Postgres client.
3. `CypherExecutor` runs the query against AGE, deserializes the AGType records, and returns JSON payloads.
4. Metrics counters, gauges, and histogram buckets are updated based on success or failure.
5. Response is returned to client with execution time, row counts, and optional error metadata.

Error paths update both `graphops_requests_total{status="error"}` and `graphops_errors_total` with contextual labels so the Grafana dashboards can differentiate connection failures from query issues.

## 5. Configuration Surface

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | _required_ | PgBouncer connection string used by `DbPool` |
| `GRAPHOPS_GRAPH` | `ninaivalaigal_intelligence` | Apache AGE graph name fed into `CypherExecutor` |
| `GRAPHOPS_GRPC_ADDR` | `0.0.0.0:50051` | Bind address for gRPC server |
| `GRAPHOPS_METRICS_ADDR` | `0.0.0.0:9090` | Bind address for metrics/health server |
| `RUST_LOG` | `info` | Standard tracing filter |

Credentials are typically provided via `.env` loaded by `dotenvy` (see README Quick Start).

## 6. Observability & Operations

- **Metrics**: Prometheus scrape verifies counters increment for every RPC and load test. Cache hit counter is incremented with zero to keep the series present even before cache integration.
- **Health**: `/health` returns JSON without hitting the database; gRPC `HealthCheck` performs a real client acquisition to confirm connectivity.
- **Logging**: Structured tracing spans include `trace_id` where available. Errors are logged with context and mirrored into Prometheus error counters.
- **Monitoring Scripts**: `scripts/monitor-query-performance.sh` tails metrics locally while load generators (`graphops_cli`, `grpcurl`) exercise RPCs.

## 7. Production Considerations

- PgBouncer must be in transaction pooling mode so each logical client can issue AGE `simple_query` calls safely.
- The service is stateless; horizontal scaling is achieved by running multiple instances behind an L4 load balancer.
- Resource sizing should budget for the Hyper HTTP listener and the tonic gRPC server within a single Tokio runtime.
- Metric histogram buckets were selected to capture sub-100ms latencies targeted for Phase 1.

## 8. Roadmap Notes

- Swap to extended protocol queries once PgBouncer configuration supports unnamed prepared statements to reduce latency volatility.
- Add histogram quantile export and propagate `p50/p95/p99` into `MetricsResponse` for richer client telemetry.
- Extend `CypherExecutor` to support parameterized queries and reuse execution plans once cache support lands.
- Integrate OpenTelemetry tracing (tonic + Hyper) to correlate requests across services.

---

_For questions or changes, contact Developer A (Phase 0 maintainer)._
