# Testing Guide: Centralized bcrypt Helper & Auth Refactoring

**For**: Future developers working on authentication features
**Date**: 2025-10-30
**Context**: Developer A's centralized bcrypt helper implementation

---

## ⚠️ CRITICAL: Always Run Both Unit AND Integration Tests

Before claiming work is complete, you MUST run and pass:
1. ✅ **Unit Tests** (fast, no setup): 39 tests
2. ✅ **Integration Tests** (requires services): 2 tests

**Total**: 41 tests must pass before work is considered complete.

---

## 🧪 Unit Tests (No Services Required)

### Quick Start

```bash
cd /Users/swami/WorkSpace/ninaivalaigal
source /opt/homebrew/anaconda3/etc/profile.d/conda.sh
conda activate nina
export NINAIVALAIGAL_JWT_SECRET="test_jwt_secret"  # pragma: allowlist secret
cd services/core-api
pytest tests/auth/ -v
```

### Expected Output

```
========================= 39 passed in 6.5s =========================
```

### What Gets Tested

- `test_password_utils.py` (9 tests): bcrypt hash/verify functions
- `test_auth_core.py` (14 tests): JWT tokens, password validation
- `test_middleware.py` (12 tests): RBAC middleware, permissions
- `test_signup_login_flow.py` (4 tests): Signup/login with password hashing

---

## 🔌 Integration Tests (Requires Running Services)

### Prerequisites Check

```bash
# 1. Verify all containers are running
container list | grep ninaivalaigal-dev

# Expected output:
# ninaivalaigal-dev-db
# ninaivalaigal-dev-pgbouncer-tx
# ninaivalaigal-dev-pgbouncer-sess
# ninaivalaigal-dev-core-api
# ninaivalaigal-dev-redis
```

### Configuration Setup

```bash
# 1. Get Core API container IP
CORE_API_IP=$(container inspect ninaivalaigal-dev-core-api | grep IPAddress | tail -1 | awk -F'"' '{print $4}')
echo "Core API IP: $CORE_API_IP"

# 2. Update .env.test with the container IP
# Edit file: /Users/swami/WorkSpace/ninaivalaigal/.env.test
# Update this line:
CORE_API_BASE_URL=http://192.168.66.131:8000  # Use YOUR container IP

# 3. Verify database credentials in .env.test:
DATABASE_URL=postgresql://nina:dev_password_change_in_production@localhost:6432/ninaivalaigal_dev  # pragma: allowlist secret
```

### Run Integration Tests

```bash
cd /Users/swami/WorkSpace/ninaivalaigal
conda activate nina
source .env.test
pytest tests/integration/test_auth_pgbouncer.py -v
```

### Expected Output

```
========================= 2 passed in 2.1s ==========================
```

### What Gets Tested

- `test_signup_persists_bcrypt_hash`: Full signup flow through Core API → PgBouncer → PostgreSQL
- `test_login_updates_last_login`: Login flow with last_login timestamp update

---

## 🚨 Common Mistakes & Fixes

### Mistake #1: Only Running Unit Tests

**Problem**: Developer claims "all tests pass" but only ran unit tests (39/41 tests)

**Impact**: Integration issues not caught (wrong DB creds, missing API endpoints, etc.)

**Fix**: Always run BOTH unit AND integration tests

---

### Mistake #2: Wrong CORE_API_BASE_URL

**Symptom**: Integration tests skip with "Core API not reachable"

**Cause**: Using `http://localhost:8000` instead of container IP

**Fix**:
```bash
# Get correct container IP
container inspect ninaivalaigal-dev-core-api | grep IPAddress
# Update .env.test with the IP
CORE_API_BASE_URL=http://192.168.66.131:8000
```

---

### Mistake #3: Wrong Database Credentials

**Symptom**: Integration tests skip with "SASL authentication failed"

**Cause**: Using `postgres:postgres` instead of actual dev credentials

**Fix**: Update `.env.test`:
```bash
POSTGRES_USER=nina
POSTGRES_PASSWORD=dev_password_change_in_production  # pragma: allowlist secret
POSTGRES_DB=ninaivalaigal_dev
DATABASE_URL=postgresql://nina:dev_password_change_in_production@localhost:6432/ninaivalaigal_dev  # pragma: allowlist secret
```

---

### Mistake #4: Wrong Python Environment

**Symptom**: Import errors, missing dependencies

**Cause**: Using system Python instead of conda nina environment

**Fix**:
```bash
source /opt/homebrew/anaconda3/etc/profile.d/conda.sh
conda activate nina
which python  # Should show: /opt/homebrew/anaconda3/envs/nina/bin/python
```

---

## ✅ Complete Testing Checklist

Before claiming work complete, verify:

- [ ] Unit tests run: `pytest tests/auth/ -v`
- [ ] Unit tests pass: 39 passed
- [ ] All containers running: `container list | grep ninaivalaigal-dev`
- [ ] Container IP obtained and `.env.test` updated
- [ ] Integration tests run: `pytest tests/integration/test_auth_pgbouncer.py -v`
- [ ] Integration tests pass: 2 passed
- [ ] **Total: 41 tests passing**
- [ ] Screenshot/log of test results saved
- [ ] Taiga US updated with test commands and results

---

## 📊 Success Criteria

```bash
# Final validation command
echo "=== Unit Tests ===" && \
cd services/core-api && pytest tests/auth/ -v --tb=line && \
echo "" && echo "=== Integration Tests ===" && \
cd ../.. && source .env.test && pytest tests/integration/test_auth_pgbouncer.py -v --tb=line

# Expected output:
# === Unit Tests ===
# ========================= 39 passed =========================
# === Integration Tests ===
# ========================= 2 passed ==========================
```

---

## 📚 Additional Resources

- **Integration Test README**: `/tests/integration/README.md`
- **Test Configuration**: `/.env.test`
- **Unit Test Location**: `/services/core-api/tests/auth/`
- **Integration Test Location**: `/tests/integration/test_auth_pgbouncer.py`

---

**Remember**: Tests that skip are NOT tests that pass. If a test skips, investigate why!
