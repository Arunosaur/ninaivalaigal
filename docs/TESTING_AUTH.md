# Practical Guide: Testing Authentication

This guide provides practical examples and strategies for testing the authentication system in ninaivalaigal.

## 1. Setting Up Test Environment

Before running auth tests, ensure your environment is set up correctly.

**Key components:**
- **Test Database:** A dedicated database for testing to avoid data corruption.
- **Pytest Fixtures:** Reusable setup and teardown logic for tests (`conftest.py`).
- **TestClient:** A way to make requests to your FastAPI application in tests.

```python
# conftest.py
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from myapp.main import app
from myapp.database import Base, get_db

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c
```

## 2. Testing Signup Flow

**Goal:** Ensure users can create accounts successfully and that validation works.

```python
# tests/test_signup.py
def test_signup_success(client):
    response = client.post("/auth/signup/individual", json={
        "email": "test@example.com",
        "password": "password123",
        "name": "Test User"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "jwt_token" in data["user"]

def test_signup_duplicate_email(client, test_user):
    response = client.post("/auth/signup/individual", json={
        "email": test_user.email,  # Existing user
        "password": "password123",
        "name": "Another User"
    })
    assert response.status_code == 400
    assert "Email already registered" in response.json()["detail"]
```

## 3. Testing Login Flow

**Goal:** Verify that registered users can log in and that invalid credentials are rejected.

```python
# tests/test_login.py
def test_login_success(client, test_user):
    response = client.post("/auth/login", json={
        "email": test_user.email,
        "password": "password123"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "jwt_token" in data["user"]

def test_login_invalid_password(client, test_user):
    response = client.post("/auth/login", json={
        "email": test_user.email,
        "password": "wrongpassword"
    })
    assert response.status_code == 401
    assert "Incorrect password" in response.json()["detail"]
```

## 4. Testing JWT Tokens

**Goal:** Ensure JWT tokens are generated correctly, contain the right payload, and are validated.

```python
import jwt

def test_jwt_payload(client, test_user):
    response = client.post("/auth/login", json={
        "email": test_user.email,
        "password": "password123"
    })
    token = response.json()["user"]["jwt_token"]

    payload = jwt.decode(token, options={"verify_signature": False})  # Don't verify signature in test

    assert payload["sub"] == test_user.email
    assert "exp" in payload
    assert "iat" in payload
```

## 5. Testing Refresh Tokens

**Goal:** Verify that refresh tokens can be used to get new access tokens and can be revoked.

```python
# tests/test_refresh_token.py
def test_refresh_token_success(client, authenticated_user):
    refresh_token = authenticated_user["refresh_token"]

    response = client.post("/auth/token/refresh", json={"refresh_token": refresh_token})

    assert response.status_code == 200
    assert "access_token" in response.json()

def test_revoke_refresh_token(client, authenticated_user):
    access_token = authenticated_user["jwt_token"]
    refresh_token = authenticated_user["refresh_token"]
    headers = {"Authorization": f"Bearer {access_token}"}

    # Revoke token
    client.post("/auth/token/revoke", headers=headers, json={"refresh_token": refresh_token})

    # Try to use revoked token
    response = client.post("/auth/token/refresh", json={"refresh_token": refresh_token})
    assert response.status_code == 401
```

## 6. Testing Password Reset

**Goal:** Ensure the password reset flow (request, token generation, reset) works correctly.

```python
# tests/test_password_reset.py
def test_password_reset_flow(client, test_user):
    # 1. Request password reset
    response = client.post("/auth/password-reset-request", json={"email": test_user.email})
    assert response.status_code == 200
    # (In a real app, this would email a token)

    # 2. Get token from test setup (e.g., mock email service)
    reset_token = "... get token from mock service ..."

    # 3. Reset password
    response = client.post("/auth/password-reset", json={
        "token": reset_token,
        "new_password": "newpassword123"
    })
    assert response.status_code == 200

    # 4. Try to log in with new password
    login_response = client.post("/auth/login", json={
        "email": test_user.email,
        "password": "newpassword123"
    })
    assert login_response.status_code == 200
```

## 7. Testing Email Verification

**Goal:** Verify that new users must verify their email to access certain resources.

```python
# tests/test_email_verification.py
def test_email_verification_flow(client):
    # 1. Create unverified user
    # ...

    # 2. Try to access protected route
    # ... should fail with 403 Forbidden

    # 3. Get verification token and verify
    # ...

    # 4. Try to access protected route again
    # ... should succeed
```

## 8. Testing Logout

**Goal:** Ensure that logging out invalidates tokens.

```python
# tests/test_logout.py
def test_logout(client, authenticated_user):
    access_token = authenticated_user["jwt_token"]
    refresh_token = authenticated_user["refresh_token"]
    headers = {"Authorization": f"Bearer {access_token}"}

    # Logout (revoke refresh token)
    response = client.post("/auth/token/revoke", headers=headers, json={"refresh_token": refresh_token})
    assert response.status_code == 200

    # Verify refresh token is invalid
    refresh_response = client.post("/auth/token/refresh", json={"refresh_token": refresh_token})
    assert refresh_response.status_code == 401
```

## 9. Testing RBAC (Role-Based Access Control)

**Goal:** Ensure that users with different roles have the correct permissions.

```python
# tests/test_rbac.py
def test_admin_can_access_admin_route(client, admin_user):
    # ... login as admin_user ...
    headers = {"Authorization": f"Bearer {admin_token}"}

    response = client.get("/admin/dashboard", headers=headers)
    assert response.status_code == 200

def test_regular_user_cannot_access_admin_route(client, regular_user):
    # ... login as regular_user ...
    headers = {"Authorization": f"Bearer {user_token}"}

    response = client.get("/admin/dashboard", headers=headers)
    assert response.status_code == 403
```

## 10. Common Pitfalls and Solutions

- **Shared State:** Ensure tests are isolated and don't rely on each other.
- **Hardcoded Values:** Use fixtures to create test data dynamically.
- **Slow Tests:** Mock external services to speed up tests.
- **Flaky Tests:** Avoid relying on timing; use explicit waits or polling if necessary.
