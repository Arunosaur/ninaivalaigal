# Developer A: Auth Test Suite Fixes
## 17 Failures → Systematic Resolution Plan

**Current Status**: 72 tests, 19 passed, 36 skipped, 17 failed
**Goal**: Fix high-priority failures to get to 50+ passing tests

---

## 🔴 **Priority 1: Missing Token Endpoints (Causes 8+ failures)**

### **Issue**: Tests expect `/auth/refresh` and `/auth/validate` but get 404

**Root Cause**: `token_api.py` has these endpoints under `/auth/` prefix but they're not the right routes:
- Tests expect: `/auth/refresh` (token refresh)
- Tests expect: `/auth/validate` (token validation)
- Current: `/auth/regenerate-token` (wrong endpoint name)

### **Fix**: Add missing endpoints to `routers/signup_api.py`

```python
# Add to routers/signup_api.py after the login endpoint

@router.post("/auth/refresh", tags=["auth"])
async def refresh_token(
    refresh_token: str,
    db: DatabaseManager = Depends(get_db)
):
    """
    Refresh JWT access token using refresh token

    Expected by test_token_refresh.py
    """
    from auth import validate_refresh_token, generate_jwt_token

    try:
        # Validate refresh token
        user_id = validate_refresh_token(refresh_token)

        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token"
            )

        # Get user from database
        from auth import get_user_by_uuid
        user = get_user_by_uuid(db, user_id)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )

        # Generate new access token
        new_access_token = generate_jwt_token(user)

        return {
            "access_token": new_access_token,
            "token_type": "bearer",
            "message": "Token refreshed successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to refresh token"
        )


@router.post("/auth/validate", tags=["auth"])
async def validate_token(
    token: str = Body(..., embed=True)
):
    """
    Validate JWT access token

    Expected by test_token_validation.py
    """
    from auth import verify_token

    try:
        token_data = verify_token(token)

        if not token_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token"
            )

        return {
            "valid": True,
            "user_id": token_data.user_id,
            "username": token_data.username,
            "message": "Token is valid"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token validation error: {e}")
        return {
            "valid": False,
            "message": "Token validation failed"
        }
```

---

## 🟡 **Priority 2: Validation Errors Return 400 Instead of 422**

### **Issue**: Missing/empty password returns 400, tests expect 422

**Root Cause**: FastAPI default validation returns 422, but something is catching it and returning 400.

### **Fix**: Add custom exception handler to `main.py`

```python
# Add to main.py after app creation

from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Ensure validation errors return 422 (not 400)

    This is what tests expect for missing/invalid fields
    """
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": exc.errors(),
            "body": exc.body
        }
    )
```

---

## 🟠 **Priority 3: Signup 500 Errors → Proper Status Codes**

### **Issue**: Signup failures returning 500 instead of 409/422

**Current problems**:
- Duplicate email: 500 (should be 409 Conflict)
- Validation errors: 500 (should be 422)
- Server errors: 500 (correct, but need better messaging)

### **Fix**: Improve error handling in `signup_api.py`

```python
# Update create_individual_user function in auth.py

def create_individual_user(signup_data: IndividualUserSignup):
    """Create individual user account"""
    db = get_db()
    session = db.get_session()

    try:
        # Validate input data
        validated_data = {
            "email": validate_email(signup_data.email),
            "password": signup_data.password,
            "name": signup_data.name,
            "account_type": signup_data.account_type,
        }

        # Check if user already exists (409 Conflict)
        existing_user = db.get_user_by_email(validated_data["email"])
        if existing_user:
            raise HTTPException(
                status_code=409,  # Changed from 400
                detail="User with this email already exists"
            )

        # Validate password (422 Unprocessable Entity)
        if not validate_password(validated_data["password"]):
            raise HTTPException(
                status_code=422,  # Changed from 400
                detail=PASSWORD_REQUIREMENTS_MESSAGE
            )

        # ... rest of function ...

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        session.rollback()
        logger.error(f"User creation failed: {e}")
        # Only raise 500 for unexpected errors
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create user: {str(e)}"
        )
    finally:
        session.close()
```

### **Also update signup endpoint in `signup_api.py`**

```python
@router.post("/auth/signup/individual", tags=["auth"])
async def signup_individual_user(
    signup_data: IndividualUserSignup,
    db: DatabaseManager = Depends(get_db)
):
    """Individual user signup"""
    try:
        result = create_individual_user(signup_data)

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,  # Not 200
            content=result
        )

    except HTTPException as e:
        # Pass through HTTP exceptions with correct status codes
        raise
    except Exception as e:
        logger.error(f"Signup error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during signup"
        )
```

---

## 🟢 **Priority 4: Security Test Failures (XSS, Replay, etc.)**

### **Issue**: Security tests return 422/500/404 instead of proper rejection

**Tests expecting**:
- XSS payloads: Should be sanitized (200) or rejected (400/422)
- JWT "none" algorithm: Should be rejected (401)
- Token replay: Should be detected and rejected (401/403)

### **Fix A: XSS Sanitization**

Add input sanitization to `auth.py`:

```python
import html

def sanitize_input(text: str) -> str:
    """Sanitize user input to prevent XSS"""
    if not text:
        return text
    # HTML escape to prevent XSS
    return html.escape(text.strip())

# Update validate_email to sanitize
def validate_email(email: str) -> str:
    """Validate and sanitize email format"""
    email = sanitize_input(email)
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    if not re.match(pattern, email):
        raise HTTPException(status_code=422, detail="Invalid email format")
    return email.lower()

# Update create_individual_user to sanitize name
validated_data = {
    "email": validate_email(signup_data.email),
    "password": signup_data.password,
    "name": sanitize_input(signup_data.name),  # Sanitize name
    "account_type": signup_data.account_type,
}
```

### **Fix B: JWT "none" Algorithm Protection**

Update `auth.py` verify_token:

```python
def verify_token(token: str) -> TokenData:
    """Verify JWT token and return token data"""
    try:
        # Decode with algorithm whitelist (prevents "none" algorithm attack)
        payload = jwt.decode(
            token,
            JWT_SECRET,
            algorithms=[JWT_ALGORITHM],  # Only HS256, not "none"
            options={"verify_signature": True}  # Enforce signature verification
        )

        username: str = payload.get("email")
        user_id: str = payload.get("user_id")

        if username is None or user_id is None:
            return None

        return TokenData(username=username, user_id=user_id)

    except jwt.InvalidTokenError:
        return None
```

### **Fix C: Token Replay Detection** (Advanced - Optional)

Add JTI (JWT ID) tracking to prevent replay:

```python
# In generate_jwt_token, add unique JTI
import uuid

def generate_jwt_token(user: Any, ...) -> str:
    """Generate JWT with unique JTI for replay protection"""
    payload: dict[str, Any] = {
        "user_id": str(user_id),
        "email": email,
        "jti": str(uuid.uuid4()),  # Unique token ID
        # ... other claims ...
    }
    # ... rest of function ...

# In verify_token, check if JTI has been used (requires Redis/DB)
def verify_token(token: str) -> TokenData:
    """Verify token and check for replay"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])

        jti = payload.get("jti")
        if jti:
            # TODO: Check if JTI already used (requires token blacklist in Redis)
            # if is_token_used(jti):
            #     return None
            pass

        # ... rest of validation ...
    except jwt.InvalidTokenError:
        return None
```

---

## 📋 **Implementation Checklist**

### **Phase 1: Missing Endpoints** (30 minutes)
- [ ] Add `/auth/refresh` endpoint to `signup_api.py`
- [ ] Add `/auth/validate` endpoint to `signup_api.py`
- [ ] Import necessary auth functions
- [ ] Test: `curl -X POST http://localhost:13370/auth/refresh -d '{"refresh_token":"test"}'`

### **Phase 2: Status Code Fixes** (20 minutes)
- [ ] Add validation exception handler to `main.py`
- [ ] Update duplicate email to return 409
- [ ] Update password validation to return 422
- [ ] Update signup success to return 201

### **Phase 3: Security Hardening** (40 minutes)
- [ ] Add `sanitize_input()` function
- [ ] Update `validate_email()` to sanitize
- [ ] Update user creation to sanitize name
- [ ] Add algorithm whitelist to `verify_token()`
- [ ] Add signature verification enforcement

### **Phase 4: Validation** (15 minutes)
- [ ] Restart API: `PORT=13370 python services/core-api/local_run.py`
- [ ] Run tests: `pytest tests/auth/ -v --tb=short`
- [ ] Target: 40+ passing (up from 19)

---

## 🚀 **Quick Implementation Script**

```bash
# 1. Stop current API
# Ctrl+C in terminal where API is running

# 2. Make the code changes above
# Edit: services/core-api/routers/signup_api.py
# Edit: services/core-api/main.py
# Edit: services/core-api/auth.py

# 3. Restart API on test port
cd /Users/swami/WorkSpace/ninaivalaigal
conda activate nina

export NINAIVALAIGAL_JWT_SECRET="dev-secret-change-in-production"  # pragma: allowlist secret
export DATABASE_URL="postgresql://nina:dev_password_change_in_production@localhost:6452/ninaivalaigal_dev"  # pragma: allowlist secret
export PORT=13370

python services/core-api/local_run.py

# 4. In another terminal, run tests
conda activate nina
cd /Users/swami/WorkSpace/ninaivalaigal

export CORE_API_BASE_URL="http://localhost:13370"
pytest tests/auth/ -v --tb=short

# 5. Expected improvement
# Before: 19 passed, 17 failed
# After: 40+ passed, <10 failed
```

---

## 📊 **Expected Test Results After Fixes**

| Category | Before | After | Fixes Applied |
|----------|--------|-------|---------------|
| **Token Refresh** | 0/8 (404) | 6/8 | Added `/auth/refresh` endpoint |
| **Token Validation** | 0/5 (404) | 4/5 | Added `/auth/validate` endpoint |
| **Login Validation** | 2/5 (400) | 5/5 | Fixed 422 status codes |
| **Signup Errors** | 1/6 (500) | 5/6 | Proper 409/422/201 codes |
| **Security Tests** | 0/8 (various) | 4/8 | XSS sanitization, JWT hardening |
| **TOTAL** | **19/72** | **45+/72** | **~40% → 63%** |

---

## 🐛 **Common Pitfalls to Avoid**

1. **Don't forget imports**: `from fastapi import Body, status` for new endpoints
2. **Exception order matters**: HTTPException must be caught before general Exception
3. **Status codes matter**: Tests are strict about 409 vs 422 vs 500
4. **Test port**: Make sure API runs on 13370 (tests expect this)
5. **Module shim**: local_run.py handles auth imports, don't break the shim

---

## 📞 **If You Get Stuck**

**Debugging Commands**:
```bash
# Check what endpoints are registered
curl http://localhost:13370/openapi.json | jq '.paths | keys'

# Test specific endpoint
curl -X POST http://localhost:13370/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token":"test"}'

# Check validation error format
curl -X POST http://localhost:13370/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com"}' \
  -v

# Run single test
pytest tests/auth/test_token_refresh.py::TestTokenRefresh::test_token_refresh_with_valid_refresh_token -v
```

**Common Errors**:
- `ModuleNotFoundError: No module named 'auth'` → Restart with local_run.py (not directly with uvicorn)
- `404 Not Found` → Check router is included in main.py: `app.include_router(signup_api.router)`
- `500 Internal Server Error` → Check API logs for actual error
- Tests still skip → Check `CORE_API_BASE_URL` env var is set

---

**Good luck, Developer A!** 🚀 These fixes should get you from 19 passing to 45+ passing tests.

Let me know when you hit the next blocker!
