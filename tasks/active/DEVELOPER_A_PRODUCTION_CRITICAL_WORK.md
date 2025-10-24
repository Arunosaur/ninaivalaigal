# Developer A - Production-Critical Work Plan

**Created:** October 22, 2025, 3:30 PM
**Context:** While Developer C completes SPEC-099/100 documentation (Oct 23-24)
**Timeline:** 2 days parallel work
**Priority:** P0 - BLOCKING PRODUCTION

---

## 🚨 **CRITICAL FINDING**

**Production is NOT ready. Users cannot:**
- ❌ Sign up for accounts
- ❌ Log in to the platform
- ❌ Administrators cannot administer

**Root Cause:** Authentication & user management incomplete despite SPEC-006 (User Management) being documented

---

## 📊 **TAIGA ANALYSIS - PRODUCTION BLOCKERS**

### **Critical User Stories (Status: NOT DONE)**

| US # | Subject | Status | Assigned | Priority |
|------|---------|--------|----------|----------|
| **#20** | User signup with bcrypt | New | Unassigned | **P0** |
| **#21** | User login with password verification | New | Unassigned | **P0** |
| **#45** | JWT authentication integrated | Ready | Developer A | **P0** |

### **Additional Incomplete (80 total US, 42 NOT done)**

**By Status:**
- **New:** 13 items (mostly unassigned)
- **Ready:** 28 items (many assigned to Developer A)
- **In Progress:** 1 item (US #79 - Developer C)
- **Done:** 38 items (48%)

**Key Finding:** 52% of work is incomplete, with critical auth gaps

---

## 🎯 **RECOMMENDED WORK FOR DEVELOPER A (Oct 23-24)**

### **Priority 0: User Authentication System** ⚠️ **BLOCKS EVERYTHING**

**Why Critical:**
- Without signup/login, no one can use the platform
- Admin features useless without admin accounts
- All other features depend on authenticated users

**Tasks:**

#### **1. Complete User Signup (US #20)**

**Current State:**
- SPEC-006: Documented (signup, login, auth flows)
- Signup flow documented but not working
- Password hashing with bcrypt planned but not functional

**Implementation Required:**
```python
# server/auth_api.py or server/signup_api.py

from passlib.hash import bcrypt
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
import jwt
from datetime import datetime, timedelta

router = APIRouter()

@router.post("/auth/signup")
async def signup(
    email: str,
    password: str,
    full_name: str,
    account_type: str = "individual",
    db: Session = Depends(get_db)
):
    """
    User signup endpoint
    - Hash password with bcrypt
    - Create user in database
    - Generate JWT token
    - Return token + user info
    """
    # Check if user exists
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        raise HTTPException(400, "Email already registered")

    # Hash password
    password_hash = bcrypt.hash(password)

    # Create user
    user = User(
        email=email,
        password_hash=password_hash,
        full_name=full_name,
        account_type=account_type,
        created_at=datetime.utcnow()
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Generate JWT
    token = generate_jwt_token(user)

    return {
        "token": token,
        "user": {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "account_type": user.account_type
        }
    }
```

**Deliverables:**
- [ ] `/auth/signup` endpoint functional
- [ ] Password hashing with bcrypt working
- [ ] User created in database successfully
- [ ] JWT token generated and returned
- [ ] Manual test: curl signup → get token
- [ ] Update US #20 to "Done"

**Time Estimate:** 4 hours

---

#### **2. Complete User Login (US #21)**

**Current State:**
- Login flow documented
- Password verification planned but not working
- JWT token generation incomplete

**Implementation Required:**
```python
@router.post("/auth/login")
async def login(
    email: str,
    password: str,
    db: Session = Depends(get_db)
):
    """
    User login endpoint
    - Verify password against hash
    - Update last_login timestamp
    - Retrieve user roles
    - Generate JWT with roles
    - Return token
    """
    # Find user
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(401, "Invalid credentials")

    # Verify password
    if not bcrypt.verify(password, user.password_hash):
        raise HTTPException(401, "Invalid credentials")

    # Update last login
    user.last_login = datetime.utcnow()
    db.commit()

    # Get user roles (RBAC)
    roles = get_user_roles(user.id, db)

    # Generate JWT with roles
    token = generate_jwt_token(user, roles=roles)

    return {
        "token": token,
        "user": {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "roles": roles
        }
    }
```

**Deliverables:**
- [ ] `/auth/login` endpoint functional
- [ ] Password verification working
- [ ] Last login timestamp updated
- [ ] RBAC roles retrieved
- [ ] JWT token with roles generated
- [ ] Manual test: signup → login → get token
- [ ] Update US #21 to "Done"

**Time Estimate:** 4 hours

---

#### **3. JWT Authentication Middleware (US #45)**

**Current State:**
- Status: Ready (assigned to Developer A)
- JWT integration planned but not complete
- Auth middleware exists but may not be wired correctly

**Implementation Required:**
```python
# server/auth_middleware.py

from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt

security = HTTPBearer()

async def verify_jwt_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """
    Verify JWT token and return decoded payload
    Used as dependency for protected endpoints
    """
    try:
        token = credentials.credentials
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=["HS256"]
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(401, "Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(401, "Invalid token")

# Usage in protected endpoints
@router.get("/memory/list")
async def list_memories(
    current_user: dict = Depends(verify_jwt_token)
):
    user_id = current_user["user_id"]
    # ... rest of endpoint
```

**Deliverables:**
- [ ] JWT verification middleware working
- [ ] Protected endpoints use `Depends(verify_jwt_token)`
- [ ] Token expiration handled correctly
- [ ] Invalid token errors returned properly
- [ ] Manual test: login → use token → access protected endpoint
- [ ] Update US #45 to "Done"

**Time Estimate:** 3 hours

---

#### **4. Admin Account Setup**

**Current State:**
- Admin features exist but no way to create admin users
- RBAC system exists but admin role not assignable

**Implementation Required:**
```python
# server/admin_setup.py or management command

async def create_admin_user(
    email: str,
    password: str,
    db: Session
):
    """
    Create initial admin user
    - Hash password
    - Create user with admin role
    - Can be run via management command or script
    """
    password_hash = bcrypt.hash(password)

    user = User(
        email=email,
        password_hash=password_hash,
        full_name="Administrator",
        account_type="organization",
        created_at=datetime.utcnow()
    )
    db.add(user)
    db.commit()

    # Assign admin role
    admin_role = db.query(Role).filter(Role.name == "admin").first()
    if not admin_role:
        admin_role = Role(name="admin", permissions=["*"])
        db.add(admin_role)
        db.commit()

    user_role = UserRole(user_id=user.id, role_id=admin_role.id)
    db.add(user_role)
    db.commit()

    print(f"Admin user created: {email}")
```

**Deliverables:**
- [ ] Management command to create admin user
- [ ] Admin role properly assigned
- [ ] Admin can log in and access admin features
- [ ] Document admin setup process
- [ ] Manual test: create admin → login → access admin panel

**Time Estimate:** 2 hours

---

### **Priority 1: API Health & Production Readiness**

#### **5. API Health Checks**

**Current State:**
- Health endpoints may exist but not comprehensive
- No validation that auth system is working

**Implementation:**
```python
@router.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """
    Comprehensive health check
    - Database connectivity
    - Redis connectivity
    - Auth system status
    """
    checks = {
        "status": "healthy",
        "checks": {}
    }

    # Database
    try:
        db.execute("SELECT 1")
        checks["checks"]["database"] = "healthy"
    except Exception as e:
        checks["status"] = "unhealthy"
        checks["checks"]["database"] = f"unhealthy: {str(e)}"

    # Redis
    try:
        redis_client.ping()
        checks["checks"]["redis"] = "healthy"
    except Exception as e:
        checks["checks"]["redis"] = f"unhealthy: {str(e)}"

    # Auth system
    try:
        # Verify JWT secret is set
        if not settings.JWT_SECRET:
            raise Exception("JWT_SECRET not configured")
        checks["checks"]["auth"] = "healthy"
    except Exception as e:
        checks["status"] = "unhealthy"
        checks["checks"]["auth"] = f"unhealthy: {str(e)}"

    return checks
```

**Deliverables:**
- [ ] `/health` endpoint returns comprehensive status
- [ ] Database, Redis, Auth checks included
- [ ] Returns 200 if healthy, 503 if unhealthy
- [ ] Manual test: curl /health → verify all checks pass

**Time Estimate:** 2 hours

---

#### **6. Production Environment Validation**

**Tasks:**
```bash
# Create validation script
#!/bin/bash

echo "🔍 Production Readiness Validation"
echo ""

# 1. Test signup
echo "Testing user signup..."
SIGNUP_RESPONSE=$(curl -s -X POST http://localhost:8080/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123","full_name":"Test User"}')

if echo "$SIGNUP_RESPONSE" | grep -q "token"; then
    echo "✅ Signup working"
    TOKEN=$(echo "$SIGNUP_RESPONSE" | jq -r '.token')
else
    echo "❌ Signup failed"
    exit 1
fi

# 2. Test login
echo "Testing user login..."
LOGIN_RESPONSE=$(curl -s -X POST http://localhost:8080/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123"}')

if echo "$LOGIN_RESPONSE" | grep -q "token"; then
    echo "✅ Login working"
else
    echo "❌ Login failed"
    exit 1
fi

# 3. Test protected endpoint
echo "Testing protected endpoint..."
PROTECTED_RESPONSE=$(curl -s -X GET http://localhost:8080/memory/list \
  -H "Authorization: Bearer $TOKEN")

if echo "$PROTECTED_RESPONSE" | grep -q "error"; then
    echo "❌ Protected endpoint failed"
    exit 1
else
    echo "✅ Protected endpoint working"
fi

# 4. Test admin creation
echo "Creating admin user..."
python -c "from server.admin_setup import create_admin_user; create_admin_user('admin@example.com', 'admin123')"
echo "✅ Admin user created"

echo ""
echo "🎉 Production readiness validated!"
```

**Deliverables:**
- [ ] Validation script created
- [ ] All tests pass
- [ ] Document production deployment steps
- [ ] Ready for production deployment

**Time Estimate:** 2 hours

---

## 📋 **COMPLETE TASK LIST FOR DEVELOPER A**

### **Day 1 (Oct 23) - Core Authentication**

**Morning (4 hours):**
- [ ] 1. Implement user signup endpoint (US #20)
  - Password hashing with bcrypt
  - User creation in database
  - JWT token generation
  - Test with curl

**Afternoon (4 hours):**
- [ ] 2. Implement user login endpoint (US #21)
  - Password verification
  - Last login timestamp
  - RBAC roles retrieval
  - JWT with roles
  - Test with curl

**EOD Checklist:**
- [ ] Signup working end-to-end
- [ ] Login working end-to-end
- [ ] Tokens being generated correctly
- [ ] Update Taiga US #20, #21 to "Done"

---

### **Day 2 (Oct 24) - Auth Middleware & Production**

**Morning (3 hours):**
- [ ] 3. Complete JWT authentication middleware (US #45)
  - Verify token middleware
  - Protect all endpoints
  - Test token expiration
  - Update Taiga US #45 to "Done"

**Midday (2 hours):**
- [ ] 4. Admin account setup
  - Create management command
  - Assign admin role
  - Test admin login
  - Document process

**Afternoon (3 hours):**
- [ ] 5. Health checks
  - Comprehensive /health endpoint
  - Database, Redis, Auth checks

- [ ] 6. Production validation
  - Create validation script
  - Run all tests
  - Document deployment

**EOD Checklist:**
- [ ] All auth features working
- [ ] Admin can log in
- [ ] Production validation passes
- [ ] Documentation complete

---

## 🎯 **SUCCESS CRITERIA**

### **Technical:**
- [ ] Users can sign up successfully
- [ ] Users can log in successfully
- [ ] JWT tokens work for authentication
- [ ] Protected endpoints require valid tokens
- [ ] Admin users can be created
- [ ] Admin can access admin features
- [ ] Health checks pass

### **Production Readiness:**
- [ ] Authentication system 100% functional
- [ ] No blockers for user signup
- [ ] No blockers for admin access
- [ ] Validation script confirms all features
- [ ] Documentation complete

### **Taiga Status:**
- [ ] US #20: Done (Signup)
- [ ] US #21: Done (Login)
- [ ] US #45: Done (JWT middleware)

---

## 📊 **CURRENT STATE VS TARGET STATE**

### **Current State (Oct 22):**
```
Production Ready: ❌ NO
Users Can Sign Up: ❌ NO
Users Can Log In: ❌ NO
Admin Can Administer: ❌ NO
SPEC-006 Status: Documented (not implemented)
Critical US Status: 3 of 3 NOT done
Production Blocker: YES
```

### **Target State (Oct 24 EOD):**
```
Production Ready: ✅ YES (Auth Complete)
Users Can Sign Up: ✅ YES
Users Can Log In: ✅ YES
Admin Can Administer: ✅ YES
SPEC-006 Status: 100% implemented
Critical US Status: 3 of 3 DONE
Production Blocker: NO
```

---

## 🔄 **COORDINATION WITH DEVELOPER C**

### **Developer C Work (Parallel):**
- Oct 23: Writing SPEC-099/100 documentation (8 files)
- Oct 24: Completing documentation (7 files), review, closure

### **Developer A Work (Parallel):**
- Oct 23: Core authentication (signup, login)
- Oct 24: Auth middleware, admin setup, production validation

### **Sync Points:**
- **Oct 23 EOD:** Both check progress, identify blockers
- **Oct 24 EOD:**
  - Developer C: SPEC-099/100 closure
  - Developer A: Production auth system complete
  - **COMBINED:** Platform production-ready

---

## ⚠️ **RISK MITIGATION**

### **Risk 1: Database Schema Missing**
- **Probability:** Medium
- **Impact:** High
- **Mitigation:** Check `User` table exists, has `password_hash` column
- **Action:** Run Alembic migrations if needed

### **Risk 2: JWT Secret Not Configured**
- **Probability:** Medium
- **Impact:** High
- **Mitigation:** Check `.env` has `JWT_SECRET`
- **Action:** Generate secret if missing: `openssl rand -hex 32`

### **Risk 3: Dependencies Missing**
- **Probability:** Low
- **Impact:** Medium
- **Mitigation:** Check `requirements.txt` has `passlib`, `bcrypt`, `PyJWT`
- **Action:** Add dependencies if missing

### **Risk 4: RBAC System Not Ready**
- **Probability:** Low
- **Impact:** Medium
- **Mitigation:** Basic roles (admin, user) sufficient for MVP
- **Action:** Create minimal RBAC if full system not ready

---

## 📞 **COMMUNICATION**

### **Daily Standup (9:00 AM):**
```
Developer A Update:
- Yesterday: [Progress on auth tasks]
- Today: [Planned auth tasks]
- Blockers: [Any blockers]
- On track for Oct 24: [Yes/No]
```

### **EOD Update (5:00 PM):**
```
Developer A Status:
- Completed: [List completed tasks]
- In progress: [Current task]
- Tomorrow: [Next day's plan]
- Needs help: [Any assistance needed]
```

---

## 🎉 **IMPACT**

### **Once Complete:**
- ✅ Users can sign up and use the platform
- ✅ Admins can log in and administer
- ✅ SPEC-006 (User Management, Authentication & Signup) 100% complete
- ✅ Production deployment unblocked
- ✅ Foundation ready for SPEC-099 Phase 2 (Rust migration)

### **Business Value:**
- **Immediate:** Platform becomes usable
- **Short-term:** Can onboard real users
- **Medium-term:** Admin features operational
- **Long-term:** Foundation for all other features

---

## 📚 **REFERENCES**

**SPEC Documents:**
- `specs/006-user-signup-system/spec.md` (SPEC-006 - User Management & Auth)
- `specs/003-core-api-architecture/README.md`

**Taiga User Stories:**
- US #20: User signup with bcrypt
- US #21: User login with password verification
- US #45: JWT authentication integrated

**Related Files:**
- `server/auth_api.py` or `server/signup_api.py`
- `server/auth_middleware.py`
- `server/models.py` (User model)
- `server/database.py`

---

**Document Created:** October 22, 2025, 3:35 PM
**Priority:** P0 - CRITICAL
**Timeline:** 2 days (Oct 23-24)
**Status:** Ready for Developer A execution
**Blocks:** Production deployment, user onboarding, admin features

---

**This is the REAL production-critical work!** 🚨
