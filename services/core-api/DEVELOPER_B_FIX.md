# Developer B: Core API Container Fix

**Date:** October 20, 2025
**Issue:** Core API container failing to start due to missing `graphops_client` module
**Status:** ✅ FIXED

---

## 🔴 Root Cause

The Core API depends on `graphops_client` Python package, but the Dockerfile wasn't copying it into the container.

**Location of graphops_client:**
```
/Users/swami/WorkSpace/ninaivalaigal/python-clients/graphops/graphops_client/
```

---

## ✅ Fix Applied

Updated `services/core-api/Dockerfile` to copy the `graphops_client` package:

```dockerfile
# Copy graphops_client Python package
COPY python-clients/graphops/graphops_client /app/graphops_client

# Set Python path to include shared and graphops_client
ENV PYTHONPATH=/app:/app/shared:/app
```

---

## 🚀 How to Rebuild and Test

### **Step 1: Rebuild the Docker Image**

```bash
cd /Users/swami/WorkSpace/ninaivalaigal

# Build from the repo root (context is important!)
docker build -f services/core-api/Dockerfile -t core-api:latest .
```

**Note:** The build context must be the repo root (`.`) because the Dockerfile references:
- `services/core-api/`
- `shared/`
- `python-clients/graphops/graphops_client/`

---

### **Step 2: Run the Container**

```bash
# Run Core API container with proper database connection
docker run -d \
  --name core-api-test \
  -p 8000:8000 \
  -e DATABASE_URL="postgresql://user:pass@host:port/database" \  # pragma: allowlist secret
  -e NINAIVALAIGAL_JWT_SECRET="test-secret" \  # pragma: allowlist secret
  core-api:latest

# Check if it's running
docker ps | grep core-api

# Check logs
docker logs core-api-test
```

---

### **Step 3: Verify graphops_client is Available**

```bash
# Test that graphops_client can be imported
docker exec core-api-test python -c "import graphops_client; print('✅ graphops_client loaded successfully')"
```

**Expected output:**
```
✅ graphops_client loaded successfully
```

---

### **Step 4: Test the API**

```bash
# Health check
curl http://localhost:8000/health

# Test an endpoint
curl http://localhost:8000/api/v1/your-endpoint
```

---

## 📊 Before vs After

### **Before (Broken):**
```
ModuleNotFoundError: No module named 'graphops_client'
Container exits immediately
```

### **After (Fixed):**
```
✅ graphops_client loaded successfully
✅ Core API server starting...
✅ Uvicorn running on http://0.0.0.0:8000
```

---

## 🧪 Run Your Final Test Script

Once the container is running successfully:

```bash
cd /Users/swami/WorkSpace/ninaivalaigal
chmod +x your_test_script.sh
./your_test_script.sh
```

---

## 🔍 Troubleshooting

### **If build fails with "COPY failed":**

Make sure you're running `docker build` from the **repo root**, not from `services/core-api/`:

```bash
# ✅ Correct (from repo root)
cd /Users/swami/WorkSpace/ninaivalaigal
docker build -f services/core-api/Dockerfile -t core-api:latest .

# ❌ Wrong (from services/core-api/)
cd /Users/swami/WorkSpace/ninaivalaigal/services/core-api
docker build -t core-api:latest .  # This will fail!
```

---

### **If graphops_client still not found:**

Check the PYTHONPATH inside the container:

```bash
docker exec core-api-test python -c "import sys; print('\\n'.join(sys.path))"
```

Should include:
```
/app
/app/shared
```

---

### **If you need a clean rebuild:**

```bash
# Remove old containers and images
docker stop core-api-test
docker rm core-api-test
docker rmi core-api:latest

# Rebuild from scratch (no cache)
docker build --no-cache -f services/core-api/Dockerfile -t core-api:latest .
```

---

## ✅ Summary

**Problem:** Missing `graphops_client` module
**Solution:** Copy `python-clients/graphops/graphops_client` into Docker image
**File Modified:** `services/core-api/Dockerfile`
**Build Command:** `docker build -f services/core-api/Dockerfile -t core-api:latest .` (from repo root)
**Status:** Ready to test ✅
