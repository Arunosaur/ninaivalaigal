# Traefik API Gateway

**Task #83: Deploy API Gateway (Traefik)**
**Status:** Implementation Phase
**Developer:** Developer C

---

## 🎯 Overview

Traefik serves as the unified entry point for all Ninaivalaigal microservices, providing:

- **Unified Routing** - Single endpoint for all services
- **Load Balancing** - Distribute traffic across instances
- **SSL/TLS** - Automatic Let's Encrypt certificates
- **Rate Limiting** - Protect against abuse
- **Observability** - Metrics, logging, tracing
- **Service Discovery** - Automatic Docker container discovery

---

## 🏗️ Architecture

```
Client Request
      ↓
  [Traefik Gateway :80/443]
      ├─> /api/auth, /api/users, /api/teams, /api/orgs, /api/acl
      │   → Core API (ninaivalaigal-dev-core-api:8000)
      ├─> /api/billing, /api/usage, /api/analytics
      │   → Business Service (ninaivalaigal-dev-business-service:8000)
      ├─> /api/admin, /api/vendor
      │   → Admin/Vendor Service (ninaivalaigal-dev-admin-vendor-service:8000)
      ├─> /api/memory, /api/recall
      │   → Memory Service (ninaivalaigal-dev-memory-service:8000)
      ├─> /api/graph, /api/intelligence
      │   → Graph Service (ninaivalaigal-dev-graph-service:8000)
      ├─> /grpc
      │   → gRPC Gateway (ninaivalaigal-dev-grpc-gateway:13395)
      ├─> /health, /ping
      │   → Gateway Health Check
      └─> /metrics
          → Prometheus Metrics
```

**Path Routing:** All `/api/*` paths are routed to appropriate microservices per SPEC-100 architecture.

---

## 🚀 Quick Start

### Start Gateway

```bash
# Using script
./scripts/gateway-start.sh

# Or using make
make gateway-up
```

### Check Status

```bash
./scripts/gateway-status.sh
```

### Stop Gateway

```bash
./scripts/gateway-stop.sh
```

---

## 📁 Configuration Files

### `traefik.yml` - Static Configuration

Main Traefik configuration including:
- Entry points (HTTP/HTTPS)
- Providers (Docker, File)
- Certificate resolvers (Let's Encrypt)
- Logging and metrics

### `dynamic.yml` - Dynamic Routing

Service routing rules including:
- Router definitions
- Service backends
- Middlewares (rate limiting, CORS, security)
- Health checks

### `docker-compose.yml` - Deployment

Container deployment configuration with:
- Port mappings
- Volume mounts
- Network configuration
- Health checks

---

## 🔗 Routes

| Path Pattern | Target Service | Container | Port | Description |
|--------------|----------------|-----------|------|-------------|
| `/api/auth`, `/api/users`, `/api/teams`, `/api/orgs`, `/api/acl` | Core API | ninaivalaigal-dev-core-api | 8000 | Authentication, Users, Teams, Organizations, ACL |
| `/api/billing`, `/api/usage`, `/api/analytics` | Business Service | ninaivalaigal-dev-business-service | 8000 | Billing, Usage Analytics |
| `/api/admin`, `/api/vendor` | Admin/Vendor Service | ninaivalaigal-dev-admin-vendor-service | 8000 | Admin Console, Vendor Management |
| `/api/memory`, `/api/recall` | Memory Service | ninaivalaigal-dev-memory-service | 8000 | Memory CRUD operations (Rust) |
| `/api/graph`, `/api/intelligence` | Graph Service | ninaivalaigal-dev-graph-service | 8000 | Graph Intelligence, AI operations |
| `/grpc` | gRPC Gateway | ninaivalaigal-dev-grpc-gateway | 13395 | gRPC to REST translation |
| `/health`, `/ping` | Gateway | Internal | - | Gateway health check |
| `/metrics` | Prometheus | Internal | - | Prometheus metrics endpoint |

---

## 🛡️ Security Features

### Rate Limiting
- **Average:** 100 requests/second
- **Burst:** 50 requests
- **Period:** 1 second

### CORS Configuration
- Allowed origins: localhost:3000, localhost:8080, localhost:8081, localhost:8181
- Allowed methods: GET, POST, PUT, DELETE, PATCH, OPTIONS
- Allowed headers: Authorization, Content-Type, X-Requested-With, *
- Max age: 3600 seconds (1 hour)

### Security Headers
- SSL redirect enabled
- HSTS with 1-year max age
- X-Frame-Options: DENY
- X-Content-Type-Options: nosniff
- XSS Protection enabled

### Request Limits
- Max body size: 10MB

---

## 📊 Monitoring

### Dashboard

Access Traefik dashboard at: http://localhost:8080

Features:
- Service overview
- Router status
- Middleware configuration
- Health checks
- Traffic statistics

### Metrics

Prometheus metrics available at: http://localhost/metrics

Key metrics:
- `traefik_entrypoint_requests_total` - Total requests
- `traefik_entrypoint_request_duration_seconds` - Request duration
- `traefik_service_requests_total` - Service-level requests
- `traefik_backend_requests_total` - Backend requests

### Health Check

Gateway health: http://localhost/health

---

## 📝 Logging

### Access Logs

Location: `/var/log/traefik/access.log`

Format: JSON with fields:
- Request method, path, status
- Response time
- Client IP
- User agent
- Referer

### Application Logs

Location: `/var/log/traefik/traefik.log`

Format: JSON with levels:
- INFO - General information
- WARN - Warnings
- ERROR - Errors

### View Logs

```bash
# Real-time logs
docker logs -f ninaivalaigal-gateway

# Last 100 lines
docker logs --tail 100 ninaivalaigal-gateway

# Access logs
docker exec ninaivalaigal-gateway cat /var/log/traefik/access.log

# Traefik logs
docker exec ninaivalaigal-gateway cat /var/log/traefik/traefik.log
```

---

## 🔧 Configuration

### Environment Variables

None required for basic setup. SSL certificates are auto-managed by Let's Encrypt.

### Custom Configuration

Edit `dynamic.yml` to:
- Add new routes
- Modify middlewares
- Adjust rate limits
- Configure CORS origins

Changes are detected automatically (file provider watch enabled).

---

## 🧪 Testing

### Test Gateway Health

```bash
curl http://localhost/health
```

### Test Service Routes

```bash
# Gateway Health
curl http://localhost/health

# Core API
curl http://localhost/api/auth/health
curl http://localhost/api/users/health

# Business Service
curl http://localhost/api/billing/health

# Memory Service
curl http://localhost/api/memory/health

# Graph Service
curl http://localhost/api/graph/health

# Metrics
curl http://localhost/metrics
```

### Load Testing

```bash
# Using Apache Bench
ab -n 1000 -c 10 http://localhost/api/health

# Using wrk
wrk -t4 -c100 -d30s http://localhost/api/health
```

---

## 🐛 Troubleshooting

### Gateway Not Starting

1. Check Docker is running: `docker info`
2. Check ports are available: `lsof -i :80 -i :443 -i :8080`
3. Check logs: `docker logs ninaivalaigal-gateway`

### Services Not Routing

1. Verify network: `docker network ls | grep ninaivalaigal`
2. Check service discovery: Visit dashboard at http://localhost:8080
3. Verify service health in `dynamic.yml`

### SSL Certificate Issues

1. Check ACME logs: `docker logs ninaivalaigal-gateway | grep acme`
2. Verify domain DNS points to server
3. Ensure ports 80/443 are accessible externally

### High Latency

1. Check metrics: http://localhost/metrics
2. Review access logs for slow endpoints
3. Verify backend service health
4. Check rate limiting configuration

---

## 🔄 Updates

### Reload Configuration

Configuration reloads automatically when files change.

Manual reload:
```bash
docker restart ninaivalaigal-gateway
```

### Update Traefik Version

1. Edit `docker-compose.yml`
2. Change image version: `traefik:v2.X`
3. Restart gateway: `./scripts/gateway-stop.sh && ./scripts/gateway-start.sh`

---

## 📚 Additional Resources

- [Traefik Documentation](https://doc.traefik.io/traefik/)
- [Docker Provider](https://doc.traefik.io/traefik/providers/docker/)
- [Let's Encrypt](https://doc.traefik.io/traefik/https/acme/)
- [Prometheus Metrics](https://doc.traefik.io/traefik/observability/metrics/prometheus/)

---

## ✅ Checklist

- [ ] Gateway starts successfully
- [ ] Dashboard accessible
- [ ] All routes working
- [ ] Health checks passing
- [ ] Metrics available
- [ ] Logs properly formatted
- [ ] Rate limiting functional
- [ ] CORS configured
- [ ] SSL certificates obtained (production)

---

**Last Updated:** November 7, 2025
**Developer:** Developer F
**Task:** US#83 - API Gateway Path Routing (Traefik)
**Status:** ✅ Configuration Complete - Ready for Testing
**SPECs:** SPEC-099, SPEC-100
