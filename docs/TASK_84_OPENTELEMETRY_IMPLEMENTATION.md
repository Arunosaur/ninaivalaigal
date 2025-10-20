# Task #84: OpenTelemetry Distributed Tracing Implementation

**Status:** In Progress
**Started:** October 20, 2025
**Priority:** HIGH (SPEC-099/100 completion)

---

## 🎯 **Objective**

Implement comprehensive distributed tracing across all ninaivalaigal microservices using OpenTelemetry to enable:
- End-to-end request visibility across service boundaries
- Performance bottleneck identification
- Service dependency mapping
- Error tracking and debugging
- SLO monitoring

---

## 📋 **Current Architecture**

### **Services to Instrument:**
1. **Python Services** (FastAPI)
   - Core API (port 13390)
   - Business Service (port 13391)
   - Admin/Vendor Service (port 13392)
   - Graph Service (port 13394)

2. **Rust Services**
   - Memory Service (port 13393)
   - GraphOps (port 13398)

3. **Go Services**
   - gRPC Gateway (port 13395)
   - Load Tester (port 13396)
   - CLI Tools (port 13397)

4. **Infrastructure**
   - API Gateway (Traefik) - ports 80/443
   - PgBouncer (port 6432)
   - PostgreSQL (port 5432)
   - Redis (port 6379)

---

## 🏗️ **Implementation Plan**

### **Phase 1: Infrastructure Setup (2-3 hours)**

#### 1.1 Deploy Jaeger All-in-One
```yaml
# docker-compose.observability.yml
version: '3.8'

services:
  jaeger:
    image: jaegertracing/all-in-one:latest
    container_name: ninaivalaigal-dev-jaeger
    ports:
      - "5775:5775/udp"    # Zipkin compact thrift
      - "6831:6831/udp"    # Jaeger compact thrift
      - "6832:6832/udp"    # Jaeger binary thrift
      - "5778:5778"        # Serve configs
      - "16686:16686"      # Jaeger UI
      - "14268:14268"      # Jaeger collector HTTP
      - "14250:14250"      # Jaeger gRPC
      - "9411:9411"        # Zipkin compatible
    environment:
      - COLLECTOR_ZIPKIN_HOST_PORT=:9411
      - COLLECTOR_OTLP_ENABLED=true
    networks:
      - ninaivalaigal-network

networks:
  ninaivalaigal-network:
    external: true
```

#### 1.2 Create Management Scripts
- `scripts/nv-jaeger-start.sh`
- `scripts/nv-jaeger-stop.sh`
- `scripts/nv-jaeger-status.sh`

---

### **Phase 2: Python Services (FastAPI) - 4-6 hours**

#### 2.1 Add Dependencies
```python
# requirements/base.in
opentelemetry-api>=1.20.0,<2.0.0
opentelemetry-sdk>=1.20.0,<2.0.0
opentelemetry-instrumentation-fastapi>=0.41b0,<1.0.0
opentelemetry-instrumentation-httpx>=0.41b0,<1.0.0
opentelemetry-instrumentation-psycopg2>=0.41b0,<1.0.0
opentelemetry-instrumentation-redis>=0.41b0,<1.0.0
opentelemetry-exporter-jaeger>=1.20.0,<2.0.0
opentelemetry-exporter-otlp>=1.20.0,<2.0.0
```

#### 2.2 Create Tracing Module
```python
# server/observability/tracing.py
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.psycopg2 import Psycopg2Instrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor

def init_tracing(app, service_name: str):
    """Initialize OpenTelemetry tracing for FastAPI"""
    # Set up tracer provider
    trace.set_tracer_provider(TracerProvider())
    tracer = trace.get_tracer(__name__)

    # Configure OTLP exporter
    otlp_exporter = OTLPSpanExporter(
        endpoint="http://localhost:4317",  # Jaeger OTLP gRPC endpoint
        insecure=True
    )

    # Add span processor
    trace.get_tracer_provider().add_span_processor(
        BatchSpanProcessor(otlp_exporter)
    )

    # Instrument FastAPI
    FastAPIInstrumentor.instrument_app(app, tracer_provider=trace.get_tracer_provider())

    # Instrument HTTP clients
    HTTPXClientInstrumentor().instrument()

    # Instrument database
    Psycopg2Instrumentor().instrument()

    # Instrument Redis
    RedisInstrumentor().instrument()

    return tracer
```

#### 2.3 Update main.py
```python
# server/main.py
from observability.tracing import init_tracing

app = FastAPI(title="Ninaivalaigal Core API")

# Initialize tracing
tracer = init_tracing(app, "ninaivalaigal-core-api")
```

---

### **Phase 3: Rust Services - 6-8 hours**

#### 3.1 Add Dependencies to Cargo.toml
```toml
[dependencies]
opentelemetry = "0.21"
opentelemetry-otlp = "0.14"
opentelemetry-http = "0.10"
tracing = "0.1"
tracing-opentelemetry = "0.22"
tracing-subscriber = "0.3"
```

#### 3.2 Create Tracing Module (Rust)
```rust
// rust-services/common/src/tracing.rs
use opentelemetry::sdk::trace::TracerProvider;
use opentelemetry_otlp::WithExportConfig;
use tracing_subscriber::layer::SubscriberExt;
use tracing_subscriber::util::SubscriberInitExt;

pub fn init_tracing(service_name: &str) -> anyhow::Result<()> {
    let tracer = opentelemetry_otlp::new_pipeline()
        .tracing()
        .with_exporter(
            opentelemetry_otlp::new_exporter()
                .tonic()
                .with_endpoint("http://localhost:4317")
        )
        .with_trace_config(
            opentelemetry::sdk::trace::config()
                .with_resource(opentelemetry::sdk::Resource::new(vec![
                    opentelemetry::KeyValue::new("service.name", service_name),
                ]))
        )
        .install_batch(opentelemetry::runtime::Tokio)?;

    tracing_subscriber::registry()
        .with(tracing_subscriber::EnvFilter::from_default_env())
        .with(tracing_opentelemetry::layer().with_tracer(tracer))
        .with(tracing_subscriber::fmt::layer())
        .init();

    Ok(())
}
```

#### 3.3 Update Memory Service main.rs
```rust
// rust-services/memory-service/src/main.rs
mod tracing;

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    // Initialize tracing
    tracing::init_tracing("ninaivalaigal-memory-service")?;

    // Rest of the service initialization...
}
```

#### 3.4 Update GraphOps main.rs
```rust
// rust-services/graphops/src/main.rs
#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    // Initialize tracing
    common::tracing::init_tracing("ninaivalaigal-graphops")?;

    // Rest of the service initialization...
}
```

---

### **Phase 4: Go Services - 4-6 hours**

#### 4.1 Add Dependencies
```go
// go-services/go.mod
require (
    go.opentelemetry.io/otel v1.20.0
    go.opentelemetry.io/otel/exporters/otlp/otlptrace v1.20.0
    go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracegrpc v1.20.0
    go.opentelemetry.io/otel/sdk v1.20.0
    go.opentelemetry.io/otel/trace v1.20.0
    go.opentelemetry.io/contrib/instrumentation/google.golang.org/grpc/otelgrpc v0.46.0
    go.opentelemetry.io/contrib/instrumentation/net/http/otelhttp v0.46.0
)
```

#### 4.2 Create Tracing Package
```go
// go-services/pkg/tracing/tracing.go
package tracing

import (
    "context"
    "go.opentelemetry.io/otel"
    "go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracegrpc"
    "go.opentelemetry.io/otel/sdk/resource"
    sdktrace "go.opentelemetry.io/otel/sdk/trace"
    semconv "go.opentelemetry.io/otel/semconv/v1.20.0"
)

func InitTracing(ctx context.Context, serviceName string) (*sdktrace.TracerProvider, error) {
    exporter, err := otlptracegrpc.New(ctx,
        otlptracegrpc.WithInsecure(),
        otlptracegrpc.WithEndpoint("localhost:4317"),
    )
    if err != nil {
        return nil, err
    }

    res := resource.NewWithAttributes(
        semconv.SchemaURL,
        semconv.ServiceName(serviceName),
    )

    tp := sdktrace.NewTracerProvider(
        sdktrace.WithBatcher(exporter),
        sdktrace.WithResource(res),
    )

    otel.SetTracerProvider(tp)
    return tp, nil
}
```

#### 4.3 Update gRPC Gateway
```go
// go-services/grpc-gateway/main.go
import (
    "ninaivalaigal/pkg/tracing"
    "go.opentelemetry.io/contrib/instrumentation/google.golang.org/grpc/otelgrpc"
)

func main() {
    ctx := context.Background()

    // Initialize tracing
    tp, err := tracing.InitTracing(ctx, "ninaivalaigal-grpc-gateway")
    if err != nil {
        log.Fatal(err)
    }
    defer tp.Shutdown(ctx)

    // Create gRPC server with tracing
    grpcServer := grpc.NewServer(
        grpc.UnaryInterceptor(otelgrpc.UnaryServerInterceptor()),
        grpc.StreamInterceptor(otelgrpc.StreamServerInterceptor()),
    )
}
```

---

### **Phase 5: Trace Propagation - 2-3 hours**

#### 5.1 Configure Context Propagation
All services must propagate trace context via headers:
- `traceparent` (W3C Trace Context)
- `tracestate`

```python
# Python (FastAPI) - automatic with instrumentation

# Rust - add to HTTP clients
use opentelemetry::propagation::TextMapPropagator;
use opentelemetry_http::HeaderInjector;

let propagator = opentelemetry::sdk::propagation::TraceContextPropagator::new();
let mut injector = HeaderInjector(headers);
propagator.inject_context(&cx, &mut injector);

# Go - automatic with otelhttp and otelgrpc
```

#### 5.2 Test Trace Propagation
```bash
# Send request through API Gateway → gRPC Gateway → Services
curl -H "traceparent: 00-$(uuidgen | tr -d '-')000000000000-$(uuidgen | tr -d '-' | cut -c1-16)-01" \
  http://localhost/api/memory/health

# Verify trace in Jaeger UI
open http://localhost:16686
```

---

### **Phase 6: Dashboard and Testing - 2-3 hours**

#### 6.1 Jaeger UI Access
```bash
# Access Jaeger UI
open http://localhost:16686

# Search for traces
- Service: ninaivalaigal-core-api
- Operation: GET /api/memory/*
- Tags: http.status_code=200
```

#### 6.2 Create Test Suite
```python
# tests/integration/test_tracing.py
import pytest
import httpx
from opentelemetry import trace

@pytest.mark.asyncio
async def test_end_to_end_tracing():
    """Test distributed tracing across services"""
    # Start a trace
    tracer = trace.get_tracer(__name__)
    with tracer.start_as_current_span("test-request"):
        # Make request
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:13390/health")
            assert response.status_code == 200

            # Verify trace ID in response headers
            assert "traceparent" in response.headers
```

#### 6.3 Performance Metrics
- Trace collection overhead < 5ms per request
- 99.9% trace sampling for critical paths
- Automatic span correlation across services

---

## 📊 **Success Criteria**

### **Functional Requirements:**
- [ ] All 9 services instrumented with OpenTelemetry
- [ ] Jaeger collecting and displaying traces
- [ ] End-to-end trace visibility (client → gateway → services → database)
- [ ] Trace context propagated across all service boundaries
- [ ] Error spans properly tagged and searchable

### **Performance Requirements:**
- [ ] Tracing overhead < 5ms P95
- [ ] Trace completeness > 99%
- [ ] Jaeger UI responsive < 2s for queries

### **Operational Requirements:**
- [ ] Management scripts for Jaeger (start/stop/status)
- [ ] Documentation for trace analysis
- [ ] Integration with existing monitoring

---

## 🔧 **Technical Details**

### **Trace Context Format (W3C)**
```
traceparent: 00-{trace-id}-{span-id}-{flags}
Example: 00-0af7651916cd43dd8448eb211c80319c-b7ad6b7169203331-01
```

### **Service Name Convention**
```
ninaivalaigal-{service}
Examples:
- ninaivalaigal-core-api
- ninaivalaigal-memory-service
- ninaivalaigal-graphops
- ninaivalaigal-grpc-gateway
```

### **Span Attributes**
```python
# Required attributes
service.name = "ninaivalaigal-core-api"
http.method = "GET"
http.url = "/api/memory/123"
http.status_code = 200

# Custom attributes
user.id = "12345"
team.id = "67890"
db.system = "postgresql"
db.operation = "SELECT"
```

---

## 📁 **Files to Create/Modify**

### **New Files:**
- `docker-compose.observability.yml`
- `server/observability/tracing.py`
- `rust-services/common/src/tracing.rs`
- `go-services/pkg/tracing/tracing.go`
- `scripts/nv-jaeger-start.sh`
- `scripts/nv-jaeger-stop.sh`
- `scripts/nv-jaeger-status.sh`
- `docs/OPENTELEMETRY_GUIDE.md`
- `tests/integration/test_tracing.py`

### **Modified Files:**
- `server/main.py` (all Python services)
- `rust-services/memory-service/src/main.rs`
- `rust-services/graphops/src/main.rs`
- `go-services/grpc-gateway/main.go`
- `go-services/load-tester/main.go`
- `go-services/cli-tools/cmd/root.go`
- `requirements/base.in`
- `rust-services/*/Cargo.toml`
- `go-services/go.mod`
- `Makefile` (add tracing commands)

---

## 🎯 **Implementation Timeline**

| Phase | Duration | Deliverable |
|-------|----------|-------------|
| **Phase 1** | 2-3 hours | Jaeger deployed and accessible |
| **Phase 2** | 4-6 hours | Python services instrumented |
| **Phase 3** | 6-8 hours | Rust services instrumented |
| **Phase 4** | 4-6 hours | Go services instrumented |
| **Phase 5** | 2-3 hours | Trace propagation working |
| **Phase 6** | 2-3 hours | Dashboard and testing complete |
| **Total** | 20-29 hours | Full distributed tracing operational |

**Estimated Completion:** 3-4 days with focused effort

---

## 🚀 **Next Steps**

1. ✅ Create this specification document
2. ⏳ Deploy Jaeger infrastructure
3. ⏳ Instrument Python services (highest priority)
4. ⏳ Instrument Rust services
5. ⏳ Instrument Go services
6. ⏳ Test and validate end-to-end tracing

---

**Status:** Phase 1 starting now
**Last Updated:** October 20, 2025
