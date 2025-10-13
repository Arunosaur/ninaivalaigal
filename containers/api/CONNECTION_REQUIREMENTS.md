# API Container Connection Requirements - Quick Reference

**For detailed documentation:** See `docs/deployment/API_CONTAINER_REQUIREMENTS.md`
**Architecture:** See `specs/086-multi-runtime-port-allocation/README.md`

---

## 🚨 Critical Rules

### 1. **PgBouncer Mandate**
```bash
# ✅ CORRECT: API → PgBouncer (port 6432) → Database
DATABASE_URL="postgresql://nina:password@${PGBOUNCER_IP}:6432/ninaivalaigal_dev"  # pragma: allowlist secret

# ❌ WRONG: API → Database directly (port 5432)
DATABASE_URL="postgresql://nina:password@${DB_IP}:5432/ninaivalaigal_dev"  # pragma: allowlist secret
```

### 2. **Dynamic IP Resolution**
```bash
# ✅ CORRECT: Extract IP from column 6
get_container_ip() {
    container list | grep "$1" | awk '{print $6}'
}

# ❌ WRONG: Extract last field (gets "MB" not IP!)
awk '{print $(NF)}'  # Returns "MB" from memory column
```

### 3. **Redis Authentication Required**
```bash
# ✅ CORRECT: Include password in Redis URL
REDIS_URL="redis://:nina_redis_dev_password@${REDIS_IP}:6379/0"  # pragma: allowlist secret

# ❌ WRONG: No password (will fail authentication)
REDIS_URL="redis://${REDIS_IP}:6379/0"
```

---

## ⚡ Quick Start

```bash
# 1. Get dynamic IPs
PGBOUNCER_IP=$(container list | grep "ninaivalaigal-dev-pgbouncer" | awk '{print $6}')
REDIS_IP=$(container list | grep "ninaivalaigal-dev-redis" | awk '{print $6}')

# 2. Build connection URLs
DATABASE_URL="postgresql://nina:dev_password_change_in_production@${PGBOUNCER_IP}:6432/ninaivalaigal_dev"  # pragma: allowlist secret
REDIS_URL="redis://:nina_redis_dev_password@${REDIS_IP}:6379/0"  # pragma: allowlist secret

# 3. Start API container
container run -d --name ninaivalaigal-dev-api \
    -p 13390:8000 \
    -e DATABASE_URL="${DATABASE_URL}" \
    -e NINAIVALAIGAL_DATABASE_URL="${DATABASE_URL}" \
    -e REDIS_URL="${REDIS_URL}" \
    -e NINAIVALAIGAL_REDIS_URL="${REDIS_URL}" \
    -e NINAIVALAIGAL_JWT_SECRET="dev_jwt_secret_change_in_production" `# pragma: allowlist secret` \
    -e NINA_ENV="dev" \
    -e PYTHONPATH=/app:/app/server \
    nina-api:arm64

# 4. Verify health
curl http://localhost:13390/health
# Expected: {"status": "ok"}
```

---

## 🔍 Troubleshooting

### API returns 500 error?
```bash
# Check logs
container logs ninaivalaigal-dev-api 2>&1 | tail -50

# Common issues:
# - "Name or service not known" → Using hostname instead of IP
# - "invalid username-password pair" → Wrong Redis password
# - "server DNS lookup failed" → PgBouncer can't find DB (wrong IP)
```

### Can't connect to Redis?
```bash
# Test Redis connection
REDIS_IP=$(container list | grep "ninaivalaigal-dev-redis" | awk '{print $6}')
redis-cli -h ${REDIS_IP} -p 6379 -a "nina_redis_dev_password" PING  # pragma: allowlist secret
# Expected: PONG

# Get actual password from container
container inspect ninaivalaigal-dev-redis | grep requirepass
```

### Can't connect to database?
```bash
# Test PgBouncer → Database connection
PGPASSWORD="dev_password_change_in_production" psql \  # pragma: allowlist secret
    -h localhost -p 6452 -U nina -d ninaivalaigal_dev \
    -c "SELECT 'PgBouncer Connected!' AS status;"
```

---

## 📦 Required Environment Variables

| Variable | Format | Example |
|----------|--------|---------|
| `DATABASE_URL` | `postgresql://user:pass@pgbouncer_ip:6432/db` | `postgresql://nina:***@192.168.64.137:6432/ninaivalaigal_dev` <!-- pragma: allowlist secret --> |
| `REDIS_URL` | `redis://:password@redis_ip:6379/0` | `redis://:***@192.168.64.105:6379/0` |
| `NINAIVALAIGAL_JWT_SECRET` | String | `dev_jwt_secret_change_in_production` |
| `NINA_ENV` | `dev`/`test`/`prod` | `dev` |
| `PYTHONPATH` | `/app:/app/server` | `/app:/app/server` |

---

## ✅ Pre-flight Checklist

Before starting API container:
- [ ] Database container running
- [ ] PgBouncer container running and connected to DB
- [ ] Redis container running with authentication
- [ ] Dynamic IPs resolved correctly
- [ ] `DATABASE_URL` uses PgBouncer IP (port 6432)
- [ ] `REDIS_URL` includes password
- [ ] Container name: `ninaivalaigal-${ENV}-api` (no runtime suffix!)

---

**Related Documentation:**
- Full guide: `docs/deployment/API_CONTAINER_REQUIREMENTS.md`
- Architecture: `specs/086-multi-runtime-port-allocation/README.md`
- Reference script: `scripts/stack-start-complete.sh`
