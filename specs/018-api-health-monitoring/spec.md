# SPEC-018: API Health & Monitoring

## Overview

This specification defines the comprehensive health monitoring and diagnostics system for ninaivalaigal API, providing detailed health endpoints, SLO monitoring, performance metrics, and operational observability for production and development environments.

## Motivation

- **Operational Visibility**: Real-time insight into API health and performance
- **SLO Compliance**: Service Level Objective monitoring and alerting
- **Proactive Monitoring**: Early detection of performance degradation and issues
- **Debugging Support**: Detailed diagnostics for troubleshooting
- **Production Readiness**: Enterprise-grade health monitoring capabilities

## Specification

### 1. Health Endpoint Architecture

#### 1.1 Health Endpoint Hierarchy
```
/health                 # Basic health check (200 OK)
├── /health/detailed    # Comprehensive system status
├── /health/ready       # Readiness probe (K8s compatible)
├── /health/live        # Liveness probe (K8s compatible)
└── /memory/health      # Memory provider specific health
```

#### 1.2 Health Check Categories
```yaml
System Health:
  - API Server: FastAPI application status
  - Database: PostgreSQL connectivity and performance
  - Memory Provider: Memory substrate health
  - Dependencies: External service connectivity

Performance Health:
  - Response Times: P50, P95, P99 latencies
  - Throughput: Requests per second
  - Error Rates: 4xx and 5xx error percentages
  - Resource Usage: CPU, memory, disk utilization
```

### 2. Basic Health Endpoint

#### 2.1 GET /health
```json
Purpose: Simple health check for load balancers and basic monitoring
Response Time: < 10ms target
Status Codes:
  - 200: Service is healthy
  - 503: Service is unhealthy

Response Format:
{
  "status": "healthy",
  "timestamp": "2024-01-20T10:30:00Z",
  "version": "1.0.0"
}
```

#### 2.2 Implementation Requirements
```python
@router.get("/health")
async def health_check():
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "version": get_version()
    }
```

### 3. Detailed Health Endpoint

#### 3.1 GET /health/detailed
```json
Purpose: Comprehensive system diagnostics
Response Time: < 250ms target (SLO compliant)
Authentication: Optional (configurable)

Response Format:
{
  "status": "healthy",
  "timestamp": "2024-01-20T10:30:00Z",
  "version": "1.0.0",
  "uptime": "2d 14h 32m 15s",
  "environment": "production",
  "components": {
    "database": {
      "status": "healthy",
      "response_time_ms": 12,
      "connections": {
        "active": 3,
        "idle": 7,
        "max": 100
      },
      "last_check": "2024-01-20T10:29:55Z"
    },
    "memory_provider": {
      "status": "healthy",
      "provider": "PostgresMemoryProvider",
      "response_time_ms": 8,
      "last_check": "2024-01-20T10:29:58Z"
    }
  },
  "metrics": {
    "requests_total": 15420,
    "requests_per_second": 12.5,
    "error_rate_percent": 0.02,
    "avg_response_time_ms": 45
  },
  "slo_compliance": {
    "availability_percent": 99.98,
    "p95_response_time_ms": 89,
    "error_rate_percent": 0.02,
    "target_met": true
  }
}
```

#### 3.2 Component Health Checks
```python
Database Health Check:
  - Connection test: SELECT 1
  - Response time measurement
  - Connection pool status
  - Query performance metrics

Memory Provider Health Check:
  - Provider availability test
  - Response time measurement
  - Storage backend connectivity
  - Operation success rates
```

### 4. Kubernetes-Compatible Probes

#### 4.1 GET /health/ready (Readiness Probe)
```json
Purpose: Kubernetes readiness probe
Criteria: Service ready to accept traffic
Checks:
  - Database connectivity
  - Memory provider availability
  - Critical dependencies

Response:
{
  "ready": true,
  "checks": {
    "database": "pass",
    "memory_provider": "pass"
  }
}
```

#### 4.2 GET /health/live (Liveness Probe)
```json
Purpose: Kubernetes liveness probe
Criteria: Service is alive and should not be restarted
Checks:
  - Basic application responsiveness
  - Critical system resources
  - Deadlock detection

Response:
{
  "alive": true,
  "checks": {
    "application": "pass",
    "resources": "pass"
  }
}
```

### 5. Memory Provider Health

#### 5.1 GET /memory/health
```json
Purpose: Memory substrate specific health monitoring
Provider Types: Native (PostgreSQL) or HTTP (mem0)

Native Provider Response:
{
  "healthy": true,
  "provider": "PostgresMemoryProvider",
  "database_connection": "healthy",
  "response_time_ms": 8,
  "operations": {
    "remember": "healthy",
    "recall": "healthy",
    "list_memories": "healthy"
  },
  "storage": {
    "total_memories": 1247,
    "storage_size_mb": 45.2
  }
}

HTTP Provider Response:
{
  "healthy": true,
  "provider": "Mem0HttpMemoryProvider",
  "endpoint": "http://localhost:8001",
  "response_time_ms": 15,
  "authentication": "valid",
  "operations": {
    "remember": "healthy",
    "recall": "healthy",
    "list_memories": "healthy"
  }
}
```

### 6. Performance Metrics Integration

#### 6.1 Prometheus Metrics Endpoint
```
GET /metrics

# HELP ninaivalaigal_requests_total Total number of requests
# TYPE ninaivalaigal_requests_total counter
ninaivalaigal_requests_total{method="GET",endpoint="/health"} 1247

# HELP ninaivalaigal_request_duration_seconds Request duration
# TYPE ninaivalaigal_request_duration_seconds histogram
ninaivalaigal_request_duration_seconds_bucket{le="0.1"} 1200
ninaivalaigal_request_duration_seconds_bucket{le="0.25"} 1245
ninaivalaigal_request_duration_seconds_bucket{le="0.5"} 1247

# HELP ninaivalaigal_database_connections Database connections
# TYPE ninaivalaigal_database_connections gauge
ninaivalaigal_database_connections{state="active"} 3
ninaivalaigal_database_connections{state="idle"} 7
```

#### 6.2 Health Metrics Collection
```python
Health Check Metrics:
  - Health check response times
  - Health check success/failure rates
  - Component availability percentages
  - SLO compliance tracking
```

### 7. SLO (Service Level Objective) Monitoring

#### 7.1 SLO Definitions
```yaml
Availability SLO:
  Target: 99.9% uptime
  Measurement: Successful health checks / Total health checks
  Window: 30-day rolling window

Response Time SLO:
  Target: P95 < 200ms for /health/detailed
  Measurement: 95th percentile response time
  Window: 24-hour rolling window

Error Rate SLO:
  Target: < 0.1% error rate
  Measurement: 5xx errors / Total requests
  Window: 24-hour rolling window
```

#### 7.2 SLO Compliance Reporting
```json
{
  "slo_compliance": {
    "availability": {
      "target_percent": 99.9,
      "actual_percent": 99.98,
      "status": "compliant",
      "window": "30d"
    },
    "response_time": {
      "target_p95_ms": 200,
      "actual_p95_ms": 89,
      "status": "compliant",
      "window": "24h"
    },
    "error_rate": {
      "target_percent": 0.1,
      "actual_percent": 0.02,
      "status": "compliant",
      "window": "24h"
    }
  }
}
```

### 8. Alerting Integration

#### 8.1 Alert Conditions
```yaml
Critical Alerts:
  - Health check failures > 3 consecutive
  - Database connectivity lost
  - Memory provider unavailable
  - P95 response time > 500ms

Warning Alerts:
  - P95 response time > 200ms
  - Error rate > 0.1%
  - Database connection pool > 80% utilization
  - Memory usage > 80%
```

#### 8.2 Alert Payload Format
```json
{
  "alert": "health_check_failure",
  "severity": "critical",
  "service": "ninaivalaigal-api",
  "component": "database",
  "message": "Database health check failed",
  "timestamp": "2024-01-20T10:30:00Z",
  "details": {
    "error": "Connection timeout",
    "response_time_ms": 5000,
    "consecutive_failures": 3
  }
}
```

## Implementation

### 1. FastAPI Router Integration
```python
# server/health_router.py
from fastapi import APIRouter, HTTPException
from datetime import datetime
import asyncio

router = APIRouter(prefix="/health", tags=["health"])

@router.get("/")
async def basic_health():
    return {"status": "healthy", "timestamp": datetime.utcnow()}

@router.get("/detailed")
async def detailed_health():
    # Comprehensive health checks
    pass

@router.get("/ready")
async def readiness_probe():
    # Kubernetes readiness probe
    pass

@router.get("/live")
async def liveness_probe():
    # Kubernetes liveness probe
    pass
```

### 2. Health Check Framework
```python
# server/health_checks.py
class HealthChecker:
    async def check_database(self) -> HealthResult:
        # Database connectivity and performance check
        pass

    async def check_memory_provider(self) -> HealthResult:
        # Memory provider health check
        pass

    async def aggregate_health(self) -> SystemHealth:
        # Aggregate all component health checks
        pass
```

### 3. Metrics Collection
```python
# server/metrics.py
from prometheus_client import Counter, Histogram, Gauge

health_check_counter = Counter(
    'ninaivalaigal_health_checks_total',
    'Total health checks performed',
    ['endpoint', 'status']
)

health_check_duration = Histogram(
    'ninaivalaigal_health_check_duration_seconds',
    'Health check response time'
)
```

## Testing Strategy

### 1. Health Endpoint Testing
```python
# Test basic health endpoint
def test_basic_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

# Test detailed health endpoint
def test_detailed_health():
    response = client.get("/health/detailed")
    assert response.status_code == 200
    assert "components" in response.json()
    assert "slo_compliance" in response.json()
```

### 2. Component Health Testing
```python
# Test database health check
def test_database_health():
    # Mock database failure
    # Verify health endpoint reflects failure
    pass

# Test memory provider health check
def test_memory_provider_health():
    # Mock memory provider failure
    # Verify health endpoint reflects failure
    pass
```

### 3. SLO Compliance Testing
```python
# Test SLO response time compliance
def test_slo_response_time():
    start_time = time.time()
    response = client.get("/health/detailed")
    duration = time.time() - start_time
    assert duration < 0.25  # 250ms SLO
```

## Security Considerations

### 1. Information Disclosure
```yaml
Security Measures:
  - Sensitive information redaction in health responses
  - Optional authentication for detailed health endpoints
  - Rate limiting on health endpoints
  - No internal system details in public health checks
```

### 2. Access Control
```yaml
Access Levels:
  - Public: Basic health check (/health)
  - Internal: Detailed health (/health/detailed)
  - Admin: Full diagnostics and metrics
```

## Success Criteria

### 1. Functional Requirements
- ✅ All health endpoints respond correctly
- ✅ Component health checks work reliably
- ✅ SLO compliance is accurately measured
- ✅ Kubernetes probes function properly
- ✅ Metrics are collected and exposed

### 2. Performance Requirements
- ✅ Basic health check < 10ms response time
- ✅ Detailed health check < 250ms response time
- ✅ Health checks don't impact application performance
- ✅ Metrics collection has minimal overhead

### 3. Operational Requirements
- ✅ Health status accurately reflects system state
- ✅ Alerts trigger appropriately
- ✅ Troubleshooting information is helpful
- ✅ Integration with monitoring systems works

## Future Enhancements

1. **Advanced Diagnostics**: Memory profiling, thread dumps, performance analysis
2. **Custom Health Checks**: User-defined health check plugins
3. **Health History**: Historical health data and trend analysis
4. **Dependency Mapping**: Visual representation of service dependencies
5. **Automated Remediation**: Self-healing capabilities for common issues

## Dependencies

- FastAPI (web framework)
- Prometheus client (metrics collection)
- PostgreSQL client (database health checks)
- asyncio (asynchronous health checks)
- datetime (timestamp generation)

This specification ensures ninaivalaigal has comprehensive, production-ready health monitoring capabilities suitable for enterprise deployment and operations.
