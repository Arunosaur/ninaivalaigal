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
  [Traefik Gateway]
      ├─> /api/*      → Core API (8000)
      ├─> /business/* → Business Service (8001)
      ├─> /memory/*   → Memory Service (13393)
      ├─> /graph/*    → GraphOps (13394)
      ├─> /health     → Gateway Health
      └─> /metrics    → Prometheus Metrics
```

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

| Path | Target | Port | Description |
|------|--------|------|-------------|
| `/api/*` | Core API | 8000 | Authentication, Users, Teams |
| `/business/*` | Business Service | 8001 | Business logic |
| `/memory/*` | Memory Service | 13393 | Memory operations |
| `/graph/*` | GraphOps | 13394 | Graph intelligence |
| `/health` | Gateway | - | Health check |
| `/metrics` | Prometheus | - | Metrics endpoint |

---

## 🛡️ Security Features

### Rate Limiting
- **Average:** 100 requests/second
- **Burst:** 50 requests
- **Period:** 1 second

### CORS Configuration
- Allowed origins: localhost:3000, localhost:8080
- Allowed methods: GET, POST, PUT, DELETE, PATCH, OPTIONS
- Max age: 100 seconds

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
# Core API
curl http://localhost/api/health

# Business Service
curl http://localhost/business/health

# Memory Service
curl http://localhost/memory/health

# GraphOps
curl http://localhost/graph/health
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

**Last Updated:** October 20, 2025
**Developer:** Developer C
**Task:** #83 - API Gateway Deployment
