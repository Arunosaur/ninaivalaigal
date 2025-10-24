# US #77: Quick Reference Card

**Status:** 4 of 7 tests passed | **Next:** Package + Tests 5-7

---

## ⚡ IMMEDIATE ACTIONS

### **1. Package Tarball** (5 min)
```bash
cd services/grpc-gateway
make docker-package-arm64
ls -lh *.tar
sha256sum *.tar
```
**Document:** Path, size, checksum in validation guide

---

### **2. Start Backends** (Pre-test)
```bash
# Ensure these are running:
curl http://localhost:13393/health  # Memory
curl http://localhost:13398/health  # GraphOps (port 13398!)
curl http://localhost:13390/health  # Core API
```

---

### **3. Set GraphOps Port** (Important!)
```bash
export GRAPHOPS_SERVICE_PORT=13398
# NOT 50051 - that was default gRPC display
```

---

## 🧪 TEST EXECUTION

### **Test 5: Routing** (15 min)
```bash
# Start gateway
export GRAPHOPS_SERVICE_PORT=13398
./nv-grpc-gateway-start.sh

# Test routing (capture timings)
time curl http://localhost:13395/api/v1/memory/health
time curl http://localhost:13395/api/v1/graph/health
time curl http://localhost:13395/api/v1/core/health
```
**Capture:** Timings, status codes, log samples

---

### **Test 6: Error Handling** (10 min)
```bash
# Stop Memory Service
# Test failure
curl -v http://localhost:13395/api/v1/memory/health

# Verify other backends OK
curl http://localhost:13395/api/v1/graph/health

# Restart Memory, verify recovery
curl http://localhost:13395/api/v1/memory/health
```
**Capture:** Error codes, recovery time, logs

---

### **Test 7: Logging** (10 min)
```bash
# Start with log capture
./nv-grpc-gateway-start.sh 2>&1 | tee gateway-startup.log

# Make requests
curl http://localhost:13395/health
curl http://localhost:13395/api/v1/memory/health
```
**Capture:** Log samples section-by-section

---

## 📝 WHAT TO DOCUMENT

**For Each Test:**
- ✅ Timings (response times, overhead)
- ✅ Failure modes (error codes, behavior)
- ✅ Log samples (section-by-section)
- ✅ Observations (notes, issues)

**Templates:** All in `US_77_VALIDATION_GUIDE.md`

---

## 🎯 SUCCESS CHECKLIST

- [ ] Tarball packaged and documented
- [ ] Test 5: No 502/503 errors
- [ ] Test 6: Graceful failure/recovery
- [ ] Test 7: Quality logs captured
- [ ] All templates filled in validation guide
- [ ] Taiga US #77 updated

---

## ⚠️ KEY REMINDERS

1. **GraphOps port is 13398** (not 50051)
2. **Always set:** `export GRAPHOPS_SERVICE_PORT=13398`
3. **Capture timings** for all tests
4. **Document log samples** section-by-section
5. **Update both** validation guide AND Taiga

---

**Time:** ~50 minutes total
**Status:** Ready to execute
**Quality:** 100% pass rate (4/4 tests so far)
