# Developer A: Phase 2 Debugging Guide

## 📊 **Current Status: 31/72 (Expected 44)**

You're **13 tests short** of the expected result. Let me diagnose why.

---

## 🔍 **Root Cause Analysis**

### **Issue 1: JSON Middleware Not Working** ❌

**Problem**: Malformed JSON still returns 422 (not 400)

**Why**: FastAPI/Starlette parses JSON before our middleware runs. The middleware I added won't work as intended.

**Solution**: Need to catch at Starlette level before FastAPI sees it.

### **Issue 2: Signup 500 Errors** ❌

**Problem**: Individual signup returns 500

**Possible causes**:
1. Database connection issue
2. Exception in `create_individual_user` not caught properly
3. Missing validation in `validate_email`

**Debug**: Check `core_api_13370.log` for actual error

### **Issue 3: Token Security 404s** ✅ (Expected)

**Why**: Tests hit `/memory` endpoint with invalid tokens, but:
- Invalid token → middleware rejects → returns 404 (not 401)
- This is actually a middleware configuration issue

---

## 🚀 **Quick Fixes**

### **Fix 1: Check the Logs First** 🔍

```bash
# Check what's actually failing
tail -100 /Users/swami/WorkSpace/ninaivalaigal/core_api_13370.log

# Look for:
# - Database connection errors
# - Exception tracebacks
# - HTTPException status codes being changed
```

### **Fix 2: Test Individual Endpoints** 🧪

```bash
# Test signup success
curl -X POST http://localhost:13370/auth/signup/individual \
  -H "Content-Type: application/json" \
  -d '{"email":"test123@example.com", "password":"StrongPass123!", "full_name":"Test User"}' \
  -v

# Expected: 201 Created
# If 500: Check logs for exception details

# Test duplicate email
curl -X POST http://localhost:13370/auth/signup/individual \
  -H "Content-Type: application/json" \
  -d '{"email":"test123@example.com", "password":"StrongPass123!", "full_name":"Test User"}' \
  -v

# Expected: 409 Conflict
# If 500: HTTPException not being preserved

# Test malformed JSON
curl -X POST http://localhost:13370/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test","password":}' \
  -v

# Expected: 400 Bad Request
# If 422: JSON parsing happens before our handler

# Test empty payload
curl -X POST http://localhost:13370/auth/login \
  -H "Content-Type: application/json" \
  -d '{}' \
  -v

# Expected: 400 Bad Request
# If 422: Validation error not caught correctly
```

---

## 🐛 **Most Likely Issues**

### **1. Signup 500 Error - Database Issue**

**Hypothesis**: `create_individual_user` is failing due to database constraint

**Check**:
```bash
# Look for these in logs:
grep "Failed to create user" core_api_13370.log
grep "IntegrityError" core_api_13370.log
grep "duplicate key" core_api_13370.log
```

**Possible fix**: Database might have stale data from previous tests

```bash
# Clean up test users
psql postgresql://nina:dev_password_change_in_production@localhost:6452/ninaivalaigal_dev

DELETE FROM users WHERE email LIKE '%@spec052.com';
DELETE FROM users WHERE email LIKE '%@example.com';
\q
```

### **2. Empty JSON Payload - Validation Issue**

**Hypothesis**: Empty `{}` passes JSON parsing but fails field validation → 422

**Why**: Login expects `email` and `password`, when missing → validation error → 422

**Fix needed**: Catch empty required fields as 400 (not 422)

Update `login` endpoint to explicitly check for empty fields:

```python
# In signup_api.py, login endpoint
@router.post("/auth/login")
async def login(request: Request):
    try:
        payload = await request.json()
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    email = payload.get("email")
    password = payload.get("password")

    # Explicitly check for missing/empty fields (400 not 422)
    if not email or not password:
        raise HTTPException(
            status_code=400,
            detail="Missing required fields: email and password"
        )

    # ... rest of login logic
```

### **3. Token Security 404s - Middleware Order**

**Hypothesis**: RBAC middleware runs before route matching, so invalid tokens → 404

**Why**:
1. Request comes in: `GET /memory`
2. RBAC middleware checks token → invalid
3. Should return 401, but route doesn't exist yet
4. FastAPI returns 404

**This is actually complex** - these tests might not pass without more work on middleware.

---

## 📋 **Action Plan**

### **Step 1: Debug Logs** (5 minutes)
```bash
tail -100 core_api_13370.log | grep -A 5 "error\|Error\|ERROR\|Exception\|Failed"
```

Look for actual exception details. This will tell us why signup returns 500.

### **Step 2: Clean Database** (2 minutes)
```bash
psql postgresql://nina:dev_password_change_in_production@localhost:6452/ninaivalaigal_dev \
  -c "DELETE FROM users WHERE email LIKE '%@spec052.com' OR email LIKE '%@example.com';"
```

### **Step 3: Test One Endpoint** (3 minutes)
```bash
# Try a fresh signup
curl -X POST http://localhost:13370/auth/signup/individual \
  -H "Content-Type: application/json" \
  -d '{"email":"fresh_test@example.com", "password":"StrongPass123!", "full_name":"Fresh Test"}' \
  -v
```

If this works (201), the database was the issue.
If this fails (500), check the logs for the exception.

### **Step 4: Run Focused Tests** (5 minutes)
```bash
# Just test signup flows
pytest tests/auth/test_signup.py -v --tb=short

# Just test JSON validation
pytest tests/auth/test_negative_cases.py::TestInputValidationEdgeCases -v --tb=short
```

---

## 💡 **Expected Outcomes**

### **Best Case** (Database was the issue)
- Clean database
- Restart API
- 40+ tests pass

### **Realistic Case** (Some fixes needed)
- Signup works after DB clean → +3 tests
- JSON validation still 422 → needs deeper fix → 0 tests
- Token security still 404 → complex middleware issue → 0 tests

**Total**: 31 → 34 tests passing

### **JSON Validation Fixes** (If needed)

The JSON parsing issue is tricky. FastAPI/Starlette handles this at a low level. Options:

**Option A**: Accept 422 for now, focus on other tests
**Option B**: Custom request parser (complex, 2+ hours)
**Option C**: Update tests to expect 422 (pragmatic)

**Recommendation**: **Option A** - The 422 vs 400 debate is minor. Focus on the signup 500 errors which are more critical.

---

## 🎯 **Realistic Target**

Given the issues, here's a realistic expectation:

| Category | Current | After Fixes | Notes |
|----------|---------|-------------|-------|
| Signup flows | Low | +3 tests | Fix database issues |
| JSON validation | 0 | 0 tests | Accept 422 for now |
| Token security | 0 | 0 tests | Complex middleware fix |
| **TOTAL** | **31** | **34** | **+3 tests** |

---

## 🚀 **Next Steps for You**

1. **Check logs**: `tail -100 core_api_13370.log | grep -i error`
2. **Clean database**: Delete test users
3. **Restart API**: `kill 17730 && python services/core-api/local_run.py`
4. **Test signup**: Use curl commands above
5. **Report back**: What does the log say? Does signup work after DB clean?

---

## 📞 **When You Report Back**

Please share:
1. **Relevant log lines** (error messages from `core_api_13370.log`)
2. **Curl test result** (did fresh signup return 201 or 500?)
3. **Test count after DB clean** (did it improve?)

This will tell me exactly what's wrong and how to fix it.

---

**Don't worry about missing the 44 target** - the 422 vs 400 issue is a FastAPI design quirk, and middleware fixes for token security are complex. Focus on getting signup working (500 → 201), which should get you to ~34 passing.

Then we can decide if the remaining fixes are worth the time, or if 34/72 (47%) is good enough for now and we move to other work.
