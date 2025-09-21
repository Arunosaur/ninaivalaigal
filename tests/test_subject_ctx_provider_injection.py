"""
Subject Context Provider Injection Test

Proves that dependency injection works correctly for subject context providers
with FastAPI routes and RBAC integration.
"""

from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from server.security.rbac.context import SubjectContext
from server.security.rbac.context_provider import (
    create_mock_subject_provider,
    get_subject_ctx_dep,
    install_subject_ctx_provider,
)


def test_mock_provider_injection():
    """Test mock subject context provider injection."""

    app = FastAPI()

    # Create mock provider
    mock_provider = create_mock_subject_provider(
        default_user_id="test_user_123",
        default_org_id="test_org_456",
        default_roles=["admin", "user"],
    )

    # Install provider
    install_subject_ctx_provider(app, mock_provider)

    # Get dependency
    subject_ctx_dep = get_subject_ctx_dep(app)

    # Create test route
    @app.get("/whoami")
    async def whoami(ctx: SubjectContext = Depends(subject_ctx_dep)):
        if ctx is None:
            return {"authenticated": False}

        return {
            "authenticated": True,
            "user_id": ctx.user_id,
            "org_id": ctx.organization_id,
            "role": ctx.role.value if ctx.role else None,
            "permissions": ctx.permissions or [],
            "mock": getattr(ctx, "raw_claims", {}).get("mock", False),
        }

    # Test with client
    client = TestClient(app)

    # Test default context
    response = client.get("/whoami")
    assert response.status_code == 200
    data = response.json()
    assert data["authenticated"] == True
    assert data["user_id"] == "test_user_123"
    assert data["org_id"] == "test_org_456"
    assert data["role"] is not None
    assert data["mock"] == True

    return True


def test_custom_header_provider():
    """Test custom header-based provider injection."""

    app = FastAPI()

    # Create custom provider that reads headers
    async def header_provider(request) -> SubjectContext:
        from server.security.rbac.context import Role

        user_id = request.headers.get("X-User-Id", "anonymous")
        org_id = request.headers.get("X-Org-Id", "default")
        role_str = request.headers.get("X-Role", "user")

        # Map string to Role enum
        role = None
        try:
            role = Role(role_str.lower())
        except ValueError:
            role = Role.USER

        ctx = SubjectContext(user_id=user_id, organization_id=org_id, role=role)
        # Add raw_claims as attribute
        ctx.raw_claims = {"source": "headers"}
        return ctx

    # Install custom provider
    install_subject_ctx_provider(app, header_provider)

    # Get dependency
    subject_ctx_dep = get_subject_ctx_dep(app)

    # Create test route
    @app.get("/protected")
    async def protected_route(ctx: SubjectContext = Depends(subject_ctx_dep)):
        return {
            "user_id": ctx.user_id,
            "org_id": ctx.organization_id,
            "role": ctx.role.value if ctx.role else None,
            "source": getattr(ctx, "raw_claims", {}).get("source"),
        }

    # Test with client
    client = TestClient(app)

    # Test with custom headers
    response = client.get(
        "/protected",
        headers={
            "X-User-Id": "custom_user",
            "X-Org-Id": "custom_org",
            "X-Role": "admin",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == "custom_user"
    assert data["org_id"] == "custom_org"
    assert data["role"] == "admin"
    assert data["source"] == "headers"

    return True


def test_fallback_provider_behavior():
    """Test fallback behavior when no provider is registered."""

    app = FastAPI()

    # Don't install any provider - should use default JWT fallback
    subject_ctx_dep = get_subject_ctx_dep(app)

    @app.get("/fallback")
    async def fallback_route(ctx: SubjectContext = Depends(subject_ctx_dep)):
        if ctx is None:
            return {"fallback": True, "authenticated": False}

        return {"fallback": False, "authenticated": True, "user_id": ctx.user_id}

    # Test with client (no auth header)
    client = TestClient(app)
    response = client.get("/fallback")

    assert response.status_code == 200
    data = response.json()
    assert data["fallback"] == True
    assert data["authenticated"] == False

    return True


def test_provider_error_handling():
    """Test error handling in subject context providers."""

    app = FastAPI()

    # Create provider that raises exception
    async def failing_provider(request) -> SubjectContext:
        raise Exception("Provider failed")

    # Install failing provider
    install_subject_ctx_provider(app, failing_provider)

    # Get dependency
    subject_ctx_dep = get_subject_ctx_dep(app)

    @app.get("/error-test")
    async def error_test_route(ctx: SubjectContext = Depends(subject_ctx_dep)):
        if ctx is None:
            return {"error_handled": True, "ctx_is_none": True}

        return {"error_handled": False, "ctx_is_none": False}

    # Test with client
    client = TestClient(app)
    response = client.get("/error-test")

    assert response.status_code == 200
    data = response.json()
    assert data["error_handled"] == True
    assert data["ctx_is_none"] == True

    return True


def test_multiple_apps_isolation():
    """Test that different apps can have different providers."""

    # Create two apps with different providers
    app1 = FastAPI()
    app2 = FastAPI()

    # Provider 1: Returns user "app1_user"
    async def provider1(request) -> SubjectContext:
        from server.security.rbac.context import Role

        ctx = SubjectContext(
            user_id="app1_user", organization_id="org1", role=Role.USER
        )
        ctx.raw_claims = {"app": "app1"}
        return ctx

    # Provider 2: Returns user "app2_user"
    async def provider2(request) -> SubjectContext:
        from server.security.rbac.context import Role

        ctx = SubjectContext(
            user_id="app2_user", organization_id="org2", role=Role.ADMIN
        )
        ctx.raw_claims = {"app": "app2"}
        return ctx

    # Install different providers
    install_subject_ctx_provider(app1, provider1)
    install_subject_ctx_provider(app2, provider2)

    # Create routes
    @app1.get("/app1")
    async def app1_route(ctx: SubjectContext = Depends(get_subject_ctx_dep(app1))):
        return {
            "user_id": ctx.user_id,
            "app": getattr(ctx, "raw_claims", {}).get("app"),
        }

    @app2.get("/app2")
    async def app2_route(ctx: SubjectContext = Depends(get_subject_ctx_dep(app2))):
        return {
            "user_id": ctx.user_id,
            "app": getattr(ctx, "raw_claims", {}).get("app"),
        }

    # Test both apps
    client1 = TestClient(app1)
    client2 = TestClient(app2)

    response1 = client1.get("/app1")
    response2 = client2.get("/app2")

    assert response1.status_code == 200
    assert response2.status_code == 200

    data1 = response1.json()
    data2 = response2.json()

    assert data1["user_id"] == "app1_user"
    assert data1["app"] == "app1"
    assert data2["user_id"] == "app2_user"
    assert data2["app"] == "app2"

    return True


def run_all_tests():
    """Run all subject context provider injection tests."""

    tests = [
        ("Mock Provider Injection", test_mock_provider_injection),
        ("Custom Header Provider", test_custom_header_provider),
        ("Fallback Provider Behavior", test_fallback_provider_behavior),
        ("Provider Error Handling", test_provider_error_handling),
        ("Multiple Apps Isolation", test_multiple_apps_isolation),
    ]

    results = []

    for test_name, test_func in tests:
        try:
            passed = test_func()
            results.append((test_name, passed, None))
        except Exception as e:
            results.append((test_name, False, str(e)))

    return results


if __name__ == "__main__":
    # Run all tests
    test_results = run_all_tests()

    print("Subject Context Provider Injection Test Results:")
    print("=" * 60)

    passed_count = 0
    total_count = len(test_results)

    for test_name, passed, error in test_results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{status} {test_name}")

        if error:
            print(f"   Error: {error}")

        if passed:
            passed_count += 1

    print("=" * 60)
    print(f"Overall: {passed_count}/{total_count} tests passed")

    if passed_count == total_count:
        print("🎉 All dependency injection tests passed!")
    else:
        print("⚠️  Some tests failed - check implementation")
