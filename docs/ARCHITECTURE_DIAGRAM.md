# 🏗️ Ninaivalaigal Architecture Diagram

## 📊 Complete Network + Container + Port Flow

This diagram shows how all components connect across Docker, Colima, and Apple CLI runtimes.

---

## 🎯 Production-Aligned Architecture (All Traffic → PgBouncer)

### **High-Level Architecture Flow**

```mermaid
graph TB
    subgraph "External World"
        Browser[🌐 Browser / Public Users]
        AdminBrowser[👔 Admin Staff]
    end

    subgraph "Frontend Layer"
        UIExternal[📱 UI - External<br/>Customer App<br/>Port: 8081/8091/8101]
        UIInternal[🔐 UI - Internal<br/>Admin Console<br/>Port: 8181/8191/8201]
    end

    subgraph "API Layer"
        API[⚡ FastAPI Server<br/>Port: 13370/13470/13570<br/><br/>• REST Endpoints<br/>• MCP Server<br/>• WebSocket Support]
    end

    subgraph "Connection Pooling"
        PgBouncer[🔄 PgBouncer<br/>Port: 6432/6532/6632<br/><br/>• Connection Pooling<br/>• SCRAM-SHA-256 Auth<br/>• Production Parity]
    end

    subgraph "Data Layer"
        Postgres[(🐘 PostgreSQL 15<br/>Port: 5432/5532/5632<br/><br/>• pgvector v0.5.1<br/>• Apache AGE v1.5.0-rc0<br/>• Embeddings + Graph)]
        Redis[💾 Redis 7<br/>Port: 6379/6479/6579<br/><br/>• Session Cache<br/>• Memory Cache<br/>• Rate Limiting]
    end

    Browser --> UIExternal
    AdminBrowser --> UIInternal

    UIExternal --> API
    UIInternal --> API

    API --> PgBouncer
    API --> Redis

    PgBouncer --> Postgres

    style Browser fill:#e1f5ff
    style AdminBrowser fill:#ffe1e1
    style UIExternal fill:#4CAF50,color:#fff
    style UIInternal fill:#f44336,color:#fff
    style API fill:#2196F3,color:#fff
    style PgBouncer fill:#FF9800,color:#fff
    style Postgres fill:#673AB7,color:#fff
    style Redis fill:#F44336,color:#fff
```

### **Detailed Component Interaction**

```mermaid
sequenceDiagram
    participant User as 🌐 User Browser
    participant UI as 📱 UI Layer
    participant API as ⚡ FastAPI
    participant Redis as 💾 Redis
    participant PgB as 🔄 PgBouncer
    participant DB as 🐘 PostgreSQL

    User->>UI: HTTP Request (8081)
    UI->>API: API Call (13370)

    alt Check Cache First
        API->>Redis: Check cache (6379)
        Redis-->>API: Cache Hit/Miss
    end

    alt Cache Miss - Query Database
        API->>PgB: SQL Query (6432)
        PgB->>DB: Connection Pool (5432)
        DB-->>PgB: Query Result
        PgB-->>API: Result
        API->>Redis: Update Cache
    end

    API-->>UI: JSON Response
    UI-->>User: Rendered UI

    Note over API,Redis: Session validation<br/>Rate limiting<br/>Memory cache
    Note over PgB,DB: Connection pooling<br/>25 connections max<br/>Transaction mode
```

### **Container Network Architecture**

```mermaid
graph LR
    subgraph "Docker Network: ninaivalaigal-network (172.28.0.0/16)"
        subgraph "Database Tier"
            DB[PostgreSQL<br/>172.28.0.10:5432]
            PgB[PgBouncer<br/>172.28.0.20:6432]
        end

        subgraph "Cache Tier"
            Redis[Redis<br/>172.28.0.30:6379]
        end

        subgraph "Application Tier"
            API[FastAPI<br/>172.28.0.100:8000]
        end

        subgraph "Frontend Tier"
            UIExt[UI-External<br/>172.28.0.150:80]
            UIInt[UI-Internal<br/>172.28.0.151:80]
        end
    end

    subgraph "Host Machine"
        HostPorts[Port Mappings<br/>5432, 6432, 6379<br/>13370, 8081, 8181]
    end

    API --> PgB
    PgB --> DB
    API --> Redis
    UIExt --> API
    UIInt --> API

    HostPorts -.->|Port Forward| DB
    HostPorts -.->|Port Forward| PgB
    HostPorts -.->|Port Forward| Redis
    HostPorts -.->|Port Forward| API
    HostPorts -.->|Port Forward| UIExt
    HostPorts -.->|Port Forward| UIInt

    style DB fill:#673AB7,color:#fff
    style PgB fill:#FF9800,color:#fff
    style Redis fill:#F44336,color:#fff
    style API fill:#2196F3,color:#fff
    style UIExt fill:#4CAF50,color:#fff
    style UIInt fill:#f44336,color:#fff
```

---

## 🔀 Runtime × Environment Port Matrix

### **Docker Runtime**

```
┌─────────────┬──────────────┬────────────┬──────────┬───────┬───────────────┬───────────────┐
│ Environment │ PostgreSQL   │ PgBouncer  │ Redis    │ API   │ UI-External   │ UI-Internal   │
├─────────────┼──────────────┼────────────┼──────────┼───────┼───────────────┼───────────────┤
│ Dev         │ 5432         │ 6432       │ 6379     │ 13370 │ 8081          │ 8181          │
│ Test        │ 5532         │ 6532       │ 6479     │ 13470 │ 8091          │ 8191          │
│ Prod        │ 5632         │ 6632       │ 6579     │ 13570 │ 8101          │ 8201          │
└─────────────┴──────────────┴────────────┴──────────┴───────┴───────────────┴───────────────┘
```

### **Colima Runtime**

```
┌─────────────┬──────────────┬────────────┬──────────┬───────┬───────────────┬───────────────┐
│ Environment │ PostgreSQL   │ PgBouncer  │ Redis    │ API   │ UI-External   │ UI-Internal   │
├─────────────┼──────────────┼────────────┼──────────┼───────┼───────────────┼───────────────┤
│ Dev         │ 5442         │ 6442       │ 6389     │ 13380 │ 8091          │ 8191          │
│ Test        │ 5542         │ 6542       │ 6489     │ 13480 │ 8101          │ 8201          │
│ Prod        │ 5642         │ 6642       │ 6589     │ 13580 │ 8111          │ 8211          │
└─────────────┴──────────────┴────────────┴──────────┴───────┴───────────────┴───────────────┘
```

### **Apple CLI Runtime**

```
┌─────────────┬──────────────┬────────────┬──────────┬───────┬───────────────┬───────────────┐
│ Environment │ PostgreSQL   │ PgBouncer  │ Redis    │ API   │ UI-External   │ UI-Internal   │
├─────────────┼──────────────┼────────────┼──────────┼───────┼───────────────┼───────────────┤
│ Dev         │ 5452         │ 6452       │ 6399     │ 13390 │ 8101          │ 8201          │
│ Test        │ 5552         │ 6552       │ 6499     │ 13490 │ 8111          │ 8211          │
│ Prod        │ 5652         │ 6652       │ 6599     │ 13590 │ 8121          │ 8221          │
└─────────────┴──────────────┴────────────┴──────────┴───────┴───────────────┴───────────────┘
```

---

## 🔌 Connection Flow Details

### **1. User Request Flow (External)**

```
Browser
   ↓
   ↓ HTTP :8081 (Docker Dev)
   ↓
UI - External (Customer App)
   ↓
   ↓ HTTP :13370
   ↓
FastAPI Server
   ↓
   ├─→ Redis :6379 (Cache)
   │
   └─→ PgBouncer :6432
          ↓
          ↓ PostgreSQL Protocol
          ↓
       PostgreSQL :5432
```

### **2. Admin Request Flow (Internal)**

```
Admin Browser
   ↓
   ↓ HTTP :8181 (Docker Dev)
   ↓
UI - Internal (Admin Console)
   ↓
   ↓ HTTP :13370
   ↓
FastAPI Server
   ↓
   ├─→ Redis :6379 (Session)
   │
   └─→ PgBouncer :6432
          ↓
          ↓ PostgreSQL Protocol
          ↓
       PostgreSQL :5432
```

### **3. Database Connection String**

```python
# ✅ CORRECT - Through PgBouncer
DATABASE_URL = "postgresql+asyncpg://nv_user:password@pgbouncer:6432/ninaivalaigal"  # pragma: allowlist secret

# ❌ WRONG - Direct to Postgres (bypasses connection pooling)
DATABASE_URL = "postgresql+asyncpg://nv_user:password@postgres:5432/ninaivalaigal"  # pragma: allowlist secret
```

### **4. Sync Session (SessionLocal)**

```python
# ✅ CORRECT - Through PgBouncer
DATABASE_SYNC_URL = "postgresql://nv_user:password@pgbouncer:6432/ninaivalaigal"  # pragma: allowlist secret
engine = create_engine(DATABASE_SYNC_URL, pool_pre_ping=True)

# ❌ WRONG - Direct to Postgres
DATABASE_SYNC_URL = "postgresql://nv_user:password@postgres:5432/ninaivalaigal"  # pragma: allowlist secret
```

---

## 🚀 Deployment Architecture (Multi-Runtime)

```mermaid
graph TB
    subgraph "Development Workstation"
        subgraph "Docker Runtime (Port Base: 5432)"
            DockerDB[PostgreSQL :5432]
            DockerPgB[PgBouncer :6432]
            DockerAPI[API :13370]
        end

        subgraph "Colima Runtime (Port Base: 5442)"
            ColimaDB[PostgreSQL :5442]
            ColimaPgB[PgBouncer :6442]
            ColimaAPI[API :13380]
        end

        subgraph "Apple CLI Runtime (Port Base: 5452)"
            AppleDB[PostgreSQL :5452]
            ApplePgB[PgBouncer :6452]
            AppleAPI[API :13390]
        end
    end

    subgraph "Shared Resources"
        GHCR[GitHub Container Registry<br/>ghcr.io/arunosaur/ninaivalaigal-db]
        LocalImages[Local Image Cache<br/>nina-intelligence-db:arm64]
    end

    DockerDB -.->|Pull/Build| GHCR
    ColimaDB -.->|Pull/Build| GHCR
    AppleDB -.->|Pull/Build| GHCR

    GHCR -.->|Cache| LocalImages

    style DockerDB fill:#2196F3,color:#fff
    style ColimaDB fill:#4CAF50,color:#fff
    style AppleDB fill:#FF9800,color:#fff
    style GHCR fill:#673AB7,color:#fff
    style LocalImages fill:#9E9E9E,color:#fff
```

### **Data Flow with Caching Strategy**

```mermaid
flowchart LR
    subgraph "Client Request"
        Client[User Request]
    end

    subgraph "FastAPI Processing"
        API[API Handler]
        Cache{Check Redis<br/>Cache}
    end

    subgraph "Data Retrieval"
        Redis[(Redis Cache<br/>1h TTL)]
        PgBouncer[PgBouncer<br/>Connection Pool]
        DB[(PostgreSQL<br/>Primary Data)]
    end

    Client --> API
    API --> Cache

    Cache -->|Hit| Redis
    Redis -->|Return Cached| API

    Cache -->|Miss| PgBouncer
    PgBouncer --> DB
    DB --> PgBouncer
    PgBouncer --> API
    API -->|Update Cache| Redis

    API --> Client

    style Client fill:#e1f5ff
    style API fill:#2196F3,color:#fff
    style Cache fill:#FF9800,color:#fff
    style Redis fill:#F44336,color:#fff
    style PgBouncer fill:#FF9800,color:#fff
    style DB fill:#673AB7,color:#fff
```

### **Health Monitoring Flow**

```mermaid
graph TD
    subgraph "Monitoring System"
        HealthCheck[Health Check Endpoint<br/>/health/detailed]
        Metrics[Prometheus Metrics<br/>/metrics]
    end

    subgraph "Component Health"
        DBHealth{Database<br/>Healthy?}
        RedisHealth{Redis<br/>Healthy?}
        PgBHealth{PgBouncer<br/>Healthy?}
    end

    subgraph "Actions"
        AlertSlack[Slack Alert]
        RestartService[Auto-restart<br/>Service]
        LogError[Error Logging]
    end

    HealthCheck --> DBHealth
    HealthCheck --> RedisHealth
    HealthCheck --> PgBHealth

    DBHealth -->|No| AlertSlack
    DBHealth -->|No| RestartService
    DBHealth -->|No| LogError

    RedisHealth -->|No| AlertSlack
    RedisHealth -->|No| LogError

    PgBHealth -->|No| AlertSlack
    PgBHealth -->|No| RestartService

    style HealthCheck fill:#2196F3,color:#fff
    style Metrics fill:#4CAF50,color:#fff
    style DBHealth fill:#FF9800,color:#fff
    style RedisHealth fill:#FF9800,color:#fff
    style PgBHealth fill:#FF9800,color:#fff
    style AlertSlack fill:#F44336,color:#fff
    style RestartService fill:#673AB7,color:#fff
    style LogError fill:#9E9E9E,color:#fff
```

---

## 🎯 Design Rationale

### **Why PgBouncer for Everything?**

| Benefit | Impact |
|---------|--------|
| **Connection Pooling** | Reuse few connections for thousands of API requests |
| **Production Parity** | Dev/staging/prod all use same connection pattern |
| **Memory Efficiency** | Reduced PostgreSQL memory footprint |
| **Restart Isolation** | App can restart without affecting DB connections |
| **Consistent Monitoring** | Single choke point for all DB traffic metrics |

### **Why Split UI (External vs Internal)?**

| Reason | Benefit |
|--------|---------|
| **Security** | Admin console not exposed to public internet |
| **Routing** | Can use different domains (app.X.io vs admin.X.io) |
| **Resource Isolation** | Customer traffic doesn't affect admin operations |
| **Access Control** | Separate authentication mechanisms |
| **Compliance** | Audit trails for internal vs external access |

### **Port Allocation Strategy**

```
Base Port + Environment Offset + Runtime Offset

Examples:
- PostgreSQL Dev Docker:   5432 + 0   + 0  = 5432
- PostgreSQL Dev Colima:   5432 + 0   + 10 = 5442
- PostgreSQL Dev Apple:    5432 + 0   + 20 = 5452

- PostgreSQL Test Docker:  5432 + 100 + 0  = 5532
- PostgreSQL Test Colima:  5432 + 100 + 10 = 5542

- API Prod Docker:        13370 + 200 + 0  = 13570
```

**Benefits:**
- No port collisions across runtimes
- Can run multiple environments simultaneously
- Predictable port numbers
- Easy to remember pattern

---

## 🛡️ Production Best Practices

### **1. All DB Traffic → PgBouncer**

```yaml
# docker-compose.yml
api:
  environment:
    DATABASE_URL: "postgresql+asyncpg://${DB_USER}:${DB_PASSWORD}@pgbouncer:${PGBOUNCER_PORT}/${DB_NAME}"
  depends_on:
    - pgbouncer  # NOT postgres
```

### **2. Application Containers Connect to PgBouncer ONLY**

```
✅ api → pgbouncer:6432 → postgres:5432
❌ api → postgres:5432 directly
```

### **3. PgBouncer Config Standardization**

```ini
# pgbouncer.ini (same across all environments)
[databases]
ninaivalaigal = host=postgres port=5432 dbname=ninaivalaigal

[pgbouncer]
pool_mode = transaction
max_client_conn = 1000
default_pool_size = 25
```

### **4. UI Split Deployment**

```
# Production (Kubernetes)
app.ninaivalaigal.io       → UI-External (Public)
admin.ninaivalaigal.io     → UI-Internal (VPN/IP restricted)

# Local Development
localhost:8081             → UI-External
localhost:8181             → UI-Internal
```

---

## 📦 Container Networking

### **Docker Compose Networks**

```yaml
networks:
  ninaivalaigal-network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.28.0.0/16

services:
  postgres:
    networks:
      ninaivalaigal-network:
        ipv4_address: 172.28.0.10

  pgbouncer:
    networks:
      ninaivalaigal-network:
        ipv4_address: 172.28.0.20

  redis:
    networks:
      ninaivalaigal-network:
        ipv4_address: 172.28.0.30

  api:
    networks:
      ninaivalaigal-network:
        ipv4_address: 172.28.0.100
```

### **Service Discovery**

```
postgres:5432    → Resolved by Docker DNS to 172.28.0.10
pgbouncer:6432   → Resolved by Docker DNS to 172.28.0.20
redis:6379       → Resolved by Docker DNS to 172.28.0.30
```

---

## 🔍 Verification Commands

### **Check Connection Flow**

```bash
# 1. Verify PgBouncer is running
docker exec -it ninaivalaigal-dev-pgbouncer pgbouncer -V

# 2. Test connection through PgBouncer
psql "postgresql://nv_user:password@localhost:6432/ninaivalaigal" -c "SELECT version();"  # pragma: allowlist secret

# 3. Check active connections in PgBouncer
docker exec -it ninaivalaigal-dev-pgbouncer \
  psql -h localhost -p 6432 -U nv_user -d pgbouncer -c "SHOW POOLS;"

# 4. Verify API connects through PgBouncer
docker logs ninaivalaigal-dev-api 2>&1 | grep -i "pgbouncer\|6432"
```

### **Verify Port Allocation**

```bash
# List all ninaivalaigal containers with ports
docker ps --filter "name=ninaivalaigal" \
  --format "table {{.Names}}\t{{.Ports}}"

# Check for port collisions
netstat -an | grep -E "(5432|5532|5632|6432|6532|13370|13470|8081|8181)"
```

### **Test UI Connectivity**

```bash
# External UI
curl -I http://localhost:8081

# Internal UI (Admin)
curl -I http://localhost:8181

# API Health
curl http://localhost:13370/health
```

---

## 📚 Related Documentation

- [Database Image Management](DATABASE_IMAGE_MANAGEMENT.md)
- [Database Patterns Guide](DATABASE_PATTERNS.md)
- [Docker Compose Configuration](../compose.docker.yml)
- [Multi-Architecture Build Strategy](MULTI_ARCH_BUILD_STRATEGY.md)

---

## 🎯 Quick Reference

### **For Developers:**
```bash
# Connect to DB (through PgBouncer)
psql postgresql://nv_user:password@localhost:6432/ninaivalaigal  # pragma: allowlist secret

# Access External UI
open http://localhost:8081

# Access Admin Console
open http://localhost:8181

# Check API Health
curl http://localhost:13370/health/detailed
```

### **For DevOps:**
```bash
# View PgBouncer stats
docker exec ninaivalaigal-dev-pgbouncer \
  psql -h localhost -p 6432 -U nv_user -d pgbouncer -c "SHOW STATS;"

# Check connection pool usage
docker exec ninaivalaigal-dev-pgbouncer \
  psql -h localhost -p 6432 -U nv_user -d pgbouncer -c "SHOW POOLS;"

# Monitor PostgreSQL connections
docker exec ninaivalaigal-dev-db \
  psql -U nina -d ninaivalaigal -c \
  "SELECT count(*) FROM pg_stat_activity WHERE datname='ninaivalaigal';"
```

---

**Last Updated:** October 4, 2025, 20:30 CST
**Status:** ✅ Production-Ready Architecture
**Version:** 2.0 (PgBouncer Mandatory, UI Split)
