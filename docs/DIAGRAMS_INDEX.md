# 📊 Architecture Diagrams Index

Complete visual guide to ninaivalaigal architecture across all runtimes and environments.

---

## 🎯 Quick Navigation

| Diagram Type | Description | Link |
|--------------|-------------|------|
| **High-Level Architecture** | Complete system overview | [View](#high-level) |
| **Sequence Diagrams** | Component interaction flow | [View](#sequence) |
| **Network Architecture** | Container networking | [View](#network) |
| **Deployment** | Multi-runtime deployment | [View](#deployment) |
| **Data Flow** | Caching strategy | [View](#data-flow) |
| **Monitoring** | Health check flow | [View](#monitoring) |
| **Port Matrix** | Complete port allocation | [View](#ports) |

---

## 📋 Available Diagrams

### <a name="high-level"></a>🏗️ **1. High-Level Architecture**
**Shows:** Browser → UI → API → PgBouncer → PostgreSQL + Redis

**Location:** [ARCHITECTURE_DIAGRAM.md](ARCHITECTURE_DIAGRAM.md#high-level-architecture-flow)

```
External Users → UI (8081/8181) → API (13370) → PgBouncer (6432) → PostgreSQL (5432)
                                                ↘ Redis (6379)
```

**Key Features:**
- ✅ All traffic routes through PgBouncer
- ✅ Split UI (External vs Internal)
- ✅ Redis for caching and sessions
- ✅ Production-aligned architecture

---

### <a name="sequence"></a>🔄 **2. Sequence Diagram - Request Flow**
**Shows:** Detailed interaction between components with cache logic

**Location:** [ARCHITECTURE_DIAGRAM.md](ARCHITECTURE_DIAGRAM.md#detailed-component-interaction)

```
User → UI → API → Redis (cache check) → PgBouncer → PostgreSQL
                   ↓ (cache hit)
                   Return cached data
```

**Key Features:**
- ✅ Cache-first strategy
- ✅ Session validation
- ✅ Rate limiting flow
- ✅ Connection pooling

---

### <a name="network"></a>🌐 **3. Container Network Architecture**
**Shows:** Docker network with IP allocation and port forwarding

**Location:** [ARCHITECTURE_DIAGRAM.md](ARCHITECTURE_DIAGRAM.md#container-network-architecture)

```
172.28.0.0/16 Docker Network
├── PostgreSQL (172.28.0.10:5432)
├── PgBouncer (172.28.0.20:6432)
├── Redis (172.28.0.30:6379)
├── API (172.28.0.100:8000)
├── UI-External (172.28.0.150:80)
└── UI-Internal (172.28.0.151:80)
```

**Key Features:**
- ✅ Static IP allocation
- ✅ Host port mapping
- ✅ Service discovery via DNS
- ✅ Network isolation

---

### <a name="deployment"></a>🚀 **4. Multi-Runtime Deployment**
**Shows:** Parallel development across Docker, Colima, Apple CLI

**Location:** [ARCHITECTURE_DIAGRAM.md](ARCHITECTURE_DIAGRAM.md#deployment-architecture-multi-runtime)

```
Docker  Runtime: Ports 5432, 6432, 13370
Colima  Runtime: Ports 5442, 6442, 13380
Apple   Runtime: Ports 5452, 6452, 13390
         ↓          ↓          ↓
    GitHub Container Registry (GHCR)
         ↓
    Local Image Cache
```

**Key Features:**
- ✅ No port collisions
- ✅ Shared image registry
- ✅ Parallel development
- ✅ Runtime-specific offsets

---

### <a name="data-flow"></a>💾 **5. Data Flow with Caching**
**Shows:** How data flows from client to database with Redis caching

**Location:** [ARCHITECTURE_DIAGRAM.md](ARCHITECTURE_DIAGRAM.md#data-flow-with-caching-strategy)

```
Client Request
    ↓
API Handler → Check Redis Cache
    ↓               ↙        ↘
Cache Hit        Cache Miss
    ↓               ↓
Return Cached    Query via PgBouncer
                    ↓
                PostgreSQL
                    ↓
                Update Cache
```

**Key Features:**
- ✅ 1-hour TTL on cache
- ✅ Cache-aside pattern
- ✅ Automatic cache warming
- ✅ Connection pooling

---

### <a name="monitoring"></a>📊 **6. Health Monitoring Flow**
**Shows:** Automated health checks and recovery actions

**Location:** [ARCHITECTURE_DIAGRAM.md](ARCHITECTURE_DIAGRAM.md#health-monitoring-flow)

```
/health/detailed Endpoint
    ↓
Check: DB, Redis, PgBouncer
    ↓ (any unhealthy)
Actions: Slack Alert, Auto-restart, Log Error
```

**Key Features:**
- ✅ Multi-component health checks
- ✅ Automatic service restart
- ✅ Slack notifications
- ✅ Error logging

---

### <a name="ports"></a>🔢 **7. Complete Port Matrix**
**Shows:** All 9 port configurations (3 runtimes × 3 environments)

**Location:** [ARCHITECTURE_DIAGRAM.md](ARCHITECTURE_DIAGRAM.md#runtime--environment-port-matrix)

| Runtime | Env  | Postgres | PgBouncer | Redis | API   | UI-Ext | UI-Int |
|---------|------|----------|-----------|-------|-------|--------|--------|
| Docker  | Dev  | 5432     | 6432      | 6379  | 13370 | 8081   | 8181   |
| Docker  | Test | 5532     | 6532      | 6479  | 13470 | 8091   | 8191   |
| Docker  | Prod | 5632     | 6632      | 6579  | 13570 | 8101   | 8201   |
| Colima  | Dev  | 5442     | 6442      | 6389  | 13380 | 8091   | 8191   |
| Colima  | Test | 5542     | 6542      | 6489  | 13480 | 8101   | 8201   |
| Colima  | Prod | 5642     | 6642      | 6589  | 13580 | 8111   | 8211   |
| Apple   | Dev  | 5452     | 6452      | 6399  | 13390 | 8101   | 8201   |
| Apple   | Test | 5552     | 6552      | 6499  | 13490 | 8111   | 8211   |
| Apple   | Prod | 5652     | 6652      | 6599  | 13590 | 8121   | 8221   |

**Port Calculation:**
```
Base Port + Environment Offset + Runtime Offset = Final Port

Examples:
5432 + 0 (dev) + 0 (docker)  = 5432
5432 + 0 (dev) + 10 (colima) = 5442
5432 + 100 (test) + 0        = 5532
```

---

## 🎯 Design Principles

### **1. Production Parity**
All environments (dev/test/prod) use the same architecture:
- ✅ All DB traffic → PgBouncer
- ✅ Redis for caching
- ✅ Split UI (External/Internal)

### **2. No Port Collisions**
Smart port allocation prevents conflicts:
- ✅ Environment offset: +0, +100, +200
- ✅ Runtime offset: +0, +10, +20
- ✅ Predictable pattern

### **3. Connection Pooling**
PgBouncer mediates all database access:
- ✅ Reuse connections
- ✅ Reduced memory footprint
- ✅ Production parity

### **4. Security Isolation**
Split UI architecture:
- ✅ External: Public customers (8081)
- ✅ Internal: Admin staff (8181)
- ✅ Separate domains in production

---

## 📚 Related Documentation

### **Architecture:**
- [Complete Architecture Diagrams](ARCHITECTURE_DIAGRAM.md)
- [Database Patterns](DATABASE_PATTERNS.md)
- [Database Image Management](DATABASE_IMAGE_MANAGEMENT.md)

### **Deployment:**
- [Docker Compose Configuration](../compose.docker.yml)
- [Multi-Architecture Build Strategy](MULTI_ARCH_BUILD_STRATEGY.md)

### **Development:**
- [Development Setup](../README.md#quick-start)
- [Colleague Quick Start](../COLLEAGUE_QUICK_START.md)

---

## 🔍 Quick References

### **Connect to Components:**

```bash
# Database (through PgBouncer - recommended)
psql "postgresql://nv_user:password@localhost:6432/ninaivalaigal"  # pragma: allowlist secret

# Database (direct - not recommended)
psql "postgresql://nina:password@localhost:5432/ninaivalaigal"  # pragma: allowlist secret

# Redis CLI
docker exec -it ninaivalaigal-dev-redis redis-cli

# API Health Check
curl http://localhost:13370/health/detailed

# External UI
open http://localhost:8081

# Admin Console
open http://localhost:8181
```

### **View PgBouncer Stats:**

```bash
docker exec ninaivalaigal-dev-pgbouncer \
  psql -h localhost -p 6432 -U nv_user -d pgbouncer -c "SHOW POOLS;"
```

### **Check Container Status:**

```bash
docker-compose -f compose.docker.yml ps
```

---

## 🎓 For New Team Members

**Start here:**
1. 📖 Read [High-Level Architecture](#high-level)
2. 🔍 Review [Port Matrix](#ports)
3. 🚀 Check [Deployment Architecture](#deployment)
4. 💾 Understand [Data Flow](#data-flow)

**Then deep dive:**
5. 🔄 Study [Sequence Diagrams](#sequence)
6. 🌐 Learn [Network Architecture](#network)
7. 📊 Explore [Monitoring](#monitoring)

---

**Last Updated:** October 4, 2025
**Status:** ✅ Complete Visual Architecture Documentation
**Diagrams:** 7 comprehensive Mermaid diagrams
**Coverage:** All runtimes × all environments
