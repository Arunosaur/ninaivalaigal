# Container Dependency Management Protocol

## 🚨 CRITICAL: Why This Document Exists

**This document exists because we keep having the SAME recurring issue:**
- API containers crash due to missing dependencies (e.g., `structlog`)
- We rebuild containers but forget `--no-cache`, leading to stale dependency layers
- Stack goes down frequently, causing development delays
- We waste time debugging the same problem repeatedly

## 🔒 MANDATORY PROTOCOL

### 1. **ALWAYS Use Validated Build Process**

```bash
# ✅ CORRECT: Use the validated build script
make build-api

# ❌ WRONG: Direct container build (bypasses validation)
container build -t nina-api:arm64 -f Dockerfile.api .
```

### 2. **NEVER Skip --no-cache After Dependency Changes**

The validated build script automatically uses `--no-cache`, but if you must build manually:

```bash
# ✅ CORRECT: Forces fresh dependency installation
container build --no-cache -t nina-api:arm64 -f Dockerfile.api .

# ❌ WRONG: Uses cached layers that may be missing new dependencies
container build -t nina-api:arm64 -f Dockerfile.api .
```

### 3. **ALWAYS Verify Dependencies After Build**

The validated build script automatically checks dependencies, but for manual verification:

```bash
# Check if specific dependency is installed
container run --rm nina-api:arm64 pip list | grep structlog

# Test critical imports
container run --rm nina-api:arm64 python -c "import structlog; print('✅ structlog works')"
```

## 🔍 Root Cause Analysis

### Why This Keeps Happening

1. **Container Layer Caching**: Docker/Container CLI caches layers to speed up builds
2. **Stale Dependency Layers**: When we add new dependencies to `requirements.txt`, the cached `pip install` layer doesn't see them
3. **Silent Failures**: Container builds succeed but are missing new dependencies
4. **Cascade Failures**: Missing dependencies cause API crashes, bringing down the entire stack

### The Technical Details

```dockerfile
# This layer gets cached
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt  # ← This layer is cached!

# If requirements.txt changes but we don't use --no-cache,
# the pip install layer is reused and new dependencies are missed
```

## 🛡️ Prevention Measures

### 1. Automated Build Validation

We've created `scripts/build-and-validate-api.sh` that:
- ✅ Always uses `--no-cache`
- ✅ Verifies critical dependencies are installed
- ✅ Tests critical imports
- ✅ Validates main application imports
- ✅ Checks requirements.txt consistency

### 2. Makefile Integration

```bash
# Use this for all API builds
make build-api

# Only use this if you understand the risks
make build-api-unsafe
```

### 3. Container Health Monitoring

We have `scripts/nv-container-health.sh` that:
- Monitors container health
- Auto-restarts failed containers
- Provides detailed diagnostics

## 📋 Troubleshooting Checklist

When the API container fails to start:

1. **Check container logs**:
   ```bash
   container logs nv-api
   ```

2. **Look for import errors** (like `ModuleNotFoundError: No module named 'structlog'`)

3. **Verify dependencies in the image**:
   ```bash
   container run --rm nina-api:arm64 pip list | grep [missing-dependency]
   ```

4. **Rebuild with validation**:
   ```bash
   make build-api
   ```

5. **Test the rebuilt container**:
   ```bash
   container run --rm nina-api:arm64 python -c "import [missing-dependency]; print('✅ works')"
   ```

## 🔄 Standard Operating Procedure

### When Adding New Dependencies

1. **Add to requirements.txt**
2. **Rebuild with validation**: `make build-api`
3. **Verify the build passed all validation steps**
4. **Test the stack**: `make stack-up && make stack-status`
5. **Commit both requirements.txt and any related code changes**

### When Stack Goes Down Unexpectedly

1. **Check stack status**: `make stack-status`
2. **Check container logs**: `container logs nv-api`
3. **Look for dependency-related errors**
4. **If dependency missing, rebuild**: `make build-api`
5. **Restart stack**: `make stack-up`

## 🚫 What NOT to Do

- ❌ Never use `container build` without `--no-cache` after dependency changes
- ❌ Never skip dependency verification after building
- ❌ Never assume a successful build means all dependencies are present
- ❌ Never ignore import errors in container logs
- ❌ Never use `make build-api-unsafe` unless you understand the risks

## 📝 Remember This

**Container layer caching is the enemy when dependencies change!**

The build may succeed, but your container will be missing dependencies because Docker/Container CLI reused the old `pip install` layer. Always use `--no-cache` or the validated build script.

## 🎯 Success Metrics

You'll know this protocol is working when:
- ✅ API containers start successfully after rebuilds
- ✅ No more `ModuleNotFoundError` in container logs
- ✅ Stack stays up consistently
- ✅ We stop having this same conversation repeatedly

---

**This document should be consulted EVERY TIME we have container dependency issues. If we're still having the same problems, we're not following this protocol.**
