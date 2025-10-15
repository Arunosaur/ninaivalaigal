# GraphOps Rust Service - Deployment Guide

**SPEC-099 Phase 0: Contract Definition & DevOps Infrastructure**

This guide covers the deployment of the high-performance Rust GraphOps service for Apache AGE Cypher query execution.

## Prerequisites

- Container runtime (Docker or Apple Container CLI)
- PostgreSQL 15+ with Apache AGE extension
- Redis (optional, for caching)
- gRPC client tools (grpcurl recommended)

## Configuration

### Environment Variables

```bash
# Database Connection
DATABASE_URL="postgresql://user:pass@host:5432/database"  # pragma: allowlist secret
DB_POOL_SIZE=10

# Service Configuration
GRPC_PORT=50051
LOG_LEVEL=info
RUST_LOG=graphops=debug

# Performance Tuning
QUERY_TIMEOUT_MS=5000
MAX_CONCURRENT_REQUESTS=1000

# Monitoring
PROMETHEUS_PORT=9090
ENABLE_TRACING=true
JAEGER_ENDPOINT=http://localhost:14268/api/traces
```

## Local Development

### Build the Service

```bash
# Using the build script (auto-detects architecture)
./scripts/build-graphops-rust.sh

# Or manually with container CLI
container build \
  --platform linux/arm64 \
  -t graphops-rust:arm64 \
  -f containers/graphops-rust/Dockerfile \
  .

# Or with Docker
docker build \
  --platform linux/amd64 \
  -t graphops-rust:amd64 \
  -f containers/graphops-rust/Dockerfile \
  .
```

### Run the Service

```bash
# Using container CLI (Apple Container CLI)
container run -d \
  --name graphops-rust \
  -p 50051:50051 \
  -p 9090:9090 \
  -e DATABASE_URL="$DATABASE_URL" \
  -e LOG_LEVEL=debug \
  graphops-rust:arm64

# Using Docker
docker run -d \
  --name graphops-rust \
  -p 50051:50051 \
  -p 9090:9090 \
  -e DATABASE_URL="$DATABASE_URL" \
  -e LOG_LEVEL=debug \
  graphops-rust:amd64
```

### Health Check

```bash
# gRPC health check using grpcurl
grpcurl -plaintext localhost:50051 ninaivalaigal.graphops.v1.GraphOpsService/HealthCheck

# Expected response:
# {
#   "status": "HEALTH_STATUS_HEALTHY",
#   "database": {
#     "name": "database",
#     "status": "HEALTH_STATUS_HEALTHY"
#   },
#   "ageExtension": {
#     "name": "age_extension",
#     "status": "HEALTH_STATUS_HEALTHY"
#   },
#   "uptimeSeconds": "120",
#   "version": "0.1.0"
# }
```

### Testing Queries

```bash
# Execute a simple Cypher query
grpcurl -plaintext -d '{
  "query": "MATCH (n:User) RETURN n LIMIT 5",
  "timeout_ms": 5000,
  "trace_id": "test-001"
}' localhost:50051 ninaivalaigal.graphops.v1.GraphOpsService/ExecuteQuery

# Batch query execution
grpcurl -plaintext -d '{
  "queries": [
    {"query": "MATCH (n:User) RETURN count(n)"},
    {"query": "MATCH (n:Memory) RETURN count(n)"}
  ],
  "fail_fast": false
}' localhost:50051 ninaivalaigal.graphops.v1.GraphOpsService/ExecuteQueryBatch
```

## Performance Benchmarking

### Rust Benchmarks

```bash
# Navigate to Rust service directory
cd rust-services/graphops

# Run benchmarks with Criterion
cargo bench

# Results will be in target/criterion/
```

### Comparison with Python

```bash
# Run Python baseline benchmarks
python3 benchmarks/python_graphops_baseline.py

# Run Rust benchmarks
cd rust-services/graphops && cargo bench

# Compare results
./scripts/compare-performance.sh
```

### Expected Performance Targets

- **Latency P95**: < 10ms (Rust) vs < 50ms (Python)
- **Throughput**: 10,000+ req/s (Rust) vs 1,000+ req/s (Python)
- **Memory Usage**: 50MB (Rust) vs 200MB (Python)
- **CPU Efficiency**: 5-10x improvement with Rust

## Monitoring

### Prometheus Metrics

The service exposes metrics at `http://localhost:9090/metrics`:

**Key Metrics:**
- `graphops_request_duration_seconds` - Request latency histogram
- `graphops_requests_total` - Total requests counter (by status)
- `graphops_cache_hits_total` - Cache hits counter
- `graphops_db_connections_active` - Active database connections
- `graphops_errors_total` - Total errors counter (by type)

### Grafana Dashboard

Import the pre-configured dashboard:

```bash
# Dashboard location
monitoring/grafana-dashboards/graphops-performance.json

# Features:
# - Request latency P50/P95/P99 comparison
# - Throughput comparison (Rust vs Python)
# - Cache hit rate monitoring
# - Database connection pooling metrics
# - Error rate tracking
```

### Distributed Tracing

Enable OpenTelemetry tracing:

```bash
# Set environment variables
export ENABLE_TRACING=true
export JAEGER_ENDPOINT=http://localhost:14268/api/traces

# View traces in Jaeger UI
open http://localhost:16686
```

## Production Deployment

### Using Docker Compose

```yaml
version: '3.8'

services:
  graphops-rust:
    image: graphops-rust:arm64
    container_name: graphops-rust
    ports:
      - "50051:50051"
      - "9090:9090"
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres:5432/ninaivalaigal  # pragma: allowlist secret
      - GRPC_PORT=50051
      - LOG_LEVEL=info
      - DB_POOL_SIZE=20
    depends_on:
      - postgres
    restart: unless-stopped
    healthcheck:
      test: ["/app/graphops-service", "--health-check"]
      interval: 30s
      timeout: 3s
      retries: 3
```

### Using Kubernetes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: graphops-rust
  namespace: ninaivalaigal
spec:
  replicas: 3
  selector:
    matchLabels:
      app: graphops-rust
  template:
    metadata:
      labels:
        app: graphops-rust
    spec:
      containers:
      - name: graphops
        image: graphops-rust:arm64
        ports:
        - containerPort: 50051
          name: grpc
        - containerPort: 9090
          name: metrics
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: graphops-secrets
              key: database-url
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          exec:
            command: ["/app/graphops-service", "--health-check"]
          initialDelaySeconds: 5
          periodSeconds: 30
        readinessProbe:
          exec:
            command: ["/app/graphops-service", "--health-check"]
          initialDelaySeconds: 5
          periodSeconds: 10
```

## Troubleshooting

### Container Won't Start

```bash
# Check logs
container logs graphops-rust
# or
docker logs graphops-rust

# Verify database connection
psql $DATABASE_URL -c "SELECT version();"

# Check Apache AGE extension
psql $DATABASE_URL -c "SELECT * FROM pg_extension WHERE extname = 'age';"
```

### gRPC Connection Refused

```bash
# Verify port is exposed
netstat -an | grep 50051

# Test with grpcurl
grpcurl -plaintext localhost:50051 list

# Check firewall rules
sudo ufw status
```

### Performance Issues

```bash
# Check resource usage
container stats graphops-rust

# Monitor database connections
psql $DATABASE_URL -c "SELECT count(*) FROM pg_stat_activity;"

# Review query performance
grpcurl -plaintext localhost:50051 ninaivalaigal.graphops.v1.GraphOpsService/GetMetrics
```

### Memory Leaks

```bash
# Enable memory profiling
export RUST_LOG=graphops=debug

# Monitor memory usage over time
watch -n 5 'container stats graphops-rust --no-stream'

# Check for connection pool exhaustion
grpcurl -plaintext localhost:50051 ninaivalaigal.graphops.v1.GraphOpsService/GetMetrics
```

## Production Rollout Strategy

See [SPEC-099](../../specs/099-rust-migration-strategy/README.md) for the complete production rollout strategy:

1. **Phase 0** (Current): Contract definition & infrastructure setup
2. **Phase 1**: Implement core Rust service with feature parity
3. **Phase 2**: Validate performance with 10% traffic shadow mode
4. **Phase 3**: Gradual rollout (10% → 50% → 100%)
5. **Phase 4**: Retire Python implementation

## Support

For issues and questions:
- GitHub Issues: https://github.com/Arunosaur/ninaivalaigal/issues
- SPEC-099 Documentation: specs/099-rust-migration-strategy/
- Developer C: Primary contact for GraphOps infrastructure

## References

- [SPEC-099: Rust Migration Strategy](../../specs/099-rust-migration-strategy/README.md)
- [SPEC-100: GraphOps Performance Baseline](../../specs/100-graphops-baseline/README.md)
- [gRPC Contract Definition](../../shared/contracts/graphops/v1/graphops.proto)
- [Apache AGE Documentation](https://age.apache.org/)
