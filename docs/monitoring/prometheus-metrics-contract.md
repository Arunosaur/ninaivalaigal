# Prometheus Metrics Contract for GraphOps

**SPEC-099 Phase 1: Metrics Integration**
**Owner**: Developer A (Implementation) / Developer C (Dashboard)

## Overview

This document defines the exact metric names, types, and labels required for the Grafana dashboard integration. All metrics MUST use these exact names to ensure dashboard compatibility.

## Required Metrics

### 1. Request Duration Histogram

**Name**: `graphops_request_duration_seconds`
**Type**: Histogram
**Unit**: Seconds
**Description**: Latency distribution of GraphOps requests

**Labels**:
- `runtime`: `"rust"` or `"python"` (for comparison)
- `operation`: RPC method name (`"ExecuteQuery"`, `"ExecuteQueryBatch"`, etc.)
- `status`: `"success"` or `"error"`

**Buckets**: Use default Prometheus buckets or:
```rust
[0.001, 0.0025, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
```

**Example**:
```rust
use prometheus::{Histogram, HistogramOpts, register_histogram};

let request_duration = register_histogram!(
    "graphops_request_duration_seconds",
    "GraphOps request latency in seconds",
    vec![0.001, 0.0025, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0]
).unwrap();

// Usage
let timer = request_duration.start_timer();
// ... execute query ...
timer.observe_duration();
```

### 2. Total Requests Counter

**Name**: `graphops_requests_total`
**Type**: Counter
**Unit**: Requests
**Description**: Total number of GraphOps requests

**Labels**:
- `runtime`: `"rust"` or `"python"`
- `operation`: RPC method name
- `status`: `"success"` or `"error"`

**Example**:
```rust
use prometheus::{IntCounter, register_int_counter_vec};

let requests_total = register_int_counter_vec!(
    "graphops_requests_total",
    "Total GraphOps requests",
    &["runtime", "operation", "status"]
).unwrap();

// Usage
requests_total
    .with_label_values(&["rust", "ExecuteQuery", "success"])
    .inc();
```

### 3. Cache Hit Counter

**Name**: `graphops_cache_hits_total`
**Type**: Counter
**Unit**: Hits
**Description**: Number of cache hits (query results cached)

**Labels**:
- `runtime`: `"rust"` or `"python"`
- `cache_type`: `"query"`, `"metadata"`, etc.

**Example**:
```rust
let cache_hits = register_int_counter_vec!(
    "graphops_cache_hits_total",
    "GraphOps cache hits",
    &["runtime", "cache_type"]
).unwrap();

// Usage
cache_hits
    .with_label_values(&["rust", "query"])
    .inc();
```

### 4. Database Connections Gauge

**Name**: `graphops_db_connections_active`
**Type**: Gauge
**Unit**: Connections
**Description**: Number of active database connections

**Labels**:
- `runtime`: `"rust"` or `"python"`
- `pool`: `"primary"` or pool identifier

**Example**:
```rust
use prometheus::{IntGauge, register_int_gauge_vec};

let db_connections = register_int_gauge_vec!(
    "graphops_db_connections_active",
    "Active database connections",
    &["runtime", "pool"]
).unwrap();

// Usage
db_connections
    .with_label_values(&["rust", "primary"])
    .set(active_count as i64);
```

### 5. Error Counter

**Name**: `graphops_errors_total`
**Type**: Counter
**Unit**: Errors
**Description**: Total errors by type

**Labels**:
- `runtime`: `"rust"` or `"python"`
- `error_type`: `"timeout"`, `"connection"`, `"query_syntax"`, `"internal"`, etc.
- `operation`: RPC method name

**Example**:
```rust
let errors_total = register_int_counter_vec!(
    "graphops_errors_total",
    "Total errors by type",
    &["runtime", "error_type", "operation"]
).unwrap();

// Usage
errors_total
    .with_label_values(&["rust", "timeout", "ExecuteQuery"])
    .inc();
```

## Optional But Recommended Metrics

### 6. Memory Usage Gauge

**Name**: `graphops_memory_bytes`
**Type**: Gauge
**Unit**: Bytes
**Description**: Current memory usage (RSS)

**Labels**:
- `runtime`: `"rust"` or `"python"`
- `type`: `"rss"`, `"heap"`, `"virtual"`

### 7. Query Planning Time Histogram

**Name**: `graphops_query_planning_seconds`
**Type**: Histogram
**Unit**: Seconds
**Description**: Time spent in query planning (from EXPLAIN ANALYZE)

**Labels**:
- `runtime`: `"rust"`

### 8. Query Execution Time Histogram

**Name**: `graphops_query_execution_seconds`
**Type**: Histogram
**Unit**: Seconds
**Description**: Time spent in query execution (from EXPLAIN ANALYZE)

**Labels**:
- `runtime`: `"rust"`

## Prometheus-Client Integration

### Recommended Crate Setup

```toml
[dependencies]
prometheus = { version = "0.13", features = ["process"] }
```

### Registry Setup

```rust
use prometheus::{Registry, TextEncoder, Encoder};

pub struct MetricsRegistry {
    registry: Registry,
    request_duration: Histogram,
    requests_total: IntCounterVec,
    cache_hits: IntCounterVec,
    db_connections: IntGaugeVec,
    errors_total: IntCounterVec,
}

impl MetricsRegistry {
    pub fn new() -> Self {
        let registry = Registry::new();

        let request_duration = Histogram::with_opts(
            HistogramOpts::new(
                "graphops_request_duration_seconds",
                "GraphOps request latency in seconds"
            ).buckets(vec![0.001, 0.0025, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0])
        ).unwrap();
        registry.register(Box::new(request_duration.clone())).unwrap();

        // ... register other metrics ...

        Self {
            registry,
            request_duration,
            // ... other fields ...
        }
    }

    pub fn gather_metrics(&self) -> String {
        let encoder = TextEncoder::new();
        let metric_families = self.registry.gather();
        let mut buffer = Vec::new();
        encoder.encode(&metric_families, &mut buffer).unwrap();
        String::from_utf8(buffer).unwrap()
    }
}
```

### gRPC Service Integration

```rust
// In your GetMetrics RPC implementation
impl GraphOpsService for MyService {
    async fn get_metrics(
        &self,
        request: Request<MetricsRequest>,
    ) -> Result<Response<MetricsResponse>, Status> {
        let window_seconds = request.get_ref().window_seconds;

        // Get Prometheus metrics
        let prom_metrics = self.metrics_registry.gather_metrics();

        // Build response (you can parse prom metrics or maintain separate counters)
        let response = MetricsResponse {
            total_queries: self.get_query_count(window_seconds),
            successful_queries: self.get_success_count(window_seconds),
            failed_queries: self.get_failure_count(window_seconds),
            p50_latency_ms: self.get_percentile(0.50),
            p95_latency_ms: self.get_percentile(0.95),
            p99_latency_ms: self.get_percentile(0.99),
            avg_execution_time_ms: self.get_avg_latency(),
            memory_usage_bytes: self.get_memory_usage(),
            active_connections: self.get_active_connections(),
        };

        Ok(Response::new(response))
    }
}
```

## Metrics Endpoint

**Path**: `/metrics`
**Format**: Prometheus text format
**Method**: GET

**Example Response**:
```
# HELP graphops_request_duration_seconds GraphOps request latency in seconds
# TYPE graphops_request_duration_seconds histogram
graphops_request_duration_seconds_bucket{runtime="rust",operation="ExecuteQuery",status="success",le="0.001"} 145
graphops_request_duration_seconds_bucket{runtime="rust",operation="ExecuteQuery",status="success",le="0.0025"} 234
graphops_request_duration_seconds_bucket{runtime="rust",operation="ExecuteQuery",status="success",le="0.005"} 345
...
graphops_request_duration_seconds_sum{runtime="rust",operation="ExecuteQuery",status="success"} 12.456
graphops_request_duration_seconds_count{runtime="rust",operation="ExecuteQuery",status="success"} 456

# HELP graphops_requests_total Total GraphOps requests
# TYPE graphops_requests_total counter
graphops_requests_total{runtime="rust",operation="ExecuteQuery",status="success"} 456
graphops_requests_total{runtime="rust",operation="ExecuteQuery",status="error"} 12

# HELP graphops_cache_hits_total GraphOps cache hits
# TYPE graphops_cache_hits_total counter
graphops_cache_hits_total{runtime="rust",cache_type="query"} 234

# HELP graphops_db_connections_active Active database connections
# TYPE graphops_db_connections_active gauge
graphops_db_connections_active{runtime="rust",pool="primary"} 8

# HELP graphops_errors_total Total errors by type
# TYPE graphops_errors_total counter
graphops_errors_total{runtime="rust",error_type="timeout",operation="ExecuteQuery"} 3
graphops_errors_total{runtime="rust",error_type="connection",operation="ExecuteQuery"} 2
```

## Grafana Dashboard Queries

The dashboard uses these PromQL queries:

### Request Latency P50/P95/P99
```promql
histogram_quantile(0.50, rate(graphops_request_duration_seconds_bucket{runtime="rust"}[5m]))
histogram_quantile(0.95, rate(graphops_request_duration_seconds_bucket{runtime="rust"}[5m]))
histogram_quantile(0.99, rate(graphops_request_duration_seconds_bucket{runtime="rust"}[5m]))
```

### Throughput (Requests/sec)
```promql
rate(graphops_requests_total{runtime="rust"}[1m])
```

### Cache Hit Rate
```promql
rate(graphops_cache_hits_total{runtime="rust"}[5m]) / rate(graphops_requests_total{runtime="rust"}[5m]) * 100
```

### Database Connections
```promql
graphops_db_connections_active{runtime="rust"}
```

### Error Rate
```promql
rate(graphops_errors_total{runtime="rust"}[5m])
```

## Testing Metrics Integration

```bash
# Start your service
cargo run --release

# Check metrics endpoint
curl http://localhost:9090/metrics

# Verify metric names match this spec
curl http://localhost:9090/metrics | grep graphops_

# Test with Prometheus locally
docker run -d -p 9090:9090 \
  -v $(pwd)/prometheus.yml:/etc/prometheus/prometheus.yml \
  prom/prometheus

# View in Grafana
docker run -d -p 3000:3000 grafana/grafana
# Import monitoring/grafana-dashboards/graphops-performance.json
```

## Day 4 Validation Checklist

- [ ] All 4 required metrics exposed at `/metrics`
- [ ] Metric names match exactly (no typos!)
- [ ] Labels include `runtime="rust"`
- [ ] Histogram buckets cover expected latency range
- [ ] Grafana dashboard displays data correctly
- [ ] PromQL queries return expected results

## References

- Prometheus Client Rust: https://docs.rs/prometheus/latest/prometheus/
- Prometheus Text Format: https://prometheus.io/docs/instrumenting/exposition_formats/
- Grafana Dashboard: `monitoring/grafana-dashboards/graphops-performance.json`

---

**Questions**: Contact Developer C if metric names need adjustment
