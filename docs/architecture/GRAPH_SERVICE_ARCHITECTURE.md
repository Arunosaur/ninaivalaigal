# Graph Service Architecture
## Separate, Modular Graph Intelligence Infrastructure

**Date**: September 22, 2024
**Architecture**: Microservices approach with optional graph intelligence

## 🏗️ **Service Separation Strategy**

### **Core Principle: Independent Services**
- **Main API** (Port 13370): Core memory management, auth, vendor admin
- **Graph Service** (Port 8001): Graph intelligence, reasoning, analytics
- **Graph Database**: Apache AGE + PostgreSQL + Redis cache

### **Why Separate Services:**
1. **Independent Scaling**: Graph operations can scale separately
2. **Technology Isolation**: Graph tech stack evolves independently
3. **Optional Dependency**: Main API works without graph service
4. **Development Velocity**: Parallel development without conflicts
5. **Deployment Flexibility**: Can disable graph features in some environments

## 🔗 **Integration Pattern: HTTP Service Calls**

### **Main API → Graph Service Integration**
```python
# In memory_suggestions.py - HTTP integration
async def get_graph_enhanced_suggestions(memory_id: str):
    try:
        # Optional graph enhancement via HTTP
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://graph-service:8001/graph/infer-relevance",
                json={"memory_id": memory_id, "max_suggestions": 5},
                timeout=2.0  # Fast timeout for optional feature
            )
            if response.status_code == 200:
                graph_suggestions = response.json()
                return enhance_suggestions_with_graph(graph_suggestions)
    except (httpx.TimeoutException, httpx.ConnectError):
        # Graceful degradation - continue without graph
        logger.info("Graph service unavailable, using standard suggestions")

    # Fallback to standard suggestions
    return get_standard_suggestions(memory_id)
```

### **Vendor Admin → Graph Analytics Integration**
```python
# In vendor_admin_api.py - Optional graph insights
async def get_tenant_insights_with_graph(tenant_id: str):
    standard_insights = await get_standard_tenant_insights(tenant_id)

    try:
        # Optional graph analytics
        graph_insights = await call_graph_service(
            "/graph/analyze-tenant-patterns",
            {"tenant_id": tenant_id}
        )
        return merge_insights(standard_insights, graph_insights)
    except GraphServiceUnavailable:
        return standard_insights  # Graceful degradation
```

## 📊 **Current Implementation Status**

### **✅ Available (Separate Services)**
- Graph Intelligence API (`server/graph_intelligence_api.py`)
- Graph Reasoner (`server/graph/graph_reasoner.py`)
- Apache AGE Client (`server/graph/age_client.py`)
- Graph Database Schema (`containers/graph-db/init-schema.sql`)
- GraphOps Deployment (`specs/062-graphops-deployment/`)

### **⚠️ Needs Integration (HTTP Calls)**
- Memory suggestions should optionally call graph service
- Vendor admin should optionally use graph analytics
- Feedback system should optionally use graph patterns
- All integrations should gracefully degrade if graph unavailable

### **🎯 Integration Plan**

#### **Phase 1: HTTP Client Integration**
1. Add HTTP client to memory suggestions for graph-enhanced results
2. Add optional graph analytics to vendor admin insights
3. Add graph pattern analysis to feedback system
4. All with graceful degradation and fast timeouts

#### **Phase 2: Graph Service Deployment**
1. Deploy graph service as separate container
2. Configure service discovery and health checks
3. Add monitoring for graph service availability
4. Test graceful degradation scenarios

#### **Phase 3: Advanced Graph Features**
1. Real-time graph updates from memory operations
2. Graph-based collaborative filtering
3. Advanced relationship detection and scoring
4. Graph-powered predictive analytics

## 🚀 **Deployment Architecture**

```yaml
# docker-compose.yml - Separate services
services:
  main-api:
    image: nina-api:arm64
    ports: ["13370:8000"]
    environment:
      - GRAPH_SERVICE_URL=http://graph-service:8001
    depends_on: [db, redis]

  graph-service:
    image: nina-graph:arm64
    ports: ["8001:8000"]
    environment:
      - GRAPH_DB_URL=postgresql://nina@graph-db:5432/nina
      - REDIS_URL=redis://redis:6379
    depends_on: [graph-db, redis]

  graph-db:
    image: nina-graph-db:arm64
    ports: ["5434:5432"]  # Separate port from main DB
    volumes: ["graph-data:/var/lib/postgresql/data"]
```

## 🔧 **Service Communication**

### **HTTP Integration Pattern**
```python
class GraphServiceClient:
    def __init__(self, base_url: str, timeout: float = 2.0):
        self.base_url = base_url
        self.timeout = timeout

    async def enhance_suggestions(self, memory_id: str) -> Optional[List[dict]]:
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/graph/infer-relevance",
                    json={"memory_id": memory_id}
                )
                return response.json() if response.status_code == 200 else None
        except Exception:
            return None  # Graceful degradation
```

### **Configuration Management**
```python
# settings.py
GRAPH_SERVICE_ENABLED = os.getenv("GRAPH_SERVICE_ENABLED", "true").lower() == "true"
GRAPH_SERVICE_URL = os.getenv("GRAPH_SERVICE_URL", "http://localhost:8001")
GRAPH_SERVICE_TIMEOUT = float(os.getenv("GRAPH_SERVICE_TIMEOUT", "2.0"))
```

## 📈 **Benefits of This Architecture**

1. **Resilience**: Main API never fails due to graph issues
2. **Performance**: Graph operations don't block main API
3. **Scalability**: Each service scales independently
4. **Maintainability**: Clear service boundaries and responsibilities
5. **Flexibility**: Can deploy with or without graph features

---

**Next Steps**: Implement HTTP client integration in memory suggestions and vendor admin, maintaining the separate service architecture while adding optional graph enhancements.
