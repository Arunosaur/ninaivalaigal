# Port Correction Plan - SPEC-086 Compliance

## Current Issues (October 7, 2025)

### Ports Not Following SPEC-086

| Service | Current Port | SPEC-086 Port | Status | Action Required |
|---------|--------------|---------------|--------|-----------------|
| PostgreSQL | 5452 | 5452 | ✅ Correct | None |
| PgBouncer | Not bound | 6452 | ❌ Missing | Rebind with -p 6452:6432 |
| Redis | 6399 | 6399 | ✅ Correct | None |
| API | 13390 | 13390 | ✅ Correct | None |
| Customer UI | 8100 | 8101 | ❌ Wrong | Rebind with -p 8101:8101 |
| Admin Console | 8101 | 8201 | ❌ Wrong | Rebind with -p 8201:8102 |

## SPEC-086 Reference

**Formula**: `Final Port = Base Port + Environment Offset + Runtime Offset`

**Apple CLI Dev (Runtime Offset = +20, Env Offset = 0):**
- PostgreSQL: 5432 + 0 + 20 = **5452** ✅
- PgBouncer: 6432 + 0 + 20 = **6452** ❌
- Redis: 6379 + 0 + 20 = **6399** ✅
- API: 13370 + 0 + 20 = **13390** ✅
- UI-External: 8081 + 0 + 20 = **8101** ❌
- UI-Internal: 8181 + 0 + 20 = **8201** ❌

## Corrective Actions

### 1. Fix PgBouncer Port
```bash
container stop ninaivalaigal-dev-pgbouncer
container delete ninaivalaigal-dev-pgbouncer
container run -d --name ninaivalaigal-dev-pgbouncer -p 6452:6432 \
  -e DB_HOST=192.168.64.188 \
  -e DB_PORT=5432 \
  -e DB_NAME=ninaivalaigal_dev \
  -e DB_USER=nina \
  -e DB_PASSWORD=dev_password_change_in_production \
  nina-pgbouncer:arm64
```

### 2. Fix Customer UI Port
```bash
container stop ninaivalaigal-dev-ui-customer
container delete ninaivalaigal-dev-ui-customer
container run -d --name ninaivalaigal-dev-ui-customer -p 8101:8101 \
  nina-customer-ui:arm64
```

### 3. Fix Admin Console Port
```bash
container stop ninaivalaigal-dev-ui-admin
container delete ninaivalaigal-dev-ui-admin
container run -d --name ninaivalaigal-dev-ui-admin -p 8201:8102 \
  nina-admin-console:arm64
```

### 4. Update API to Use Correct PgBouncer Port
```bash
container stop ninaivalaigal-dev-api
container delete ninaivalaigal-dev-api
container run -d --name ninaivalaigal-dev-api -p 13390:8000 \
  -e DATABASE_URL="postgresql://nina:dev_password_change_in_production@192.168.64.208:6432/ninaivalaigal_dev" \
  -e NINAIVALAIGAL_DATABASE_URL="postgresql://nina:dev_password_change_in_production@192.168.64.208:6432/ninaivalaigal_dev" \
  -e REDIS_URL="redis://:dev_redis_password@192.168.64.189:6379/0" \
  -e NINAIVALAIGAL_JWT_SECRET="dev-secret-change-in-production" \
  -e PYTHONPATH=/app:/app/server \
  -e ENVIRONMENT=development \
  nina-api:arm64
```

## Verification Commands

```bash
# Check all ports are correct
lsof -nP -iTCP -sTCP:LISTEN | grep -E "(5452|6452|6399|13390|8101|8201)" | awk '{print $1, $9}' | sort -u

# Expected output:
# container *:5452   (PostgreSQL)
# container *:6452   (PgBouncer)
# container *:6399   (Redis)
# container *:13390  (API)
# container *:8101   (Customer UI)
# container *:8201   (Admin Console)
```

## Service Access URLs (Corrected)

```
Database (PostgreSQL):  localhost:5452
PgBouncer:              localhost:6452
Redis:                  localhost:6399
API:                    http://localhost:13390
  - Health:             http://localhost:13390/health
  - Swagger:            http://localhost:13390/docs
Customer UI:            http://localhost:8101
Admin Console:          http://localhost:8201
Enhanced Memory:        http://localhost:7070
```

## Why This Matters

1. **Zero Port Collisions**: Enables running Docker (base ports), Colima (+10), and Apple (+20) simultaneously
2. **Predictable Ports**: Team can calculate ports using the formula
3. **Production Parity**: Same port strategy across dev/test/prod
4. **Documentation Accuracy**: All documentation references correct ports

## Update Required Files

After fixing ports, update these files:
- ✅ `docs/CONTAINER_ARCHITECTURE.md` - Update port table
- ✅ `docs/CONTAINER_BUILD_DEPLOYMENT_GUIDE.md` - Update deployment commands
- ✅ `scripts/nina-intelligence-stack-start-unified.sh` - Verify uses get-port.sh
- ✅ README files with service URLs

---

**Priority**: 🔴 High
**Impact**: Medium (services work but violate SPEC)
**Effort**: Low (simple container restart with correct ports)
