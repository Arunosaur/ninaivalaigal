# Container Rebuild Required

**Date:** October 19, 2025
**Reason:** Code changes committed that require container image updates

---

## 🔄 Containers Requiring Rebuild

### 1. Graph Service (HIGH PRIORITY)
**Container:** `ninaivalaigal-dev-graph-service`
**Image:** `nina-graph-service:arm64`
**Reason:** Added /api/v1/graph API prefix (Commit 244d21d1)

**Impact:**
- ❌ Current container returns 404 on `/api/v1/graph/health`
- ✅ After rebuild: All endpoints under `/api/v1/graph/*`
- ✅ Fixes 501 error Developer A reported
- ✅ SPEC-100 compliant structure

**Rebuild Commands:**
```bash
cd /Users/swami/WorkSpace/ninaivalaigal

# Build new image (MUST use --no-cache)
container build --no-cache \
  -t nina-graph-service:arm64 \
  -f services/graph-service/Dockerfile \
  services/graph-service

# Stop old container
container stop ninaivalaigal-dev-graph-service
container rm ninaivalaigal-dev-graph-service

# Start new container
container run -d \
  --name ninaivalaigal-dev-graph-service \
  -p 13394:8001 \
  --env-file .env \
  nina-graph-service:arm64
```

**Validation:**
```bash
# Should return 200 OK (not 404)
curl -I http://localhost:13394/api/v1/graph/health

# Should show Swagger UI
curl http://localhost:13394/docs
```

---

### 2. Memory Service (MEDIUM PRIORITY)
**Container:** `ninaivalaigal-dev-memory-service`
**Image:** `nina-memory-service:arm64`
**Reason:** Added utoipa Swagger documentation (Commit 8219001d)

**Impact:**
- ❌ Current container: No /docs endpoint
- ✅ After rebuild: Swagger UI at `/docs`
- ✅ OpenAPI JSON at `/api-docs/openapi.json`

**Rebuild Commands:**
```bash
cd /Users/swami/WorkSpace/ninaivalaigal

# Build new image (MUST use --no-cache)
container build --no-cache \
  -t nina-memory-service:arm64 \
  -f rust-services/memory-service/Dockerfile \
  rust-services/memory-service

# Stop old container
container stop ninaivalaigal-dev-memory-service
container rm ninaivalaigal-dev-memory-service

# Start new container
container run -d \
  --name ninaivalaigal-dev-memory-service \
  -p 13393:8000 \
  --env-file .env \
  nina-memory-service:arm64
```

**Validation:**
```bash
# Should show Swagger UI (not 404)
curl http://localhost:13393/docs

# Should show OpenAPI spec
curl http://localhost:13393/api-docs/openapi.json
```

---

## ⚠️ Critical Build Protocol

### ALWAYS Use --no-cache

```bash
# ❌ WRONG - Uses stale dependency layers
container build -t image:tag .

# ✅ CORRECT - Forces fresh build
container build --no-cache -t image:tag .
```

**Why:** Container layer caching can keep old dependencies, causing runtime failures even when build succeeds.

### Verify Dependencies After Build

```bash
# For Rust services - check utoipa
container run --rm nina-memory-service:arm64 \
  sh -c "cargo tree | grep utoipa"

# For Python services - check packages
container run --rm nina-graph-service:arm64 \
  pip list | grep fastapi
```

---

## 📋 Code Changes Summary

### Graph Service (services/graph-service/main.py)
```python
# OLD
app.include_router(health_router.router)

# NEW
app.include_router(health_router.router, prefix="/api/v1/graph", tags=["health"])
```

**All routers now have `/api/v1/graph` prefix for SPEC-100 compliance.**

---

### Memory Service (rust-services/memory-service/)

**Cargo.toml:**
```toml
# NEW dependencies
utoipa = { version = "4.2", features = ["axum_extras", "chrono", "uuid"] }
utoipa-swagger-ui = { version = "6.0", features = ["axum"] }
```

**main.rs:**
```rust
// Added OpenAPI documentation
#[derive(OpenApi)]
#[openapi(
    paths(health, remember, recall, list_memories, delete_memory),
    components(schemas(Memory, CreateMemoryRequest, RecallRequest)),
    ...
)]
struct ApiDoc;

// Swagger UI route
app.merge(SwaggerUi::new("/docs").url("/api-docs/openapi.json", ApiDoc::openapi()))
```

---

## 🧪 Post-Rebuild Validation

### Full Service Check
```bash
# Graph Service
curl http://localhost:13394/api/v1/graph/health
curl http://localhost:13394/docs

# Memory Service
curl http://localhost:13393/health
curl http://localhost:13393/docs

# All other services
curl http://localhost:13390/health  # Core API
curl http://localhost:13391/health  # Business
curl http://localhost:13392/health  # Admin/Vendor
```

### Load Tester Validation
```bash
# Should pass all 8 checks after graph-service rebuild
container run --rm nina-load-tester:arm64 validate http://192.168.66.94:8001
```

---

## 📊 Impact Assessment

### Before Rebuild:
- Graph Service: 404 on /api/v1/graph/health
- Memory Service: No Swagger documentation
- Load tester: Relies on fallback logic

### After Rebuild:
- ✅ Graph Service: SPEC-100 compliant endpoints
- ✅ Memory Service: Full Swagger UI
- ✅ Load tester: Clean validation (8/8 pass)
- ✅ Complete API documentation coverage

---

## 🎯 Priority Order

1. **HIGH:** Graph Service (fixes 501/404 errors)
2. **MEDIUM:** Memory Service (adds documentation)
3. **LOW:** Any other services (no breaking changes)

---

## 🤝 Developer Notes

**For Developer A:**
After graph-service rebuild, re-run your validation:
```bash
container run --rm nina-load-tester:arm64 validate http://192.168.66.94:8001
```
Should see 8/8 checks pass without fallback logic.

**For Developer C:**
Execute rebuilds during low-traffic period. Each rebuild takes ~5-10 minutes.

---

## 📚 Related Documentation

- `/docs/API_DOCUMENTATION_INDEX.md` - Complete API reference
- `/go-services/grpc-gateway/GRPC_EXPLORATION.md` - gRPC usage guide
- `/rust-services/graphops/GRAPHOPS_API_STATUS.md` - GraphOps status

---

**Status:** Pending rebuild
**Next Update:** After container rebuilds complete
