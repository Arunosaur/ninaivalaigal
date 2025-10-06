# 🔒 Current Working State
**Version:** v0.9-pre-phase1
**Last Updated:** October 6, 2025 - 11:09
**Purpose:** Lock down what works to prevent regressions
---

## What Works Right Now

### Infrastructure
- [x] **PostgreSQL Database (Apple CLI)** - Status: ✅ WORKING
  - Container: `ninaivalaigal-dev-db` (Apple Container CLI)
  - Image: `nina-intelligence-db:arm64`
  - Host: `localhost:5452` (Apple CLI dev port)
  - Database: `ninaivalaigal_dev`
  - User: `nina`
  - Password: `dev_password_change_in_production`  <!-- pragma: allowlist secret -->
  - Extensions: ✅ pgvector v0.5.1, ✅ Apache AGE v1.5.0
  - Status: Fully operational with all extensions loaded
  - Test: `PGPASSWORD=dev_password_change_in_production psql -h localhost -p 5452 -U nina -d ninaivalaigal_dev -c "\dx"` ✅ PASSES

- [x] **Redis Cache (Apple CLI)** - Status: ✅ WORKING
  - Container: `ninaivalaigal-dev-redis`
  - Host: `localhost:6399` (Apple CLI dev port)
  - Password: `dev_redis_password`  <!-- pragma: allowlist secret -->
  - Status: Running and accessible
  - Test: `redis-cli -h localhost -p 6399 -a dev_redis_password ping` ✅ PASSES

- [x] **Apple Container CLI** - Status: ✅ WORKING
  - Unified naming: `ninaivalaigal-{env}-{service}`
  - Port matrix followed: Apple CLI dev uses 5452 (DB), 6399 (Redis)
  - Containers running successfully

- [ ] **PgBouncer** - Status: NEEDS TESTING
  - Expected: Working or bypassed (document which)

### API Endpoints
- [ ] **Health Check** - Status: ⏭️ NOT TESTED (API not running)
  - Endpoint: `GET http://localhost:13370/health`
  - Smoke test: SKIPPED (expected)

- [ ] **User Signup** - Status: ⏭️ NOT TESTED (API not running)
  - Endpoint: `POST /auth/signup`
  - Expected: Not 404

- [ ] **User Login** - Status: ⏭️ NOT TESTED (API not running)
  - Endpoint: `POST /auth/login`
  - Expected: Returns JWT

### Database Schema
- [ ] **Migrations Applied** - Status: ❌ CHECK FAILED
  - Command: `cd server && alembic current`
  - Error: "No 'script_location' key found in configuration"
  - Fix needed: Alembic config issue

- [ ] **Tables Exist** - Status: [NEEDS CHECK]
  - Run: `psql -h localhost -U nina -d ninaivalaigal_dev -c "\dt"`
  - Tables: [NEEDS VERIFICATION]

### Extensions
- [ ] **Apache AGE** - Status: [CHECK TOMORROW]
  - Installed: Yes/No
  - Working: Yes/No
  - Graph name: `ninaivalaigal_graph`

- [ ] **pgvector** - Status: [CHECK TOMORROW]
  - Installed: Yes/No
  - Segfault issue: Resolved/Unresolved

---

## ❌ Known Broken Items

### Infrastructure Issues
- [ ] **Docker/Colima Corruption** - [DOCUMENT TOMORROW]
  - Symptom: "No such container" errors
  - Workaround: Use Apple Container CLI

- [ ] **PgBouncer Authentication** - [DOCUMENT TOMORROW]
  - Issue: May be broken or bypassed
  - Status: [DOCUMENT CURRENT STATE]

### Application Issues
- [ ] **Frontend** - Static HTML only (not production-ready)
- [ ] **Tests** - 145 test files, 0 passing
- [ ] **Graph Reasoner** - May have stability issues

---

## 🔒 DO NOT CHANGE

### Critical Files (Never modify without explicit approval)
1. `.pre-commit-config.yaml` - Pre-commit hooks configuration
2. `.git/hooks/pre-commit` - Pre-commit hook (DO NOT BYPASS)
3. `.git/hooks/pre-push` - Pre-push smoke tests (DO NOT BYPASS)
4. `alembic/versions/0111_memory_pgvector.py` - Database migration
5. `server/auth.py` - Authentication (working, don't break it)

### Stable Scripts (Modify with caution)
1. `scripts/nv-stack-start.sh` - Apple CLI startup
2. `scripts/nv-db-start.sh` - Database startup
3. `Makefile` - Build commands

---

## 📝 Change Log

### October 5, 2025
- **Created WORKING_STATE.md** - Baseline documentation
- **Created smoke tests** - `tests/smoke/test_critical_infrastructure.py`
- **Installed pre-push hook** - `.git/hooks/pre-push` (ACTIVE)
- **Tagged baseline** - `git tag v0.9-pre-phase1`

### [Next Entry]
- Date: [DATE]
- Change: [DESCRIPTION]
- Tested: Yes/No
- Rollback: `git revert [COMMIT_HASH]`

---

## 🚨 REGRESSION POLICY

### If Something Breaks:
1. **STOP** - Don't make it worse
2. **Check**: `git log --oneline -5`
3. **Rollback**: `git revert HEAD` OR `git reset --hard v0.9-pre-phase1`
4. **Document**: Add to "Known Broken Items" section
5. **Fix properly**: In a branch, test thoroughly, then merge

### Pre-Commit Hook Policy:
- ✅ **ALWAYS RESPECT** - Never bypass
- ⚠️ If it fails, fix the issue (don't skip)
- 🔴 Bypassing pre-commit has caused regressions before

### Pre-Push Hook Policy:
- ✅ **ALWAYS RESPECT** - Never bypass
- ⚠️ If smoke tests fail, you've introduced a regression
- 🔴 Fix the regression before pushing

---

## 📊 Validation Checklist

### Tomorrow's Tasks (Day 1 - Safety Net):
- [ ] 1. Fill in all [DOCUMENT TOMORROW] placeholders
- [ ] 2. Run smoke tests: `pytest tests/smoke/ -v`
- [ ] 3. Document current state accurately
- [ ] 4. Tag baseline: `git tag -a v0.9-pre-phase1 -m "Baseline before Phase 1"`
- [ ] 5. Push tag: `git push origin v0.9-pre-phase1`

---

## 🎯 End-of-Day Criteria (Day 1)

✅ **Smoke test passes 100%**
✅ **Pre-push hook active**
✅ **Working state documented and tagged**

**When all three are green, we start Phase 1: Week 1.**
