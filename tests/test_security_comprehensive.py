"""
Comprehensive security system test suite
"""

import os
import sys

# Add the server directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "server"))


class TestSecuritySystemIntegration:
    """Comprehensive integration tests for the security system"""

    def test_entropy_detection_real_secrets(self):
        """Test entropy detection with real-world secret patterns"""
        from security.utils.entropy import calculate_entropy

        # Real-world high entropy secrets
        high_entropy_samples = [
            "sk-1234567890abcdef1234567890abcdef12345678",  # OpenAI API key
            "AKIAIOSFODNN7EXAMPLE",  # AWS Access Key
            "ghp_1234567890abcdef1234567890abcdef12345678",  # GitHub token
            "test-1234567890-1234567890-abcdefghijklmnopqrstuvwx",  # Test token
        ]

        # Normal text (low entropy)
        low_entropy_samples = [
            "hello world this is normal text",
            "user@example.com",
            "password123",
            "The quick brown fox jumps",
        ]

        # Test high entropy detection
        for secret in high_entropy_samples:
            entropy = calculate_entropy(secret)
            assert (
                entropy > 3.5
            ), f"Secret '{secret}' should have high entropy, got {entropy}"

        # Test low entropy detection
        for text in low_entropy_samples:
            entropy = calculate_entropy(text)
            assert (
                entropy < 4.5
            ), f"Text '{text}' should have low entropy, got {entropy}"

        print("✅ Entropy detection working correctly with real secrets")

    def test_pattern_based_detection(self):
        """Test pattern-based secret detection"""
        from security.redaction.detectors import ContextAwareDetector

        detector = ContextAwareDetector()

        test_cases = [
            (
                "OpenAI key: sk-1234567890abcdef1234567890abcdef12345678",
                "openai_api_key",
            ),
            ("AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE", "aws_access_key"),
            (
                "GitHub token: ghp_1234567890abcdef1234567890abcdef12345678",
                "github_token",
            ),
            ("Contact: user@company.com", "email_address"),
            ("Phone: +1-555-123-4567", "phone_number"),
            ("Card: 4532123456789012", "credit_card"),
        ]

        for text, expected_type in test_cases:
            matches = detector.detect_secrets(text)
            assert len(matches) > 0, f"Should detect secret in: {text}"

            # Check if expected type is found
            found_types = [match.secret_type.value for match in matches]
            assert (
                expected_type in found_types
            ), f"Expected {expected_type} in {found_types} for text: {text}"

        print("✅ Pattern-based detection working correctly")

    def test_combined_detection_system(self):
        """Test the combined detection system"""
        from security.redaction.detectors import CombinedSecretDetector

        detector = CombinedSecretDetector()

        # Complex text with multiple secret types
        complex_text = """
        # Configuration file
        OPENAI_API_KEY=sk-1234567890abcdef1234567890abcdef12345678
        AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
        DATABASE_URL=postgresql://user:secret123@db.example.com:5432/mydb
        ADMIN_EMAIL=admin@company.com
        SUPPORT_PHONE=+1-555-123-4567
        GITHUB_TOKEN=ghp_1234567890abcdef1234567890abcdef12345678
        RANDOM_SECRET=aB3$kL9#mN2@pQ7&rS5*tU8!vW6%xY4^zA1&
        """

        matches = detector.detect_all_secrets(complex_text)

        assert (
            len(matches) >= 5
        ), f"Should detect multiple secrets, found {len(matches)}"

        # Verify deduplication works
        unique_positions = set((match.start_pos, match.end_pos) for match in matches)
        assert len(unique_positions) == len(
            matches
        ), "Should not have duplicate matches"

        print(f"✅ Combined detection system found {len(matches)} secrets")

    def test_redaction_tiers(self):
        """Test redaction behavior across different sensitivity tiers"""
        from security.redaction.config import ContextSensitivity
        from security.redaction.processors import ContextualRedactor

        redactor = ContextualRedactor()

        test_text = (
            "API key: sk-abc123, Email: user@company.com, Phone: +1-555-123-4567"
        )

        # Test different tiers
        tiers = [
            ContextSensitivity.PUBLIC,
            ContextSensitivity.INTERNAL,
            ContextSensitivity.CONFIDENTIAL,
            ContextSensitivity.RESTRICTED,
            ContextSensitivity.SECRETS,
        ]

        results = []
        for tier in tiers:
            result = redactor.redact(test_text, tier)
            results.append((tier, result))
            # Only CONFIDENTIAL and higher tiers should find secrets in this test
            if tier in [
                ContextSensitivity.CONFIDENTIAL,
                ContextSensitivity.RESTRICTED,
                ContextSensitivity.SECRETS,
            ]:
                assert (
                    result.total_secrets_found > 0
                ), f"Should find secrets in tier {tier.value}"

        # Verify that higher tiers find more or equal secrets
        for i in range(len(results) - 1):
            current_tier, current_result = results[i]
            next_tier, next_result = results[i + 1]

            # Higher tiers should find more or equal secrets
            assert (
                next_result.total_secrets_found >= current_result.total_secrets_found
            ), f"Tier {next_tier.value} should find >= secrets than {current_tier.value}"

        print("✅ Redaction tiers working correctly")

    def test_audit_logging(self):
        """Test audit logging functionality"""
        from security.redaction.audit import AuditEventType, RedactionAuditLogger

        logger = RedactionAuditLogger()

        # Test logging different event types
        import asyncio

        async def test_logging():
            # Log a redaction event
            await logger.log_redaction_applied(
                user_id=123,
                context_id=456,
                original_text="API key: sk-test123",
                redacted_text="API key: [REDACTED]",
                secrets_found=1,
                sensitivity_tier="internal",
                processing_time_ms=15.5,
            )

            # Log a policy violation
            await logger.log_policy_violation(
                user_id=123,
                violation_type="unauthorized_access",
                details={"attempted_tier": "secrets", "user_tier": "internal"},
            )

            # Verify events were logged
            assert len(logger.events) >= 2, "Should have logged events"

            # Check event types
            event_types = [event.event_type for event in logger.events]
            assert AuditEventType.REDACTION_APPLIED in event_types
            assert AuditEventType.POLICY_VIOLATION in event_types

        asyncio.run(test_logging())
        print("✅ Audit logging working correctly")

    def test_configuration_management(self):
        """Test configuration management"""
        from security.redaction.config import ContextSensitivity, redaction_config

        # Test default configuration
        assert redaction_config.enabled is not None
        assert redaction_config.default_tier is not None
        assert redaction_config.min_entropy > 0
        assert redaction_config.min_length > 0

        # Test tier rules
        for tier in ContextSensitivity:
            rules = redaction_config.get_tier_rules(tier)
            assert rules is not None, f"Tier {tier} should have rules"
            assert hasattr(
                rules, "allowed_patterns"
            ), f"Tier {tier} should have allowed_patterns"
            assert hasattr(
                rules, "redaction_patterns"
            ), f"Tier {tier} should have redaction_patterns"

        print("✅ Configuration management working correctly")

    def test_performance_large_text(self):
        """Test performance with large text containing secrets"""
        from security.redaction import RedactionEngine
        from security.redaction.config import ContextSensitivity

        engine = RedactionEngine()

        # Create large text with embedded secrets
        large_text_parts = []
        for i in range(500):
            large_text_parts.append(
                f"Line {i}: This is normal content for line number {i}."
            )
            if i % 50 == 0:  # Add secrets every 50 lines
                large_text_parts.append(
                    f"SECRET_{i}=sk-{i:04d}567890abcdef1234567890abcdef12345678"
                )

        large_text = "\n".join(large_text_parts)

        import time

        start_time = time.time()
        result = engine.redact(large_text, ContextSensitivity.CONFIDENTIAL)
        end_time = time.time()

        processing_time = (end_time - start_time) * 1000  # milliseconds

        assert result.total_secrets_found >= 5, "Should find embedded secrets"
        assert (
            processing_time < 3000
        ), f"Should process in <3s, took {processing_time:.2f}ms"

        # Verify secrets were redacted
        assert "sk-0000567890abcdef" not in result.redacted_text

        print(
            f"✅ Performance test passed - processed {len(large_text)} chars in {processing_time:.2f}ms"
        )

    def test_unicode_and_special_characters(self):
        """Test handling of unicode and special characters"""
        from security.redaction import RedactionEngine
        from security.redaction.config import ContextSensitivity

        engine = RedactionEngine()

        unicode_text = """
        🔐 Secrets for café application:
        API Key: sk-1234567890abcdef1234567890abcdef12345678
        Email: admin@café.com
        Message: "Hello 世界! This is a test with émojis 🚀"
        Password: pässwörd123
        """

        result = engine.redact(unicode_text, ContextSensitivity.CONFIDENTIAL)

        assert result.total_secrets_found > 0, "Should detect secrets in unicode text"
        assert "🔐" in result.redacted_text, "Should preserve unicode emoji"
        assert "世界" in result.redacted_text, "Should preserve unicode text"
        assert "émojis" in result.redacted_text, "Should preserve accented characters"
        assert "🚀" in result.redacted_text, "Should preserve unicode emoji"

        print("✅ Unicode and special character handling working correctly")

    def test_edge_cases(self):
        """Test edge cases and error conditions"""
        from security.redaction import RedactionEngine
        from security.redaction.config import ContextSensitivity

        engine = RedactionEngine()

        # Test empty text
        result = engine.redact("", ContextSensitivity.INTERNAL)
        assert result.redacted_text == ""
        assert result.total_secrets_found == 0

        # Test whitespace only
        result = engine.redact("   \n\t  ", ContextSensitivity.INTERNAL)
        assert result.total_secrets_found == 0

        # Test very long single line
        long_line = (
            "a" * 10000 + "sk-1234567890abcdef1234567890abcdef12345678" + "b" * 10000
        )
        result = engine.redact(long_line, ContextSensitivity.CONFIDENTIAL)
        assert result.total_secrets_found > 0

        # Test malformed patterns
        malformed_text = "sk-tooshort ghp_invalid_length"
        result = engine.redact(malformed_text, ContextSensitivity.CONFIDENTIAL)
        # Should not crash, may or may not detect depending on patterns

        print("✅ Edge case handling working correctly")


def run_comprehensive_tests():
    """Run all comprehensive security tests"""
    test_suite = TestSecuritySystemIntegration()

    tests = [
        test_suite.test_entropy_detection_real_secrets,
        test_suite.test_pattern_based_detection,
        test_suite.test_combined_detection_system,
        test_suite.test_redaction_tiers,
        test_suite.test_audit_logging,
        test_suite.test_configuration_management,
        test_suite.test_performance_large_text,
        test_suite.test_unicode_and_special_characters,
        test_suite.test_edge_cases,
    ]

    passed = 0
    failed = 0

    print("🔒 Running Comprehensive Security System Tests\n")
    print("=" * 60)

    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"❌ {test.__name__} failed: {e}")
            failed += 1
        print()

    print("=" * 60)
    print(f"📊 Test Results: {passed} passed, {failed} failed")

    if failed == 0:
        print("🎉 All security tests passed! The system is ready for production.")
    else:
        print("⚠️  Some tests failed. Please review and fix issues before deployment.")

    return failed == 0


if __name__ == "__main__":
    success = run_comprehensive_tests()
    sys.exit(0 if success else 1)
