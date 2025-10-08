"""
Basic security functionality tests
"""

import os
import sys

# Add the server directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "server"))


def test_entropy_calculation():
    """Test basic entropy calculation"""
    try:
        from security.utils.entropy import calculate_entropy

        # Test high entropy string
        high_entropy = "sk-1234567890abcdef1234567890abcdef12345678"
        entropy = calculate_entropy(high_entropy)
        assert entropy > 4.0, f"Expected high entropy, got {entropy}"

        # Test low entropy string
        low_entropy = "hello world"
        entropy = calculate_entropy(low_entropy)
        assert entropy < 4.0, f"Expected low entropy, got {entropy}"

        print("✅ Entropy calculation working correctly")
        return True

    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Test error: {e}")
        return False


def test_secret_detection():
    """Test basic secret detection"""
    try:
        from security.redaction.detectors import ContextAwareDetector

        detector = ContextAwareDetector()

        # Test with a simple API key pattern
        text = "API key: sk-1234567890abcdef1234567890abcdef12345678"
        matches = detector.detect_secrets(text)

        assert len(matches) > 0, "Should detect at least one secret"
        print(f"✅ Secret detection working - found {len(matches)} secrets")
        return True

    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Test error: {e}")
        return False


def test_redaction_config():
    """Test redaction configuration"""
    try:
        from security.redaction.config import ContextSensitivity, redaction_config

        # Test config access
        assert redaction_config.enabled is not None
        assert redaction_config.default_tier is not None

        # Test sensitivity tiers
        tiers = list(ContextSensitivity)
        assert len(tiers) >= 5, "Should have at least 5 sensitivity tiers"

        print("✅ Redaction configuration working correctly")
        return True

    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Test error: {e}")
        return False


def test_security_middleware_imports():
    """Test security middleware imports"""
    try:
        from security.middleware.rate_limiting import EnhancedRateLimiter
        from security.middleware.redaction_middleware import RedactionMiddleware
        from security.middleware.security_headers import SecurityHeadersMiddleware

        # Test instantiation
        headers_middleware = SecurityHeadersMiddleware
        redaction_middleware = RedactionMiddleware
        rate_limiter = EnhancedRateLimiter()

        print("✅ Security middleware imports working correctly")
        return True

    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Test error: {e}")
        return False


def run_all_tests():
    """Run all basic tests"""
    tests = [
        test_entropy_calculation,
        test_redaction_config,
        test_security_middleware_imports,
        test_secret_detection,
    ]

    passed = 0
    failed = 0

    print("Running basic security functionality tests...\n")

    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ {test.__name__} failed with exception: {e}")
            failed += 1
        print()

    print(f"Test Results: {passed} passed, {failed} failed")
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
