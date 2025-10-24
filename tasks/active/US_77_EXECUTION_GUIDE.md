# US #77: Step-by-Step Execution Guide

**Date:** October 22, 2025, 11:26 AM
**Executor:** You (Developer A unavailable)
**Status:** Tests 1-3 passed, Test 4 packaging + Tests 5-7 remaining

---

## ⚡ QUICK START

**Copy-paste these commands in sequence and share results with me.**

---

## 📦 STEP 1: PACKAGE ARM64 TARBALL (Test 4 completion)

```bash
# Navigate to grpc-gateway
cd /Users/swami/WorkSpace/ninaivalaigal/services/grpc-gateway

# Create ARM64 tarball
make docker-package-arm64

# Check result
ls -lh *.tar

# Get checksum
sha256sum *.tar || shasum -a 256 *.tar

# If successful, share with me:
# - File name
# - Size
# - Checksum
```

**Expected:** `ninaivalaigal-grpc-gateway-arm64.tar` created (~50-200 MB)

---

## 🔍 STEP 2: CHECK BACKEND SERVICES

```bash
# Check if backends are running
echo "=== Memory Service ==="
curl -s http://localhost:13393/health || echo "NOT RUNNING"

echo "=== GraphOps ==="
curl -s http://localhost:13398/health || echo "NOT RUNNING"

echo "=== Core API ==="
curl -s http://localhost:13390/health || echo "NOT RUNNING"
```

**If any backend is NOT RUNNING:**
- We can still do Test 4 (packaging) ✅
- Tests 5-7 require all backends running ⚠️
- **Share with me which backends are running**

---

## 🧪 STEP 3: TEST 5 - BACKEND ROUTING

**Only run if all backends are UP**

```bash
# Set GraphOps port
export GRAPHOPS_SERVICE_PORT=13398

# Navigate to scripts directory
cd /Users/swami/WorkSpace/ninaivalaigal

# Start gateway
./scripts/nv-grpc-gateway-start.sh

# In another terminal, test routing with timing
echo "=== Testing Memory Service Routing ==="
time curl -s http://localhost:13395/api/v1/memory/health

echo "=== Testing GraphOps Routing ==="
time curl -s http://localhost:13395/api/v1/graph/health

echo "=== Testing Core API Routing ==="
time curl -s http://localhost:13395/api/v1/core/health
```

**Share with me:**
- HTTP status codes
- Response times (from `time` command)
- Any errors (502, 503, etc.)
- Gateway log output

---

## 🔥 STEP 4: TEST 6 - ERROR HANDLING

**Only run if backends are available and you can restart them**

```bash
# First verify all working
curl http://localhost:13395/api/v1/memory/health
curl http://localhost:13395/api/v1/graph/health
curl http://localhost:13395/api/v1/core/health

# Stop Memory Service (use your method to stop it)
# Then test:
echo "=== Testing Failed Backend ==="
curl -v http://localhost:13395/api/v1/memory/health

# Check other backends still work
echo "=== Testing Other Backends ==="
curl http://localhost:13395/api/v1/graph/health
curl http://localhost:13395/api/v1/core/health

# Restart Memory Service
# Then verify recovery:
echo "=== Testing Recovery ==="
sleep 10
curl http://localhost:13395/api/v1/memory/health
```

**Share with me:**
- Error code when backend is down (502? 503?)
- Whether other backends stayed up
- Whether recovery was automatic
- Gateway logs during failure/recovery

---

## 📝 STEP 5: TEST 7 - LOGGING

```bash
# Start gateway with log capture
export GRAPHOPS_SERVICE_PORT=13398
./scripts/nv-grpc-gateway-start.sh 2>&1 | tee /tmp/gateway-startup.log

# In another terminal, make requests
curl http://localhost:13395/health
curl http://localhost:13395/api/v1/memory/health
curl http://localhost:13395/api/v1/graph/health

# View captured logs
cat /tmp/gateway-startup.log
```

**Share with me:**
- First ~50 lines of startup logs
- Sample request/response log entries
- Whether logs show backend addresses
- Whether logs show routing decisions

---

## 🎯 ALTERNATIVE: MINIMAL VALIDATION

**If backends are not available, we can still validate:**

✅ **Test 4 (Packaging):** Run Step 1 only
- This completes the ARM64 build validation
- Documents the tarball artifact
- Marks Test 4 as complete

📝 **Document Results:**
- I'll update validation guide with packaging results
- Mark Test 4 as passed
- Note that Tests 5-7 require backend availability
- Update Taiga US #77 with current status

**We'll have 4 of 7 tests complete (57%)**

---

## 🤝 HOW TO WORK WITH ME

**For Each Step:**
1. Run the commands
2. Copy the output
3. Paste it in chat
4. I'll analyze and document the results

**I Can:**
- ✅ Interpret results
- ✅ Update validation guide
- ✅ Update Taiga US #77
- ✅ Document findings
- ✅ Identify issues
- ✅ Suggest fixes

**I Cannot:**
- ❌ Execute commands on your system
- ❌ Start/stop services
- ❌ Access your network
- ❌ Interact with Docker directly

---

## 🚀 LET'S START

**Recommend starting with Step 1 (packaging):**
- Quick (1-2 minutes)
- Doesn't require backends
- Completes Test 4
- Gives us a quick win

**Then we can assess backend availability for Tests 5-7.**

---

**Ready to begin! Share the output of Step 1 and we'll proceed together.** 🎯
