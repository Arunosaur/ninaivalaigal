# Developer B - Testing & Documentation (Week 1-2)

**Date**: October 16-25, 2025
**Mission**: Test all services and document APIs
**Why You**: gRPC validation expert, testing mindset
**Time**: 6-8 hours/day for 2 weeks

---

## 🎯 Your Mission

**Test and document all 5 services:**
1. **Core API** (Python) - Day 1-2
2. **Business Service** (Python) - Day 3
3. **Admin/Vendor Service** (Python) - Day 4
4. **Memory Service** (Rust) - Week 1-2
5. **Graph/AI Service** (Rust) - Week 2

**Goal**: 100% API contract coverage, comprehensive test suite

---

## 📅 Day 1 (Oct 16) - Core API Testing

### Morning (3 hours): Contract Validation

**Already exists**: ✅ `shared/contracts/core-api/v1/openapi.yaml`

1. **Review OpenAPI contract**:
```bash
cat shared/contracts/core-api/v1/openapi.yaml

# Key endpoints to verify:
# - POST /auth/signup
# - POST /auth/login
# - POST /auth/refresh
# - GET /users/me
# - POST /teams
# - GET /teams
```

2. **Compare contract to actual code**:
```bash
# As Developer C extracts code, verify:
cd services/core-api/routers
cat auth.py

# Check:
# - Do endpoints match OpenAPI spec?
# - Are request/response models correct?
# - Are status codes matching?
```

3. **Create contract validation script**:
```python
# tests/contract_validation.py
import yaml
import requests

def load_openapi_spec(service):
    with open(f'shared/contracts/{service}/v1/openapi.yaml') as f:
        return yaml.safe_load(f)

def test_core_api_contract():
    spec = load_openapi_spec('core-api')
    base_url = 'http://localhost:8000'

    # Test each endpoint exists
    for path, methods in spec['paths'].items():
        for method in methods:
            if method == 'get':
                resp = requests.get(f'{base_url}{path}')
                assert resp.status_code in [200, 401, 403, 404]
```

### Afternoon (4 hours): Integration Tests

4. **Create test suite** (`tests/integration/test_core_api.py`):
```python
import pytest
import requests

BASE_URL = "http://localhost:8000"

class TestAuthFlow:
    """Test complete authentication flow"""

    def test_signup_creates_user(self):
        """User can sign up with valid data"""
        response = requests.post(f"{BASE_URL}/auth/signup", json={
            "email": "newuser@test.com",
            "password": "SecurePass123!",  # pragma: allowlist secret
            "name": "New User"
        })

        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newuser@test.com"
        assert data["name"] == "New User"
        assert "id" in data

    def test_signup_rejects_duplicate_email(self):
        """Cannot sign up with existing email"""
        # First signup
        requests.post(f"{BASE_URL}/auth/signup", json={
            "email": "duplicate@test.com",
            "password": "Pass123!",  # pragma: allowlist secret
            "name": "First User"
        })

        # Duplicate signup
        response = requests.post(f"{BASE_URL}/auth/signup", json={
            "email": "duplicate@test.com",
            "password": "Pass123!",  # pragma: allowlist secret
            "name": "Second User"
        })

        assert response.status_code == 400
        assert "already exists" in response.json()["detail"].lower()

    def test_login_returns_token(self):
        """User can login with correct credentials"""
        # First signup
        requests.post(f"{BASE_URL}/auth/signup", json={
            "email": "login@test.com",
            "password": "LoginPass123!",  # pragma: allowlist secret
            "name": "Login User"
        })

        # Login
        response = requests.post(f"{BASE_URL}/auth/login", json={
            "email": "login@test.com",
            "password": "LoginPass123!"  # pragma: allowlist secret
        })

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    def test_login_rejects_wrong_password(self):
        """Login fails with incorrect password"""
        # First signup
        requests.post(f"{BASE_URL}/auth/signup", json={
            "email": "wrongpass@test.com",
            "password": "CorrectPass123!",  # pragma: allowlist secret
            "name": "User"
        })

        # Login with wrong password
        response = requests.post(f"{BASE_URL}/auth/login", json={
            "email": "wrongpass@test.com",
            "password": "WrongPass123!"  # pragma: allowlist secret
        })

        assert response.status_code == 401
        assert "invalid" in response.json()["detail"].lower()


class TestUserManagement:
    """Test user management endpoints"""

    @pytest.fixture
    def auth_token(self):
        """Get auth token for authenticated requests"""
        # Signup
        requests.post(f"{BASE_URL}/auth/signup", json={
            "email": "authuser@test.com",
            "password": "AuthPass123!",  # pragma: allowlist secret
            "name": "Auth User"
        })

        # Login
        response = requests.post(f"{BASE_URL}/auth/login", json={
            "email": "authuser@test.com",
            "password": "AuthPass123!"  # pragma: allowlist secret
        })

        return response.json()["access_token"]

    def test_get_current_user(self, auth_token):
        """Get current user profile"""
        response = requests.get(
            f"{BASE_URL}/users/me",
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "authuser@test.com"
        assert data["name"] == "Auth User"

    def test_update_user_profile(self, auth_token):
        """Update user profile"""
        response = requests.patch(
            f"{BASE_URL}/users/me",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"name": "Updated Name"}
        )

        assert response.status_code == 200
        assert response.json()["name"] == "Updated Name"


class TestTeamManagement:
    """Test team management endpoints"""

    @pytest.fixture
    def auth_token(self):
        """Get auth token"""
        requests.post(f"{BASE_URL}/auth/signup", json={
            "email": "teamuser@test.com",
            "password": "TeamPass123!",  # pragma: allowlist secret
            "name": "Team User"
        })

        response = requests.post(f"{BASE_URL}/auth/login", json={
            "email": "teamuser@test.com",
            "password": "TeamPass123!"  # pragma: allowlist secret
        })

        return response.json()["access_token"]

    def test_create_team(self, auth_token):
        """Create a new team"""
        response = requests.post(
            f"{BASE_URL}/teams",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"name": "My Team"}
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "My Team"
        assert "id" in data

    def test_list_teams(self, auth_token):
        """List user's teams"""
        # Create team
        requests.post(
            f"{BASE_URL}/teams",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"name": "Team 1"}
        )

        # List teams
        response = requests.get(
            f"{BASE_URL}/teams",
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        assert response.status_code == 200
        teams = response.json()
        assert len(teams) >= 1
        assert any(t["name"] == "Team 1" for t in teams)
```

5. **Run tests**:
```bash
pytest tests/integration/test_core_api.py -v
```

**End of Day 1 Deliverable**: Core API test suite

---

## 📅 Day 2 (Oct 17) - Core API Documentation

### Morning (3 hours): API Documentation

1. **Create service README** (`services/core-api/README.md`):
```markdown
# Core API Service

Authentication and user management service.

## Endpoints

### Authentication

**POST /auth/signup**
Create a new user account.

Request:
\`\`\`json
{
  "email": "user@example.com",
  "password": "SecurePass123!",  # pragma: allowlist secret falsepositive
  "name": "User Name"
}
\`\`\`

Response (201):
\`\`\`json
{
  "id": "uuid",
  "email": "user@example.com",
  "name": "User Name",
  "created_at": "2025-10-16T10:00:00Z"
}
\`\`\`

**POST /auth/login**
Login with credentials.

Request:
\`\`\`json
{
  "email": "user@example.com",
  "password": "SecurePass123!"  # pragma: allowlist secret falsepositive
}
\`\`\`

Response (200):
\`\`\`json
{
  "access_token": "jwt_token",
  "refresh_token": "refresh_token",
  "token_type": "bearer"
}
\`\`\`

### Users

**GET /users/me**
Get current user profile. Requires authentication.

Headers:
\`\`\`
Authorization: Bearer <token>
\`\`\`

Response (200):
\`\`\`json
{
  "id": "uuid",
  "email": "user@example.com",
  "name": "User Name",
  "created_at": "2025-10-16T10:00:00Z"
}
\`\`\`

## Running Locally

\`\`\`bash
cd services/core-api
pip install -r requirements.txt
python main.py
\`\`\`

## Running Tests

\`\`\`bash
pytest tests/integration/test_core_api.py
\`\`\`

## Environment Variables

- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `JWT_SECRET`: Secret for JWT token signing
```

### Afternoon (4 hours): Usage Examples

2. **Create example scripts** (`examples/core-api/`):
```python
# examples/core-api/signup_and_login.py
"""
Example: Sign up a new user and login
"""
import requests

BASE_URL = "http://localhost:8000"

# Sign up
print("Creating new user...")
signup_response = requests.post(f"{BASE_URL}/auth/signup", json={
    "email": "demo@example.com",
    "password": "DemoPass123!",  # pragma: allowlist secret
    "name": "Demo User"
})

if signup_response.status_code == 201:
    print("✅ User created successfully")
    print(signup_response.json())
else:
    print("❌ Signup failed:", signup_response.json())
    exit(1)

# Login
print("\nLogging in...")
login_response = requests.post(f"{BASE_URL}/auth/login", json={
    "email": "demo@example.com",
    "password": "DemoPass123!"  # pragma: allowlist secret
})

if login_response.status_code == 200:
    print("✅ Login successful")
    token = login_response.json()["access_token"]
    print(f"Token: {token[:20]}...")
else:
    print("❌ Login failed:", login_response.json())
    exit(1)

# Get profile
print("\nGetting profile...")
profile_response = requests.get(
    f"{BASE_URL}/users/me",
    headers={"Authorization": f"Bearer {token}"}
)

if profile_response.status_code == 200:
    print("✅ Profile retrieved")
    print(profile_response.json())
else:
    print("❌ Failed to get profile:", profile_response.json())
```

3. **Create Postman collection**:
```json
{
  "info": {
    "name": "Core API Service",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "item": [
    {
      "name": "Auth",
      "item": [
        {
          "name": "Signup",
          "request": {
            "method": "POST",
            "header": [],
            "body": {
              "mode": "raw",
              "raw": "{\n  \"email\": \"test@example.com\",\n  \"password\": \"TestPass123!\",\n  \"name\": \"Test User\"\n}"  # pragma: allowlist secret
            },
            "url": "http://localhost:8000/auth/signup"
          }
        },
        {
          "name": "Login",
          "request": {
            "method": "POST",
            "header": [],
            "body": {
              "mode": "raw",
              "raw": "{\n  \"email\": \"test@example.com\",\n  \"password\": \"TestPass123!\"\n}"  # pragma: allowlist secret
            },
            "url": "http://localhost:8000/auth/login"
          }
        }
      ]
    }
  ]
}
```

**End of Day 2 Deliverable**: Core API fully documented

---

## 📅 Day 3 (Oct 19) - Business Service Testing

**Same process as Core API**:
1. Review OpenAPI contract for Business Service
2. Create integration tests
3. Write service README
4. Create example scripts

**Key endpoints to test**:
- POST /billing/subscriptions
- GET /billing/subscriptions
- POST /billing/payment-methods
- GET /invoices
- POST /invoices/{id}/download

**End of Day 3 Deliverable**: Business Service tested & documented

---

## 📅 Day 4 (Oct 20) - Admin/Vendor Service Testing

**Same process**:
1. Contract validation
2. Integration tests
3. Documentation
4. Examples

**Key endpoints to test**:
- GET /admin/analytics
- GET /admin/dashboard/widgets
- POST /vendor/approval
- GET /vendor/discussions

**End of Day 4 Deliverable**: Admin/Vendor Service tested & documented

---

## 📅 Week 1 (Days 1-5) - Memory Service (Rust) Testing

### As Developer A develops Memory Service

**Your tasks**:

1. **Review Rust code**:
```bash
cd rust-services/memory-service/src
cat main.rs
cat memory.rs
cat storage.rs
```

2. **Test REST endpoints** (as they're built):
```bash
# Health check
curl http://localhost:8001/health

# Create memory
curl -X POST http://localhost:8001/memory/remember \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{"content": "Test memory"}'

# List memories
curl http://localhost:8001/memory/memories \
  -H "Authorization: Bearer <token>"
```

3. **Create integration tests** (`tests/integration/test_memory_service.py`):
```python
import pytest
import requests

BASE_URL = "http://localhost:8001"

class TestMemoryService:
    def test_health(self):
        response = requests.get(f"{BASE_URL}/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "memory-service"
        assert data["language"] == "rust"

    def test_create_memory(self, auth_token):
        response = requests.post(
            f"{BASE_URL}/memory/remember",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"content": "Important meeting notes"}
        )

        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["content"] == "Important meeting notes"

    def test_list_memories(self, auth_token):
        # Create a memory first
        requests.post(
            f"{BASE_URL}/memory/remember",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"content": "Memory 1"}
        )

        # List memories
        response = requests.get(
            f"{BASE_URL}/memory/memories",
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        assert response.status_code == 200
        memories = response.json()
        assert len(memories) >= 1
```

4. **Performance testing**:
```bash
# Install hey
brew install hey

# Test memory creation performance
hey -n 1000 -c 10 -m POST \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{"content":"Performance test"}' \
  http://localhost:8001/memory/remember

# Expected: <30ms P95 latency (Rust target)
```

5. **Compare Python vs Rust**:
```python
# tests/performance/compare_memory_services.py
import time
import requests

def benchmark_service(base_url, name):
    """Benchmark memory service performance"""
    start = time.time()

    # Create 100 memories
    for i in range(100):
        requests.post(f"{base_url}/memory/remember", json={
            "content": f"Test memory {i}"
        })

    duration = time.time() - start
    print(f"{name}: {duration:.2f}s for 100 memories")
    return duration

# Benchmark both
python_time = benchmark_service("http://localhost:8001", "Python (baseline)")
rust_time = benchmark_service("http://localhost:8001", "Rust")

# Calculate improvement
improvement = ((python_time - rust_time) / python_time) * 100
print(f"\n✅ Rust is {improvement:.0f}% faster!")
```

**End of Week 1 (Memory Service)**: Performance benchmarks showing 50-90% improvement

---

## 📅 Week 2 - Graph/AI Service (Rust) Testing

### As Developer A develops Graph/AI Service

**Your tasks**:

1. **Test GraphOps integration**:
```python
# tests/integration/test_graph_ai_service.py
def test_graph_query():
    """Test graph query via GraphOps"""
    response = requests.post(
        "http://localhost:8002/graph/query",
        headers={"Authorization": f"Bearer {token}"},
        json={"query": "MATCH (u:User) RETURN u"}
    )

    assert response.status_code == 200
```

2. **Test AI endpoints**:
```python
def test_generate_insight():
    """Test AI insight generation"""
    response = requests.post(
        "http://localhost:8002/ai/insights",
        headers={"Authorization": f"Bearer {token}"},
        json={"context": "memory_123"}
    )

    assert response.status_code == 200
    data = response.json()
    assert "insight" in data
```

3. **End-to-end flow testing**:
```python
def test_full_memory_flow():
    """Test complete flow: Create memory → Graph AI → Insight"""
    # 1. Create memory (Memory Service)
    memory_resp = requests.post("http://localhost:8001/memory/remember", ...)
    memory_id = memory_resp.json()["id"]

    # 2. Generate insight (Graph/AI Service)
    insight_resp = requests.post(
        "http://localhost:8002/ai/insights",
        json={"memory_id": memory_id}
    )

    # 3. Verify insight
    assert insight_resp.status_code == 200
```

**End of Week 2 Deliverable**: All 5 services tested, documented, benchmarked

---

## ✅ Success Criteria

**By End of Week 1**:
- [ ] Core API: 100% endpoint coverage
- [ ] Business Service: All endpoints tested
- [ ] Admin/Vendor Service: All endpoints tested
- [ ] Memory Service (Rust): Performance benchmarks
- [ ] All services have README docs
- [ ] Example scripts for each service

**By End of Week 2**:
- [ ] Graph/AI Service: Full integration tests
- [ ] End-to-end flow tests passing
- [ ] Performance comparison report (Python vs Rust)
- [ ] Postman collections for all services
- [ ] Complete API documentation

---

## 📊 Deliverables

1. **Test Suites**:
   - `tests/integration/test_core_api.py`
   - `tests/integration/test_business_service.py`
   - `tests/integration/test_admin_vendor_service.py`
   - `tests/integration/test_memory_service.py`
   - `tests/integration/test_graph_ai_service.py`

2. **Documentation**:
   - `services/*/README.md` for each service
   - `examples/*/` with usage scripts
   - Postman collections

3. **Performance Reports**:
   - Python vs Rust benchmarks
   - Latency improvements
   - Throughput improvements

---

## 🆘 If You Get Stuck

### Tests Failing
1. Check if service is running: `curl http://localhost:PORT/health`
2. Check logs: `docker-compose logs <service>`
3. Verify test data setup

### Performance Not Meeting Targets
1. Work with Developer A to optimize
2. Profile with `py-spy` (Python) or `cargo flamegraph` (Rust)
3. Add more caching

---

**Focus**: Catch bugs early, document everything, prove the Rust migration ROI

**Philosophy**: Tests are documentation, documentation is tests

**Goal**: 100% confidence that the platform works!
