"""
Unit tests for security redaction engine
"""

import pytest
import asyncio
from unittest.mock import Mock, patch
from datetime import datetime

from server.security.utils.entropy import calculate_entropy, calculate_base64_entropy, calculate_hex_entropy
from server.security.redaction.detectors import SecretDetector, DetectedSecret
from server.security.redaction.processors import ContextualRedactor
from server.security.redaction.config import ContextSensitivity, redaction_config
from server.security.redaction.audit import RedactionAuditLogger, RedactionEvent, RedactionEventType
from server.security import RedactionEngine


class TestEntropyCalculation:
    """Test entropy calculation utilities"""
    
    def test_shannon_entropy_high(self):
        """Test high entropy strings (likely secrets)"""
        high_entropy_strings = [
            "sk-1234567890abcdef1234567890abcdef12345678",  # OpenAI API key format
            "AKIA1234567890ABCDEF",  # AWS access key format
            "test-1234567890-1234567890-abcdefghijklmnop",  # Test token format
            "ghp_1234567890abcdef1234567890abcdef12345678"  # GitHub token format
        ]
        
        for secret in high_entropy_strings:
            entropy = calculate_entropy(secret)
            assert entropy > 4.0, f"Expected high entropy for {secret}, got {entropy}"
    
    def test_shannon_entropy_low(self):
        """Test low entropy strings (normal text)"""
        low_entropy_strings = [
            "hello world",
            "this is a normal sentence",
            "user@example.com",
            "password123"
        ]
        
        for text in low_entropy_strings:
            entropy = calculate_entropy(text)
            assert entropy < 4.0, f"Expected low entropy for {text}, got {entropy}"
    
    def test_base64_entropy(self):
        """Test base64 entropy calculation"""
        base64_string = "SGVsbG8gV29ybGQ="  # "Hello World" in base64
        entropy = calculate_base64_entropy(base64_string)
        assert entropy > 0, "Base64 entropy should be positive"
    
    def test_hex_entropy(self):
        """Test hex entropy calculation"""
        hex_string = "48656c6c6f20576f726c64"  # "Hello World" in hex
        entropy = calculate_hex_entropy(hex_string)
        assert entropy > 0, "Hex entropy should be positive"


class TestSecretDetection:
    """Test secret detection functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.detector = SecretDetector()
    
    def test_detect_aws_access_key(self):
        """Test AWS access key detection"""
        text = "My AWS key is AKIA1234567890ABCDEF and it's secret"
        secrets = self.detector.detect_secrets(text)
        
        assert len(secrets) > 0, "Should detect AWS access key"
        aws_secret = next((s for s in secrets if s.secret_type == "aws_access_key"), None)
        assert aws_secret is not None, "Should detect AWS access key type"
        assert aws_secret.confidence > 0.8, "Should have high confidence"
    
    def test_detect_github_token(self):
        """Test GitHub token detection"""
        text = "GitHub token: ghp_1234567890abcdef1234567890abcdef12345678"
        secrets = self.detector.detect_secrets(text)
        
        github_secret = next((s for s in secrets if s.secret_type == "github_token"), None)
        assert github_secret is not None, "Should detect GitHub token"
        assert "ghp_" in github_secret.value, "Should capture the token value"
    
    def test_detect_openai_api_key(self):
        """Test OpenAI API key detection"""
        text = "OpenAI API key: sk-1234567890abcdef1234567890abcdef12345678"
        secrets = self.detector.detect_secrets(text)
        
        openai_secret = next((s for s in secrets if s.secret_type == "openai_api_key"), None)
        assert openai_secret is not None, "Should detect OpenAI API key"
        assert openai_secret.confidence > 0.9, "Should have very high confidence"
    
    def test_detect_email(self):
        """Test email detection"""
        text = "Contact me at user@example.com for more info"
        secrets = self.detector.detect_secrets(text)
        
        email_secret = next((s for s in secrets if s.secret_type == "email"), None)
        assert email_secret is not None, "Should detect email"
        assert "user@example.com" in email_secret.value, "Should capture email value"
    
    def test_detect_phone_number(self):
        """Test phone number detection"""
        text = "Call me at +1-555-123-4567 or (555) 987-6543"
        secrets = self.detector.detect_secrets(text)
        
        phone_secrets = [s for s in secrets if s.secret_type == "phone_number"]
        assert len(phone_secrets) >= 1, "Should detect at least one phone number"
    
    def test_detect_credit_card(self):
        """Test credit card detection"""
        text = "My card number is 4532-1234-5678-9012"
        secrets = self.detector.detect_secrets(text)
        
        cc_secret = next((s for s in secrets if s.secret_type == "credit_card"), None)
        assert cc_secret is not None, "Should detect credit card"
    
    def test_entropy_based_detection(self):
        """Test entropy-based secret detection"""
        # High entropy string that doesn't match patterns
        text = "Random secret: aB3$kL9#mN2@pQ7&rS5*tU8!"
        secrets = self.detector.detect_secrets(text)
        
        entropy_secrets = [s for s in secrets if s.secret_type == "high_entropy"]
        assert len(entropy_secrets) > 0, "Should detect high entropy secrets"
    
    def test_no_false_positives_normal_text(self):
        """Test that normal text doesn't trigger false positives"""
        text = "This is a normal sentence with no secrets in it."
        secrets = self.detector.detect_secrets(text)
        
        # Should not detect any secrets in normal text
        assert len(secrets) == 0, "Should not detect secrets in normal text"
    
    def test_deduplication(self):
        """Test that duplicate secrets are deduplicated"""
        text = "Key: sk-abc123 and again sk-abc123"
        secrets = self.detector.detect_secrets(text)
        
        # Should only detect one instance due to deduplication
        openai_secrets = [s for s in secrets if s.secret_type == "openai_api_key"]
        assert len(openai_secrets) <= 1, "Should deduplicate identical secrets"


class TestContextualRedaction:
    """Test contextual redaction processor"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.redactor = ContextualRedactor()
    
    def test_public_tier_no_redaction(self):
        """Test that public tier applies minimal redaction"""
        text = "Contact user@example.com for API key sk-abc123"
        result = self.redactor.redact(text, ContextSensitivity.PUBLIC)
        
        # Public tier should preserve most content
        assert "user@example.com" in result.redacted_text, "Should preserve email in public tier"
        assert "sk-abc123" not in result.redacted_text, "Should still redact API keys in public tier"
    
    def test_internal_tier_moderate_redaction(self):
        """Test internal tier redaction"""
        text = "Contact user@example.com for API key sk-abc123"
        result = self.redactor.redact(text, ContextSensitivity.INTERNAL)
        
        # Internal tier should redact some sensitive info
        assert result.total_secrets_found > 0, "Should find secrets"
        assert len(result.redacted_text) < len(text), "Should apply some redaction"
    
    def test_secrets_tier_maximum_redaction(self):
        """Test secrets tier applies maximum redaction"""
        text = "API key: sk-abc123, AWS: AKIA1234567890ABCDEF, email: user@example.com"
        result = self.redactor.redact(text, ContextSensitivity.SECRETS)
        
        # Secrets tier should redact everything sensitive
        assert "sk-abc123" not in result.redacted_text, "Should redact API key"
        assert "AKIA1234567890ABCDEF" not in result.redacted_text, "Should redact AWS key"
        assert "user@example.com" not in result.redacted_text, "Should redact email"
        assert "[REDACTED" in result.redacted_text, "Should contain redaction markers"
    
    def test_redaction_preserves_structure(self):
        """Test that redaction preserves text structure"""
        text = "Hello user@example.com, your API key is sk-abc123. Thanks!"
        result = self.redactor.redact(text, ContextSensitivity.CONFIDENTIAL)
        
        # Should preserve sentence structure
        assert result.redacted_text.startswith("Hello"), "Should preserve greeting"
        assert result.redacted_text.endswith("Thanks!"), "Should preserve closing"
        assert "," in result.redacted_text, "Should preserve punctuation"
    
    def test_batch_redaction(self):
        """Test batch redaction of multiple texts"""
        texts = [
            "API key: sk-abc123",
            "Email: user@example.com", 
            "Normal text with no secrets"
        ]
        
        results = self.redactor.redact_batch(texts, ContextSensitivity.INTERNAL)
        
        assert len(results) == 3, "Should return results for all texts"
        assert results[0].total_secrets_found > 0, "Should find secrets in first text"
        assert results[1].total_secrets_found > 0, "Should find secrets in second text"
        assert results[2].total_secrets_found == 0, "Should find no secrets in third text"


class TestRedactionAuditLogger:
    """Test redaction audit logging"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.audit_logger = RedactionAuditLogger()
    
    @pytest.mark.asyncio
    async def test_log_redaction_event(self):
        """Test logging redaction events"""
        event = RedactionEvent(
            event_type=RedactionEventType.REDACTION_APPLIED,
            user_id=123,
            context_id=456,
            original_text="API key: sk-abc123",
            redacted_text="API key: [REDACTED-API-KEY]",
            secrets_found=1,
            sensitivity_tier=ContextSensitivity.INTERNAL,
            processing_time_ms=15.5
        )
        
        # Should not raise exception
        await self.audit_logger.log_redaction_event(event)
        
        # Check that event was stored
        assert len(self.audit_logger.events) > 0, "Should store audit event"
        stored_event = self.audit_logger.events[-1]
        assert stored_event.user_id == 123, "Should store correct user ID"
        assert stored_event.secrets_found == 1, "Should store secrets count"
    
    @pytest.mark.asyncio
    async def test_log_policy_violation(self):
        """Test logging policy violations"""
        await self.audit_logger.log_policy_violation(
            user_id=123,
            violation_type="unauthorized_access",
            details={"attempted_tier": "secrets", "user_tier": "internal"}
        )
        
        # Check that violation was logged
        violations = [e for e in self.audit_logger.events if e.event_type == RedactionEventType.POLICY_VIOLATION]
        assert len(violations) > 0, "Should log policy violation"
    
    @pytest.mark.asyncio
    async def test_log_redaction_failure(self):
        """Test logging redaction failures"""
        await self.audit_logger.log_redaction_failure(
            user_id=123,
            error_message="Pattern compilation failed",
            context_data={"pattern": "invalid_regex["}
        )
        
        # Check that failure was logged
        failures = [e for e in self.audit_logger.events if e.event_type == RedactionEventType.REDACTION_FAILED]
        assert len(failures) > 0, "Should log redaction failure"


class TestRedactionEngine:
    """Test the complete redaction engine"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.engine = RedactionEngine()
    
    def test_end_to_end_redaction(self):
        """Test complete redaction workflow"""
        text = """
        Hello team,
        
        Here are the credentials for the new system:
        - API Key: sk-1234567890abcdef1234567890abcdef12345678
        - AWS Access Key: AKIA1234567890ABCDEF
        - Database URL: postgresql://user:pass@localhost:5432/db
        - Admin Email: admin@company.com
        - Support Phone: +1-555-123-4567
        
        Please keep these secure!
        """
        
        result = self.engine.redact(text, ContextSensitivity.CONFIDENTIAL)
        
        # Verify redaction occurred
        assert result.total_secrets_found > 0, "Should detect multiple secrets"
        assert "sk-1234567890abcdef" not in result.redacted_text, "Should redact API key"
        assert "AKIA1234567890ABCDEF" not in result.redacted_text, "Should redact AWS key"
        assert "admin@company.com" not in result.redacted_text, "Should redact email"
        assert "+1-555-123-4567" not in result.redacted_text, "Should redact phone"
        
        # Verify structure preservation
        assert "Hello team" in result.redacted_text, "Should preserve greeting"
        assert "Please keep these secure!" in result.redacted_text, "Should preserve closing"
        assert "[REDACTED" in result.redacted_text, "Should contain redaction markers"
    
    def test_different_sensitivity_tiers(self):
        """Test redaction behavior across different sensitivity tiers"""
        text = "Email admin@company.com about API key sk-abc123"
        
        # Test each tier
        public_result = self.engine.redact(text, ContextSensitivity.PUBLIC)
        internal_result = self.engine.redact(text, ContextSensitivity.INTERNAL)
        confidential_result = self.engine.redact(text, ContextSensitivity.CONFIDENTIAL)
        restricted_result = self.engine.redact(text, ContextSensitivity.RESTRICTED)
        secrets_result = self.engine.redact(text, ContextSensitivity.SECRETS)
        
        # Verify increasing levels of redaction
        assert len(public_result.redacted_text) >= len(internal_result.redacted_text)
        assert len(internal_result.redacted_text) >= len(confidential_result.redacted_text)
        assert len(confidential_result.redacted_text) >= len(restricted_result.redacted_text)
        assert len(restricted_result.redacted_text) >= len(secrets_result.redacted_text)
    
    def test_performance_with_large_text(self):
        """Test redaction performance with large text"""
        # Create large text with embedded secrets
        large_text = "Normal text. " * 1000 + "API key: sk-abc123 " + "More text. " * 1000
        
        import time
        start_time = time.time()
        result = self.engine.redact(large_text, ContextSensitivity.INTERNAL)
        end_time = time.time()
        
        processing_time = (end_time - start_time) * 1000  # Convert to milliseconds
        
        assert result.total_secrets_found > 0, "Should find secrets in large text"
        assert processing_time < 1000, f"Should process large text quickly, took {processing_time}ms"
    
    def test_unicode_and_special_characters(self):
        """Test redaction with unicode and special characters"""
        text = "🔑 API key: sk-abc123 for user café@example.com 中文测试"
        result = self.engine.redact(text, ContextSensitivity.INTERNAL)
        
        assert result.total_secrets_found > 0, "Should detect secrets with unicode"
        assert "🔑" in result.redacted_text, "Should preserve unicode emoji"
        assert "中文测试" in result.redacted_text, "Should preserve unicode text"


class TestConfigurationManagement:
    """Test redaction configuration management"""
    
    def test_default_configuration(self):
        """Test default configuration values"""
        assert redaction_config.enabled == True, "Redaction should be enabled by default"
        assert redaction_config.default_tier == ContextSensitivity.INTERNAL, "Default tier should be internal"
        assert redaction_config.min_entropy > 0, "Min entropy should be positive"
        assert redaction_config.min_length > 0, "Min length should be positive"
    
    def test_tier_rule_configuration(self):
        """Test that all tiers have configured rules"""
        for tier in ContextSensitivity:
            rules = redaction_config.get_tier_rules(tier)
            assert rules is not None, f"Tier {tier} should have rules configured"
            assert len(rules.allowed_patterns) >= 0, f"Tier {tier} should have allowed patterns list"
            assert len(rules.redaction_patterns) >= 0, f"Tier {tier} should have redaction patterns list"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
