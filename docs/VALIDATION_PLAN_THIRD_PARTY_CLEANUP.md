# Validation Plan: Third-Party Code Cleanup

**Date:** October 19, 2025
**Change:** Removed 229 embedded third-party files (client-tools/, vscode-client/)
**Risk Level:** LOW (verified no code dependencies)

---

## 🎯 What Was Changed

### **Removed:**
- `client-tools/` - 113 files (mem0 CLI + vendored Python packages)
- `vscode-client/` - 116 files (mem0 VSCode extension + node_modules)

### **Kept:**
- `mem0ai>=0.1.0,<1.0.0` in `requirements/base.in` ✅
- All custom code that uses mem0ai via HTTP ✅
- All container definitions ✅

### **Updated:**
- `.gitignore` - Added exclusions for third-party tools

---

## ✅ Pre-Validation Checks (Already Done)

1. ✅ Verified 0 Python imports from removed directories
2. ✅ Verified 0 references in service code
3. ✅ Verified 0 references in Dockerfiles
4. ✅ Verified containers use `pip install mem0ai` (not the removed tools)
5. ✅ Verified no Makefile dependencies

---

## 🧪 Validation Test Suite

### **Phase 1: Basic Sanity (5 minutes)**

```bash
# 1. Verify services start without errors
make stack-up

# Expected: All 6 services start successfully
# ✅ nv-db (PostgreSQL)
# ✅ nv-redis
# ✅ nv-pgbouncer
# ✅ nv-api (core-api)
# ✅ memory-service (Rust)
# ✅ grpc-gateway (Go)
```

### **Phase 2: Health Checks (2 minutes)**

```bash
# 2. Check all service health endpoints
make health-check

# Expected: All services respond with 200 OK
# ✅ http://localhost:13390/health (API)
# ✅ http://localhost:13393/health (Memory Service)
# ✅ http://localhost:13395/health (gRPC Gateway)
```

### **Phase 3: Database Connectivity (2 minutes)**

```bash
# 3. Verify database connections
psql -h localhost -p 5432 -U postgres -d ninaivalaigal -c "SELECT version();"

# Expected: PostgreSQL version displayed

# 4. Verify Redis connectivity
redis-cli -h localhost -p 6379 PING

# Expected: PONG
```

### **Phase 4: API Functionality (5 minutes)**

```bash
# 5. Test authentication endpoints
curl -X POST http://localhost:13390/api/v1/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Test123!","name":"Test User"}'  # pragma: allowlist secret

# Expected: 201 Created with user object

# 6. Test memory endpoints (if mem0ai is actually used)
curl http://localhost:13390/api/v1/memory/memories \
  -H "Authorization: Bearer <token>"

# Expected: 200 OK with memory list
```

### **Phase 5: Container Rebuilds (10 minutes)**

```bash
# 7. Rebuild API container (uses mem0ai package)
cd services/core-api
docker build -t ninaivalaigal-api:test .

# Expected: Build succeeds, pip install mem0ai works

# 8. Verify mem0ai package is installed in container
docker run --rm ninaivalaigal-api:test pip list | grep mem0

# Expected: mem0ai version displayed
```

### **Phase 6: Go Services (5 minutes)**

```bash
# 9. Rebuild and test Go services (should be unaffected)
cd go-services/grpc-gateway
go build -o grpc-gateway .

# Expected: Clean build, 0 errors

cd ../load-tester
go build -o load-tester .

# Expected: Clean build, 0 errors

cd ../cli-tools
go build -o nina-cli .

# Expected: Clean build, 0 errors
```

### **Phase 7: Rust Memory Service (5 minutes)**

```bash
# 10. Rebuild Rust memory service (should be unaffected)
cd rust-services/memory-service
cargo build --release

# Expected: Clean build, 0 errors

# 11. Run Rust tests
cargo test

# Expected: All tests pass
```

---

## 🔍 What to Look For (Red Flags)

### **❌ Build Failures:**
- "Cannot find module 'client-tools'" → Should NOT happen (we verified no imports)
- "Cannot find module 'vscode-client'" → Should NOT happen (we verified no imports)
- "mem0ai package not found" → Should NOT happen (it's in requirements.txt)

### **❌ Runtime Errors:**
- 500 errors from API → Check logs for import errors
- Services failing to start → Check for missing dependencies
- Database connection errors → Unrelated to this change

### **✅ Expected Behavior:**
- All services start normally
- All health checks pass
- No errors mentioning "client-tools" or "vscode-client"
- mem0ai package is available if needed (via pip)

---

## 📋 Test Checklist

Execute each test and mark status:

- [ ] **Phase 1:** Stack startup (`make stack-up`)
- [ ] **Phase 2:** Health checks (`make health-check`)
- [ ] **Phase 3:** Database connectivity (psql + redis-cli)
- [ ] **Phase 4:** API endpoints (auth + memory)
- [ ] **Phase 5:** Container rebuilds (API with mem0ai)
- [ ] **Phase 6:** Go services rebuild (all 3 services)
- [ ] **Phase 7:** Rust service rebuild + tests

**Pass Criteria:** 7/7 phases pass without errors related to removed directories

---

## 🚨 Rollback Plan (If Needed)

If validation fails and you need to revert:

```bash
# 1. Revert the commit
git log --oneline -1  # Get commit hash
git revert <commit-hash>

# 2. Restore removed directories
git checkout HEAD~1 -- client-tools/
git checkout HEAD~1 -- vscode-client/

# 3. Test again
make stack-up
make health-check
```

**Note:** Rollback should NOT be necessary - we verified no dependencies exist.

---

## 📊 Expected Timeline

| Phase | Duration | Critical |
|-------|----------|----------|
| Phase 1: Stack startup | 5 min | ✅ YES |
| Phase 2: Health checks | 2 min | ✅ YES |
| Phase 3: DB connectivity | 2 min | ✅ YES |
| Phase 4: API functionality | 5 min | ⚠️ Medium |
| Phase 5: Container rebuilds | 10 min | ⚠️ Medium |
| Phase 6: Go services | 5 min | ⬜ Low |
| Phase 7: Rust service | 5 min | ⬜ Low |
| **Total** | **~35 min** | |

**Minimum Validation:** Phases 1-3 must pass (critical services)
**Full Validation:** All 7 phases (recommended)

---

## ✅ Sign-Off

**Validation Completed By:** _______________
**Date:** _______________
**All Tests Passed:** [ ] YES  [ ] NO
**Issues Found:** _______________
**Production Ready:** [ ] YES  [ ] NO

---

## 📝 Notes

- If you don't use mem0ai in your code, Phase 4-5 tests may be N/A
- Go and Rust services should be completely unaffected
- The removed code was never referenced in our codebase
- All dependencies are properly managed via pip/npm/cargo/go mod

**Ready to validate?** Start with `make stack-up` and work through each phase.
