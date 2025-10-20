# GraphOps Container Startup Guide

**Task:** Start `ninaivalaigal-dev-graphops` container with Apple Container CLI
**Status:** Image rebuild in progress
**Date:** October 20, 2025

---

## 🎯 **Objective**

Start the GraphOps gRPC service container with:
1. Proper naming convention: `ninaivalaigal-dev-graphops`
2. Apple Container CLI (not Docker)
3. Health check validation
4. Integration with existing services

---

## 📋 **Current Status**

### **Issue Identified:**
Developer A built the image with **Docker**, but we need it in **Apple Container CLI**:

```bash
# ❌ Developer A's build (Docker)
docker build --no-cache --platform linux/arm64 \
  -t ninaivalaigal-graphops:arm64 \
  -f containers/graphops-rust/Dockerfile .

# ✅ Correct build (Apple Container CLI)
container build --platform linux/arm64 \
  -t ninaivalaigal-graphops:arm64 \
  -f containers/graphops-rust/Dockerfile .
```

### **Build Started:**
```bash
# Build in progress (takes ~5-10 minutes for Rust compilation)
container build --platform linux/arm64 \
  -t ninaivalaigal-graphops:arm64 \
  -f containers/graphops-rust/Dockerfile .
```

---

## 🚀 **Startup Procedure (After Build Completes)**

### **1. Verify Image Exists**

```bash
container image list | grep graphops
# Should show: ninaivalaigal-graphops:arm64
```

### **2. Get PgBouncer IP Address**

```bash
container list | grep pgbouncer
# Note the IP address (e.g., 192.168.66.90)
```

### **3. Start GraphOps Container**

```bash
container run -d \
  --name ninaivalaigal-dev-graphops \
  -e DATABASE_URL=postgresql://nina:password@192.168.66.90:6432/ninaivalaigal_dev `# pragma: allowlist secret` \
  -e GRAPHOPS_GRAPH=ninaivalaigal_intelligence_dev \
  -e GRAPHOPS_GRPC_ADDR=0.0.0.0:50051 \
  -e GRAPHOPS_METRICS_ADDR=0.0.0.0:9090 \
  -e RUST_LOG=info \
  -p 13394:50051 \
  -p 9090:9090 \
  ninaivalaigal-graphops:arm64
```

**Port Mapping:**
- `13394:50051` - gRPC service (host:container) - from ports.nv.yaml
- `9090:9090` - Metrics endpoint

**Environment Variables:**
- `DATABASE_URL` - Points to PgBouncer at correct IP (192.168.66.90:6432)
- `GRAPHOPS_GRAPH` - AGE graph name: `ninaivalaigal_intelligence_dev`
- `GRAPHOPS_GRPC_ADDR` - gRPC listen address (inside container)
- `GRAPHOPS_METRICS_ADDR` - Metrics listen address (inside container)
- `RUST_LOG` - Logging level

---

## ✅ **Validation Steps**

### **1. Check Container Status**

```bash
container list | grep graphops
# Should show: ninaivalaigal-dev-graphops running
```

### **2. Test Health Check (New Feature!)**

```bash
# Quick health check (Developer A's new feature)
container exec ninaivalaigal-dev-graphops /usr/local/bin/graphops --health-check

# Expected output:
# 🏥 Running GraphOps health check...
#   ✅ Binary executable
#   ✅ DATABASE_URL configured
#   ✅ GRAPHOPS_GRAPH configured
# ✅ GraphOps health check PASSED
```

### **3. Check Container Logs**

```bash
container logs ninaivalaigal-dev-graphops

# Should see:
# - GraphOps server starting
# - gRPC server listening on 0.0.0.0:50051
# - Metrics server on 0.0.0.0:9090
# - No connection errors
```

### **4. Test Metrics Endpoint**

```bash
# From host machine
curl http://localhost:9090/health

# Expected: HTTP 200 OK
```

### **5. Test gRPC Service**

```bash
# If grpcurl is available
grpcurl -plaintext localhost:13394 list

# Or test via gateway (once integrated)
curl http://localhost/graph/health
```

---

## 🔧 **Troubleshooting**

### **Problem: Container won't start**

```bash
# Check logs for errors
container logs ninaivalaigal-dev-graphops

# Common issues:
# 1. DATABASE_URL incorrect (check PgBouncer IP)
# 2. Graph doesn't exist in database
# 3. Port conflicts (9090 or 13394 already in use)
```

### **Problem: Can't connect to database**

```bash
# Verify PgBouncer is running
container list | grep pgbouncer

# Test PgBouncer connection
container exec ninaivalaigal-dev-pgbouncer psql -U nina -d ninaivalaigal_dev -c "SELECT 1;"

# Check if AGE graph exists
container exec ninaivalaigal-dev-db psql -U nina -d ninaivalaigal_dev -c "SELECT * FROM ag_catalog.ag_graph WHERE name = 'ninaivalaigal_intelligence_dev';"
```

### **Problem: Health check fails**

```bash
# Run health check with more details
container exec ninaivalaigal-dev-graphops /usr/local/bin/graphops --health-check

# If it exits with error, check:
# 1. DATABASE_URL format
# 2. Graph name spelling
# 3. Environment variables set correctly
```

---

## 📊 **Expected Container List After Startup**

```
container list
```

Should show all these running:

| Container Name | Purpose | Port(s) |
|----------------|---------|---------|
| `ninaivalaigal-dev-db` | PostgreSQL + AGE | 5452 |
| `ninaivalaigal-dev-pgbouncer` | Connection pooler | 6452 |
| `ninaivalaigal-dev-redis` | Cache | 6399 |
| `ninaivalaigal-dev-core-api` | Core API | 13390 |
| `ninaivalaigal-dev-business-service` | Business Logic | 13391 |
| `ninaivalaigal-dev-admin-vendor` | Admin/Vendor | 13392 |
| `ninaivalaigal-dev-memory-service` | Memory CRUD | 13393 |
| `ninaivalaigal-dev-graph-service` | Graph Intelligence | 13394* |
| **`ninaivalaigal-dev-graphops`** | **GraphOps gRPC** | **13394, 9090** |
| `ninaivalaigal-dev-grpc-gateway` | gRPC Gateway | 13395 |
| `ninaivalaigal-dev-em` | Enhanced Memory | 8301 |
| `ninaivalaigal-dev-load-tester` | Load Testing | - |

**Note:** Port 13394 conflict between graph-service and graphops needs resolution!

---

## ⚠️ **Port Conflict Warning**

**Issue:** Both `graph-service` and `graphops` want port 13394

**Resolution Options:**

### **Option 1: Use Different Ports (Recommended)**

Update ports.nv.yaml:
```yaml
graph_service: 13394       # Keep existing
graphops_grpc: 50051       # Use container port directly
graphops_metrics: 9091     # Different from 9090
```

Start GraphOps:
```bash
container run -d \
  --name ninaivalaigal-dev-graphops \
  -p 50051:50051 \
  -p 9091:9090 \
  ...
```

### **Option 2: Stop graph-service**

If graph-service and graphops are duplicate services:
```bash
# Stop old service
container stop ninaivalaigal-dev-graph-service
container rm ninaivalaigal-dev-graph-service

# Then start graphops on 13394
```

---

## 🎯 **Integration with API Gateway**

Once GraphOps is running, update Traefik configuration:

### **Add Route in `deployment/traefik/dynamic.yml`**

```yaml
http:
  routers:
    graphops-router:
      rule: "PathPrefix(`/graphops`)"
      service: graphops-service
      middlewares:
        - stripprefix-graphops
        - ratelimit

  services:
    graphops-service:
      loadBalancer:
        servers:
          - url: "http://192.168.66.XXX:9090"  # GraphOps container IP
        healthCheck:
          path: "/health"
          interval: "10s"
          timeout: "3s"

  middlewares:
    stripprefix-graphops:
      stripPrefix:
        prefixes:
          - "/graphops"
```

### **Test via Gateway**

```bash
# Health check via gateway
curl http://localhost/graphops/health

# Expected: HTTP 200 OK
```

---

## 📝 **Next Steps**

### **After Container Starts:**

1. ✅ Verify health check works
2. ✅ Test metrics endpoint
3. ✅ Check gRPC service responding
4. ✅ Integrate with API Gateway
5. ✅ Update Task #49 to Done
6. ✅ Document in deployment guides

### **For Developer A:**

Once the build completes:
1. Follow the startup procedure above
2. Validate health check: `--health-check` flag working
3. Test all endpoints (gRPC, metrics, health)
4. Report any issues with DATABASE_URL or configuration

---

## 🏆 **Success Criteria**

GraphOps container is considered successfully started when:

- ✅ Container shows "running" status
- ✅ `--health-check` returns success
- ✅ Metrics endpoint responds on port 9090
- ✅ gRPC service accepts connections on port 50051
- ✅ No database connection errors in logs
- ✅ Integrated with API Gateway

---

**Build Status:** In progress (check with `container image list | grep graphops`)
**Estimated Build Time:** 5-10 minutes (Rust compilation)
**Next:** Run startup procedure once build completes

---

**Created:** October 20, 2025
**Task:** #49 GraphOps gRPC Integration
**Related:** #83 API Gateway, #77 CLI Tools Deployment
