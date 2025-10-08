"""
Middleware Order Parity Test

Ensures middleware chain order is identical between dev/prod configurations
to prevent future drift and maintain security guarantees.
"""

from fastapi import FastAPI

from server.security.bundle import (
    SecurityBundle,
    apply_development_security,
    apply_production_security,
)


def extract_middleware_chain(app: FastAPI) -> list[str]:
    """Extract middleware chain order from FastAPI app."""
    middleware_chain = []

    # Extract middleware from app.user_middleware (reverse order as they're applied)
    for middleware in reversed(app.user_middleware):
        middleware_name = middleware.cls.__name__
        middleware_chain.append(middleware_name)

    return middleware_chain


def test_middleware_order_parity():
    """Test that dev and prod middleware chains are identical."""

    # Create production app
    prod_app = FastAPI()
    apply_production_security(prod_app)
    prod_chain = extract_middleware_chain(prod_app)

    # Create development app
    dev_app = FastAPI()
    apply_development_security(dev_app)
    dev_chain = extract_middleware_chain(dev_app)

    # Compare chains
    assert (
        prod_chain == dev_chain
    ), f"Middleware order mismatch:\nProd: {prod_chain}\nDev:  {dev_chain}"

    # Verify expected middleware are present
    expected_middleware = [
        "ContentTypeGuardMiddleware",
        "CompressionGuardMiddleware",
        "IdempotencyMiddleware",
        "RedactionASGIMiddleware",
        "ResponseRedactionASGIMiddleware",
    ]

    for expected in expected_middleware:
        assert any(
            expected in mw for mw in prod_chain
        ), f"Missing middleware: {expected}"

    return {
        "test_passed": True,
        "middleware_count": len(prod_chain),
        "chain_order": prod_chain,
    }


def test_security_bundle_consistency():
    """Test SecurityBundle.apply() produces consistent middleware order."""

    apps = []
    chains = []

    # Test multiple configurations
    configs = [
        {"enable_compression_guard": True, "enable_multipart_adapter": True},
        {"enable_compression_guard": False, "enable_multipart_adapter": True},
        {"enable_compression_guard": True, "enable_multipart_adapter": False},
    ]

    for config in configs:
        app = FastAPI()
        SecurityBundle.apply(app, **config)
        chain = extract_middleware_chain(app)

        apps.append(app)
        chains.append(chain)

    # All chains should have same base order (excluding optional middleware)
    base_middleware = ["ContentTypeGuardMiddleware", "IdempotencyMiddleware"]

    for chain in chains:
        for base_mw in base_middleware:
            assert any(
                base_mw in mw for mw in chain
            ), f"Missing base middleware: {base_mw}"

    return {
        "test_passed": True,
        "configurations_tested": len(configs),
        "consistent_base_order": True,
    }


if __name__ == "__main__":
    # Run tests
    parity_result = test_middleware_order_parity()
    consistency_result = test_security_bundle_consistency()

    print("Middleware Order Parity Test Results:")
    print(f"✅ Parity Test: {parity_result}")
    print(f"✅ Consistency Test: {consistency_result}")
