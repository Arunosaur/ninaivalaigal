# API Documentation Index

**Centralized reference for all API documentation endpoints**

---

## 🚀 Microservices (FastAPI - Auto-generated)

### Core API Service
**Port:** 13390
**Base URL:** `http://localhost:13390`

- 📖 **Swagger UI:** http://localhost:13390/docs
- 📄 **ReDoc:** http://localhost:13390/redoc
- 📋 **OpenAPI Schema:** http://localhost:13390/openapi.json

**Features:** Authentication, Users, Teams, Organizations

---

### Business Service
**Port:** 13391
**Base URL:** `http://localhost:13391`

- 📖 **Swagger UI:** http://localhost:13391/docs
- 📄 **ReDoc:** http://localhost:13391/redoc
- 📋 **OpenAPI Schema:** http://localhost:13391/openapi.json

**Features:** Billing, Usage Analytics, Admin Intelligence

---

### Admin/Vendor Service
**Port:** 13392
**Base URL:** `http://localhost:13392`

- 📖 **Swagger UI:** http://localhost:13392/docs
- 📄 **ReDoc:** http://localhost:13392/redoc
- 📋 **OpenAPI Schema:** http://localhost:13392/openapi.json

**Features:** Vendor Administration, Staff Management

---

### Memory Service (Rust)
**Port:** 13393
**Base URL:** `http://localhost:13393`
**Status:** 🔨 Not yet deployed

- 📖 **Swagger UI:** http://localhost:13393/docs (when deployed)
- 📄 **ReDoc:** http://localhost:13393/redoc (when deployed)
- 📋 **OpenAPI Schema:** http://localhost:13393/openapi.json (when deployed)

**Features:** Memory CRUD operations (Rust implementation)

---

### Graph/AI Service
**Port:** 13394
**Base URL:** `http://localhost:13394`

- 📖 **Swagger UI:** http://localhost:13394/docs
- 📄 **ReDoc:** http://localhost:13394/redoc
- 📋 **OpenAPI Schema:** http://localhost:13394/openapi.json

**Features:** Graph Intelligence, AI Reasoning, Apache AGE integration

**Note:** All endpoints now under `/api/v1/graph/*` prefix (SPEC-100 compliant)

---

### API Gateway (Go gRPC)
**Port:** 13395
**Base URL:** `http://localhost:13395`
**Protocol:** gRPC

**gRPC Exploration:**
```bash
# List available services
grpcurl -plaintext localhost:13395 list

# Describe a service
grpcurl -plaintext localhost:13395 describe <service>

# Call a method
grpcurl -plaintext -d '{}' localhost:13395 <service>/<method>
```

**Features:** REST-to-gRPC translation, Protocol Buffer messaging

---

## 🔧 Infrastructure Services

### Taiga Project Management
**Port:** 9000
**Base URL:** `http://localhost:9000`

- 🌐 **Web UI:** http://localhost:9000/
- 📖 **API Root:** http://localhost:9000/api/v1/
- 🔐 **Authentication:** Bearer token (get from web UI)

**Login Credentials:**
- Username: `admin`
- Password: `admin123`  <!-- pragma: allowlist secret -->

**Popular Endpoints:**
```bash
# List projects
GET http://localhost:9000/api/v1/projects/

# List tasks
GET http://localhost:9000/api/v1/tasks/

# List user stories
GET http://localhost:9000/api/v1/userstories/

# Authenticate
POST http://localhost:9000/api/v1/auth/
{
  "username": "admin",
  "password": "admin123",  # pragma: allowlist secret
  "type": "normal"
}
```

**API Framework:** Django REST Framework (DRF)

---

## 📊 Database Services

### PostgreSQL (Main Database)
**Port:** 5452 (Apple Container CLI dev)
**Connection:** Direct SQL access

```bash
# Connect via psql
psql -h localhost -p 5452 -U nina -d ninaivalaigal_dev

# Or via container
container exec -it ninaivalaigal-dev-db psql -U nina -d ninaivalaigal_dev
```

---

### Redis (Cache & Sessions)
**Port:** 6399 (Apple Container CLI dev)
**Connection:** redis-cli

```bash
# Connect via redis-cli
redis-cli -h localhost -p 6399

# Or via container
container exec -it ninaivalaigal-dev-redis redis-cli
```

---

## 🧪 Developer Tools

### Load Tester (Go)
**Port:** 13396
**Base URL:** `http://localhost:13396`

**CLI Usage:**
```bash
# Run load test
./load-tester --target http://localhost:13390/health --requests 1000 --concurrency 10

# Validate service
./load-tester validate http://localhost:13390
```

---

### CLI Tools (Go)
**Port:** 13397
**Base URL:** `http://localhost:13397`

**CLI Usage:**
```bash
# Interactive mode
./cli-tools

# Specific commands
./cli-tools health-check
./cli-tools deploy --service core-api
```

---

## 📝 API Standards

### SPEC-100 Compliance

All microservices follow SPEC-100 API structure:

**URL Pattern:** `/api/v{version}/{service}/{resource}`

**Examples:**
- `/api/v1/auth/login`
- `/api/v1/users/profile`
- `/api/v1/graph/intelligence`
- `/api/v1/billing/subscriptions`

**Health Endpoints (All Services):**
- `GET /api/v1/{service}/health` - Liveness check
- `GET /api/v1/{service}/ready` - Readiness check
- `GET /api/v1/{service}/metrics` - Prometheus metrics

---

## 🔍 Quick Reference

### By Port

| Port  | Service | Swagger Docs |
|-------|---------|--------------|
| 13390 | Core API | http://localhost:13390/docs |
| 13391 | Business | http://localhost:13391/docs |
| 13392 | Admin/Vendor | http://localhost:13392/docs |
| 13393 | Memory (Rust) | 🔨 Not deployed |
| 13394 | Graph/AI | http://localhost:13394/docs |
| 13395 | Gateway (gRPC) | Use grpcurl |
| 13396 | Load Tester | CLI tool |
| 13397 | CLI Tools | CLI tool |
| 9000  | Taiga | http://localhost:9000/api/v1/ |

### By Technology

**FastAPI (Python):**
- Core API, Business, Admin/Vendor, Graph/AI
- Auto-generated Swagger UI at `/docs`
- Auto-generated ReDoc at `/redoc`

**Rust:**
- Memory Service (not yet deployed)
- Will use OpenAPI spec generation

**Go:**
- Gateway (gRPC reflection)
- Load Tester (CLI)
- CLI Tools (CLI)

**Django (Taiga):**
- Django REST Framework
- API at `/api/v1/`
