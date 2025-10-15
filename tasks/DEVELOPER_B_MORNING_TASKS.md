# Developer B - Morning Tasks (October 15, 2025)

## 🎯 Today's Focus: SPEC-099 Phase 0 - Python Client Stubs & Integration Prep

**Priority:** HIGH
**Timeline:** Start of 2-3 week validation phase
**Goal:** Create Python client infrastructure for future Rust service integration

---

## 📋 Task List (Priority Order)

### 1. 📦 Create Python gRPC Client Stub Structure (1 hour)

```bash
cd /Users/swami/WorkSpace/ninaivalaigal
mkdir -p python-clients/graphops
cd python-clients/graphops

# Create Python package structure
mkdir -p graphops_client/{proto,stubs}
touch graphops_client/__init__.py
touch graphops_client/client.py
touch graphops_client/models.py
```

**File:** `graphops_client/__init__.py`
```python
"""
GraphOps Python Client
Provides interface to Rust GraphOps microservice
"""

from .client import GraphOpsClient
from .models import CypherRequest, GraphResult

__version__ = "0.1.0"
__all__ = ["GraphOpsClient", "CypherRequest", "GraphResult"]
```

**Acceptance:** Package structure created and importable

---

### 2. 🎨 Define Python Data Models (Pydantic) (1.5 hours)

**File:** `graphops_client/models.py`

```python
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class CypherRequest(BaseModel):
    """Request model for Cypher query execution"""
    query: str = Field(..., description="Cypher query string")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Query parameters")
    timeout_ms: int = Field(default=5000, description="Query timeout in milliseconds")


class GraphNode(BaseModel):
    """Represents a graph node"""
    id: str
    labels: List[str]
    properties: Dict[str, Any]


class GraphEdge(BaseModel):
    """Represents a graph edge"""
    id: str
    type: str
    source: str
    target: str
    properties: Dict[str, Any]


class QueryMetrics(BaseModel):
    """Query execution metrics"""
    execution_time_ms: float
    nodes_returned: int
    edges_returned: int
    cache_hit: bool = False


class GraphResult(BaseModel):
    """Response model for graph query results"""
    nodes: List[GraphNode] = Field(default_factory=list)
    edges: List[GraphEdge] = Field(default_factory=list)
    metrics: Optional[QueryMetrics] = None
    error: Optional[str] = None


class HealthStatus(BaseModel):
    """Service health check response"""
    status: str  # "healthy", "degraded", "unhealthy"
    uptime_seconds: int
    version: str
    database_connected: bool
```

**Test models:**
```python
# test_models.py
def test_cypher_request_validation():
    request = CypherRequest(query="MATCH (n) RETURN n")
    assert request.query == "MATCH (n) RETURN n"
    assert request.timeout_ms == 5000

def test_graph_result_structure():
    result = GraphResult(
        nodes=[GraphNode(id="1", labels=["User"], properties={"name": "Alice"})],
        metrics=QueryMetrics(execution_time_ms=12.5, nodes_returned=1, edges_returned=0)
    )
    assert len(result.nodes) == 1
    assert result.metrics.execution_time_ms == 12.5
```

**Acceptance:** Pydantic models validate correctly with pytest

---

### 3. 🔌 Create GraphOps Client Class (Mock Implementation) (2 hours)

**File:** `graphops_client/client.py`

```python
import asyncio
import logging
from typing import Optional
from .models import CypherRequest, GraphResult, HealthStatus

logger = logging.getLogger(__name__)


class GraphOpsClient:
    """
    Python client for GraphOps Rust microservice
    Currently uses mock implementation until gRPC server is ready
    """

    def __init__(self, service_url: str = "localhost:50051", timeout: int = 30):
        self.service_url = service_url
        self.timeout = timeout
        self._connected = False
        logger.info(f"GraphOpsClient initialized for {service_url}")

    async def connect(self) -> bool:
        """Establish connection to GraphOps service"""
        try:
            # TODO: Replace with actual gRPC channel setup
            logger.info("Connecting to GraphOps service...")
            await asyncio.sleep(0.1)  # Simulate connection
            self._connected = True
            return True
        except Exception as e:
            logger.error(f"Failed to connect: {e}")
            return False

    async def execute_query(self, request: CypherRequest) -> GraphResult:
        """
        Execute Cypher query via GraphOps service

        Args:
            request: CypherRequest with query and parameters

        Returns:
            GraphResult with nodes, edges, and metrics
        """
        if not self._connected:
            await self.connect()

        # TODO: Replace with actual gRPC call
        logger.info(f"Executing query: {request.query[:50]}...")

        # Mock implementation for now
        return GraphResult(
            nodes=[],
            edges=[],
            metrics=None,
            error="Mock implementation - Rust service not yet running"
        )

    async def health_check(self) -> HealthStatus:
        """Check GraphOps service health"""
        # TODO: Replace with actual gRPC health check
        return HealthStatus(
            status="mock",
            uptime_seconds=0,
            version="0.1.0-mock",
            database_connected=False
        )

    async def close(self):
        """Close connection to GraphOps service"""
        self._connected = False
        logger.info("GraphOpsClient connection closed")
```

**Test client:**
```python
# test_client.py
import pytest

@pytest.mark.asyncio
async def test_graphops_client_connect():
    client = GraphOpsClient()
    connected = await client.connect()
    assert connected is True
    await client.close()

@pytest.mark.asyncio
async def test_graphops_client_execute_query():
    client = GraphOpsClient()
    await client.connect()

    request = CypherRequest(query="MATCH (n) RETURN n LIMIT 10")
    result = await client.execute_query(request)

    assert result is not None
    await client.close()
```

**Acceptance:** Client class instantiates and mock methods work

---

### 4. 🔗 Integrate Client into Existing FastAPI (1.5 hours)

**File:** `server/graphops_integration.py`

```python
from fastapi import APIRouter, HTTPException, Depends
from graphops_client import GraphOpsClient, CypherRequest, GraphResult
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/graph", tags=["GraphOps"])

# Global client instance (will be initialized on startup)
_graphops_client: Optional[GraphOpsClient] = None


async def get_graphops_client() -> GraphOpsClient:
    """Dependency injection for GraphOps client"""
    global _graphops_client
    if _graphops_client is None:
        _graphops_client = GraphOpsClient(service_url="localhost:50051")
        await _graphops_client.connect()
    return _graphops_client


@router.post("/query", response_model=GraphResult)
async def execute_cypher_query(
    request: CypherRequest,
    client: GraphOpsClient = Depends(get_graphops_client)
):
    """
    Execute Cypher query via GraphOps Rust service
    Fallback to Python implementation if Rust service unavailable
    """
    try:
        result = await client.execute_query(request)

        # If Rust service returns error, fallback to Python
        if result.error:
            logger.warning("Rust service unavailable, using Python fallback")
            # TODO: Call existing Python GraphOps implementation
            raise HTTPException(status_code=503, detail="GraphOps service unavailable")

        return result

    except Exception as e:
        logger.error(f"GraphOps query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def graphops_health(
    client: GraphOpsClient = Depends(get_graphops_client)
):
    """Check GraphOps service health"""
    try:
        health = await client.health_check()
        return health
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}
```

**Add to main FastAPI app:**
```python
# server/main.py
from server.graphops_integration import router as graphops_router

app.include_router(graphops_router)
```

**Test endpoints:**
```bash
# Start existing API
make nina-stack-up

# Test health check
curl http://localhost:13370/graph/health

# Test query endpoint (should return mock response)
curl -X POST http://localhost:13370/graph/query \
  -H "Content-Type: application/json" \
  -d '{"query": "MATCH (n) RETURN n LIMIT 5"}'
```

**Acceptance:** New GraphOps endpoints accessible via FastAPI

---

### 5. 📊 Create Performance Comparison Baseline (1 hour)

**File:** `benchmarks/python_graphops_baseline.py`

```python
"""
Python GraphOps Performance Baseline
Measures current Python implementation for comparison with Rust
"""

import time
import asyncio
from typing import List
from server.database.operations import execute_graph_query  # Existing implementation


async def benchmark_simple_match(iterations: int = 100):
    """Benchmark simple MATCH query"""
    query = "MATCH (n) RETURN n LIMIT 10"

    times: List[float] = []
    for _ in range(iterations):
        start = time.perf_counter()
        await execute_graph_query(query)
        end = time.perf_counter()
        times.append((end - start) * 1000)  # Convert to ms

    avg_time = sum(times) / len(times)
    p50 = sorted(times)[len(times) // 2]
    p95 = sorted(times)[int(len(times) * 0.95)]
    p99 = sorted(times)[int(len(times) * 0.99)]

    print(f"Simple MATCH Query (n={iterations}):")
    print(f"  Average: {avg_time:.2f}ms")
    print(f"  P50: {p50:.2f}ms")
    print(f"  P95: {p95:.2f}ms")
    print(f"  P99: {p99:.2f}ms")

    return {"avg": avg_time, "p50": p50, "p95": p95, "p99": p99}


async def benchmark_graph_traversal(iterations: int = 50):
    """Benchmark graph traversal query"""
    query = "MATCH (a)-[r*1..3]->(b) RETURN a, r, b LIMIT 10"

    times: List[float] = []
    for _ in range(iterations):
        start = time.perf_counter()
        await execute_graph_query(query)
        end = time.perf_counter()
        times.append((end - start) * 1000)

    avg_time = sum(times) / len(times)
    p95 = sorted(times)[int(len(times) * 0.95)]

    print(f"\nGraph Traversal Query (n={iterations}):")
    print(f"  Average: {avg_time:.2f}ms")
    print(f"  P95: {p95:.2f}ms")

    return {"avg": avg_time, "p95": p95}


if __name__ == "__main__":
    print("=== Python GraphOps Baseline Benchmarks ===\n")
    asyncio.run(benchmark_simple_match())
    asyncio.run(benchmark_graph_traversal())
```

**Run baseline:**
```bash
python3 benchmarks/python_graphops_baseline.py
```

**Acceptance:** Baseline performance numbers documented

---

## 🎯 End-of-Day Goals

**By 5 PM Today:**
- [ ] Python client package structure created
- [ ] Pydantic models defined and tested
- [ ] Mock GraphOpsClient working
- [ ] FastAPI integration complete
- [ ] Python baseline benchmarks collected

**Expected Output:**
- Python client library ready for gRPC integration
- Mock endpoints accessible via `/graph/*`
- Baseline performance numbers for comparison
- Documentation of Python implementation latency

---

## 📊 Progress Tracking

| Task | Status | Time Spent | Notes |
|------|--------|------------|-------|
| Client Package Structure | ⏳ | - | - |
| Pydantic Models | ⏳ | - | - |
| Mock Client Class | ⏳ | - | - |
| FastAPI Integration | ⏳ | - | - |
| Performance Baseline | ⏳ | - | - |

---

## 🆘 If You Get Blocked

**Import Issues:**
- Ensure `graphops_client` package is in `PYTHONPATH`
- Install in development mode: `pip install -e python-clients/graphops`

**FastAPI Integration Issues:**
- Check existing GraphOps implementation location
- Verify router registration in `main.py`
- Test with curl before writing tests

**Benchmark Issues:**
- Ensure database connection working
- Check Apache AGE extension loaded
- Verify existing graph queries functional

---

## 💬 Standup Notes Template

**What I completed yesterday:**
- [Previous work]

**What I'm working on today:**
- Creating Python client library for Rust GraphOps service
- Setting up mock implementation for integration testing
- Collecting Python baseline performance metrics

**Blockers:**
- None / [Describe blocker]

**Key metrics:**
- Python baseline latency: [X]ms
- Mock client functional: Yes/No
- FastAPI endpoints working: Yes/No

---

**Questions for team:**
- Existing GraphOps Python implementation location confirmed?
- gRPC port assignment (default 50051 OK)?
- Contract definition coordination with Developer C?

---

**Next Steps (Tomorrow):**
- Implement actual gRPC client (once Developer A has server)
- Add retry logic and circuit breaker
- Create integration tests with Rust service
- Document client usage patterns

---

**Last Updated:** 2025-10-15 01:15 AM
**Owner:** Developer B
**Sprint:** SPEC-099 Phase 0 (Week 1 of 3)
