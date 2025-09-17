"""
Injectable Subject Context Provider

Provides explicit dependency injection for subject context resolution
with FastAPI integration and customizable JWT/claims processing.
"""

from typing import Callable, Optional, Dict, Any, Awaitable
from fastapi import FastAPI, Depends, Request, HTTPException
from .context import SubjectContext, resolve_jwt_claims


# Type alias for subject context provider function
SubjectContextProvider = Callable[[Request], Awaitable[Optional[SubjectContext]]]


class SubjectContextRegistry:
    """Registry for subject context providers per FastAPI app."""
    
    def __init__(self):
        self._providers: Dict[id, SubjectContextProvider] = {}
    
    def register(self, app: FastAPI, provider: SubjectContextProvider):
        """Register a subject context provider for an app."""
        self._providers[id(app)] = provider
    
    def get(self, app: FastAPI) -> Optional[SubjectContextProvider]:
        """Get the registered provider for an app."""
        return self._providers.get(id(app))
    
    def unregister(self, app: FastAPI):
        """Unregister provider for an app."""
        self._providers.pop(id(app), None)


# Global registry instance
_subject_context_registry = SubjectContextRegistry()


def install_subject_ctx_provider(app: FastAPI, provider: SubjectContextProvider):
    """
    Install a subject context provider for the FastAPI app.
    
    Args:
        app: FastAPI application instance
        provider: Async function that takes Request and returns Optional[SubjectContext]
    """
    _subject_context_registry.register(app, provider)
    
    # Store reference in app state for cleanup
    if not hasattr(app.state, 'subject_ctx_provider_installed'):
        app.state.subject_ctx_provider_installed = True
        
        # Add cleanup on app shutdown
        @app.on_event("shutdown")
        async def cleanup_subject_ctx_provider():
            _subject_context_registry.unregister(app)


def get_subject_ctx_dep(app: FastAPI):
    """
    Get FastAPI dependency function for subject context resolution.
    
    Returns a dependency function that can be used with Depends() in routes.
    
    Usage:
        subject_ctx_dep = get_subject_ctx_dep(app)
        
        @app.get("/protected")
        async def protected_route(ctx: SubjectContext = Depends(subject_ctx_dep)):
            return {"user_id": ctx.user_id}
    """
    
    async def subject_context_dependency(request: Request) -> Optional[SubjectContext]:
        """FastAPI dependency for subject context resolution."""
        
        provider = _subject_context_registry.get(app)
        
        if provider is None:
            # Fallback to default JWT resolution if no provider registered
            return await default_jwt_subject_provider(request)
        
        try:
            return await provider(request)
        except Exception as e:
            # Log error but don't fail request - return None for anonymous access
            import logging
            logging.warning(f"Subject context provider failed: {e}")
            return None
    
    return subject_context_dependency


async def default_jwt_subject_provider(request: Request) -> Optional[SubjectContext]:
    """
    Default subject context provider using JWT resolution.
    
    Extracts JWT from Authorization header and resolves claims to SubjectContext.
    """
    
    # Extract Authorization header
    auth_header = request.headers.get("Authorization", "")
    
    if not auth_header.startswith("Bearer "):
        return None
    
    token = auth_header[7:]  # Remove "Bearer " prefix
    
    try:
        # Use existing JWT claims resolution
        claims = resolve_jwt_claims(token)
        
        if not claims:
            return None
        
        # Extract subject context from claims
        return SubjectContext(
            user_id=claims.get("sub"),
            organization_id=claims.get("org_id"),
            team_id=claims.get("team_id"),
            roles=claims.get("roles", []),
            permissions=claims.get("permissions", []),
            raw_claims=claims
        )
        
    except Exception:
        # JWT verification failed - return None for anonymous access
        return None


def create_verified_jwt_provider(
    jwks_client,
    audience: str,
    issuer: str,
    require_verification: bool = True
) -> SubjectContextProvider:
    """
    Create a verified JWT subject context provider.
    
    Args:
        jwks_client: JWKS client for key verification
        audience: Expected JWT audience
        issuer: Expected JWT issuer
        require_verification: If True, reject unverified tokens
    
    Returns:
        SubjectContextProvider function
    """
    
    async def verified_jwt_provider(request: Request) -> Optional[SubjectContext]:
        """Subject context provider with full JWT verification."""
        
        # Extract Authorization header
        auth_header = request.headers.get("Authorization", "")
        
        if not auth_header.startswith("Bearer "):
            return None
        
        token = auth_header[7:]
        
        try:
            import jwt
            from jwt.exceptions import InvalidTokenError
            
            # Get signing key from JWKS
            unverified_header = jwt.get_unverified_header(token)
            kid = unverified_header.get("kid")
            
            if not kid:
                if require_verification:
                    return None
                # Fallback to unverified parsing
                claims = jwt.decode(token, options={"verify_signature": False})
            else:
                # Verify with JWKS
                signing_key = jwks_client.get_signing_key(kid)
                claims = jwt.decode(
                    token,
                    signing_key.key,
                    algorithms=["RS256", "ES256"],
                    audience=audience,
                    issuer=issuer
                )
            
            # Create subject context
            return SubjectContext(
                user_id=claims.get("sub"),
                organization_id=claims.get("org_id"),
                team_id=claims.get("team_id"),
                roles=claims.get("roles", []),
                permissions=claims.get("permissions", []),
                raw_claims=claims
            )
            
        except InvalidTokenError:
            if require_verification:
                return None
            # Try unverified fallback
            try:
                claims = jwt.decode(token, options={"verify_signature": False})
                return SubjectContext(
                    user_id=claims.get("sub"),
                    organization_id=claims.get("org_id"),
                    team_id=claims.get("team_id"),
                    roles=claims.get("roles", []),
                    permissions=claims.get("permissions", []),
                    raw_claims=claims
                )
            except Exception:
                return None
        
        except Exception:
            return None
    
    return verified_jwt_provider


def create_mock_subject_provider(
    default_user_id: str = "test_user",
    default_org_id: str = "test_org",
    default_roles: list = None
) -> SubjectContextProvider:
    """
    Create a mock subject context provider for testing.
    
    Args:
        default_user_id: Default user ID for mock context
        default_org_id: Default organization ID
        default_roles: Default roles list
    
    Returns:
        SubjectContextProvider function for testing
    """
    
    if default_roles is None:
        default_roles = ["user"]
    
    async def mock_provider(request: Request) -> Optional[SubjectContext]:
        """Mock subject context provider for testing."""
        
        # Check for test headers to override defaults
        user_id = request.headers.get("X-Test-User-Id", default_user_id)
        org_id = request.headers.get("X-Test-Org-Id", default_org_id)
        roles = request.headers.get("X-Test-Roles", ",".join(default_roles)).split(",")
        
        from .context import Role
        
        # Map first role to Role enum
        role = None
        if roles:
            try:
                role = Role(roles[0].lower())
            except ValueError:
                role = Role.USER
        
        ctx = SubjectContext(
            user_id=user_id,
            organization_id=org_id,
            team_id=request.headers.get("X-Test-Team-Id"),
            role=role,
            permissions=roles  # Store roles as permissions for compatibility
        )
        
        # Add raw_claims as attribute
        ctx.raw_claims = {
            "sub": user_id,
            "org_id": org_id,
            "roles": roles,
            "mock": True
        }
        
        return ctx
    
    return mock_provider


def test_subject_context_provider():
    """Test subject context provider functionality."""
    
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    
    # Create test app
    app = FastAPI()
    
    # Create mock provider
    mock_provider = create_mock_subject_provider(
        default_user_id="test_123",
        default_org_id="org_456",
        default_roles=["admin", "user"]
    )
    
    # Install provider
    install_subject_ctx_provider(app, mock_provider)
    
    # Get dependency
    subject_ctx_dep = get_subject_ctx_dep(app)
    
    # Create test route
    @app.get("/test")
    async def test_route(ctx: Optional[SubjectContext] = Depends(subject_ctx_dep)):
        if ctx is None:
            return {"authenticated": False}
        
        return {
            "authenticated": True,
            "user_id": ctx.user_id,
            "org_id": ctx.organization_id,
            "roles": ctx.roles
        }
    
    # Test with client
    client = TestClient(app)
    
    # Test default context
    response = client.get("/test")
    assert response.status_code == 200
    data = response.json()
    assert data["authenticated"] == True
    assert data["user_id"] == "test_123"
    assert data["org_id"] == "org_456"
    assert "admin" in data["roles"]
    
    # Test with custom headers
    response = client.get("/test", headers={
        "X-Test-User-Id": "custom_user",
        "X-Test-Org-Id": "custom_org",
        "X-Test-Roles": "viewer"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == "custom_user"
    assert data["org_id"] == "custom_org"
    assert data["roles"] == ["viewer"]
    
    return {
        "test_passed": True,
        "provider_installed": True,
        "dependency_working": True
    }


if __name__ == "__main__":
    # Run test
    results = test_subject_context_provider()
    print("Subject Context Provider Test Results:")
    print(f"✅ Test passed: {results['test_passed']}")
    print(f"✅ Provider installed: {results['provider_installed']}")
    print(f"✅ Dependency working: {results['dependency_working']}")
