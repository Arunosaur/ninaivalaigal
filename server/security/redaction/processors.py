"""
Redaction Processors

Implements contextual redaction logic with tier-appropriate rules.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from .config import ContextSensitivity, RedactionConfig, redaction_config
from .detectors import CombinedSecretDetector, SecretMatch, SecretType


@dataclass
class RedactionResult:
    """Result of redaction processing"""
    original_text: str
    redacted_text: str
    redactions_applied: list[dict[str, Any]]
    context_tier: ContextSensitivity
    processing_time_ms: float
    total_secrets_found: int
    entropy_score: float | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'original_length': len(self.original_text),
            'redacted_length': len(self.redacted_text),
            'redactions_applied': self.redactions_applied,
            'context_tier': self.context_tier.value,
            'processing_time_ms': self.processing_time_ms,
            'total_secrets_found': self.total_secrets_found,
            'entropy_score': self.entropy_score,
            'processed_at': datetime.utcnow().isoformat()
        }


class ContextualRedactor:
    """Main redaction processor with context sensitivity awareness"""

    def __init__(self, config: RedactionConfig | None = None):
        self.config = config or redaction_config
        self.secret_detector = CombinedSecretDetector(
            min_entropy=self.config.min_entropy,
            min_length=self.config.min_length
        )

    def redact(self, text: str, context_tier: ContextSensitivity) -> RedactionResult:
        """
        Apply tier-appropriate redaction rules to text.
        
        Args:
            text: Input text to redact
            context_tier: Sensitivity tier determining redaction rules
            
        Returns:
            RedactionResult with redacted text and metadata
        """
        if not self.config.enabled:
            return RedactionResult(
                original_text=text,
                redacted_text=text,
                redactions_applied=[],
                context_tier=context_tier,
                processing_time_ms=0.0,
                total_secrets_found=0
            )

        start_time = datetime.utcnow()

        # Get applicable rules for this tier
        tier_rules = self.config.get_rules_for_tier(context_tier)

        # Detect secrets
        detected_secrets = self.secret_detector.detect_all_secrets(text)

        # Filter secrets based on tier rules and confidence
        applicable_secrets = self._filter_secrets_by_tier(detected_secrets, tier_rules, context_tier)

        # Apply redactions
        redacted_text = self._apply_redactions(text, applicable_secrets)

        # Calculate processing time
        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000

        # Build redaction metadata
        redactions_applied = [
            {
                'secret_type': secret.secret_type.value,
                'start_pos': secret.start_pos,
                'end_pos': secret.end_pos,
                'confidence': secret.confidence,
                'entropy_score': secret.entropy_score,
                'replacement': secret.replacement_text,
                'pattern_name': secret.pattern_name
            }
            for secret in applicable_secrets
        ]

        return RedactionResult(
            original_text=text,
            redacted_text=redacted_text,
            redactions_applied=redactions_applied,
            context_tier=context_tier,
            processing_time_ms=processing_time,
            total_secrets_found=len(applicable_secrets),
            entropy_score=self._calculate_overall_entropy(text)
        )

    def _filter_secrets_by_tier(self, secrets: list[SecretMatch], tier_rules: list[str],
                               context_tier: ContextSensitivity) -> list[SecretMatch]:
        """Filter detected secrets based on tier rules and confidence thresholds"""
        filtered_secrets = []

        for secret in secrets:
            # Check if this secret type should be redacted for this tier
            if self._should_redact_secret(secret, tier_rules, context_tier):
                filtered_secrets.append(secret)

        return filtered_secrets

    def _should_redact_secret(self, secret: SecretMatch, tier_rules: list[str],
                             context_tier: ContextSensitivity) -> bool:
        """Determine if a secret should be redacted based on tier rules"""

        # Special handling for SECRETS tier - redact everything
        if context_tier == ContextSensitivity.SECRETS:
            return True

        # Check specific secret type rules
        secret_type_rules = {
            SecretType.AWS_ACCESS_KEY: 'aws_access_keys',
            SecretType.AWS_SECRET_KEY: 'aws_secret_keys',
            SecretType.GITHUB_TOKEN: 'github_tokens',
            SecretType.OPENAI_API_KEY: 'openai_api_keys',
            SecretType.JWT_TOKEN: 'jwt_tokens',
            SecretType.DATABASE_URL: 'database_urls',
            SecretType.EMAIL_ADDRESS: 'email_full_redaction',
            SecretType.PHONE_NUMBER: 'phone_number_redaction',
            SecretType.CREDIT_CARD: 'credit_card_numbers',
            SecretType.HIGH_ENTROPY_STRING: 'high_entropy_secrets',
            SecretType.GENERIC_API_KEY: 'credential_patterns'
        }

        rule_name = secret_type_rules.get(secret.secret_type)
        if rule_name and rule_name in tier_rules:
            # Check confidence threshold
            from .config import RULE_DEFINITIONS
            rule_def = RULE_DEFINITIONS.get(rule_name)
            if rule_def and secret.confidence >= rule_def.min_confidence:
                return True

        # Check entropy-based rules
        if secret.secret_type == SecretType.HIGH_ENTROPY_STRING:
            if 'high_entropy_secrets' in tier_rules and secret.entropy_score >= self.config.min_entropy:
                return True
            if 'low_entropy_secrets' in tier_rules and secret.entropy_score >= 3.5:
                return True

        # Check catch-all rules
        if 'all_pii_redaction' in tier_rules:
            return secret.secret_type in [SecretType.EMAIL_ADDRESS, SecretType.PHONE_NUMBER]

        if 'all_high_entropy_strings' in tier_rules and secret.entropy_score >= 4.0:
            return True

        if 'all_credential_patterns' in tier_rules:
            return secret.secret_type in [
                SecretType.AWS_ACCESS_KEY, SecretType.AWS_SECRET_KEY,
                SecretType.GITHUB_TOKEN, SecretType.OPENAI_API_KEY,
                SecretType.JWT_TOKEN, SecretType.GENERIC_API_KEY
            ]

        return False

    def _apply_redactions(self, text: str, secrets: list[SecretMatch]) -> str:
        """Apply redactions to text, handling overlaps and maintaining readability"""
        if not secrets:
            return text

        # Sort secrets by position (reverse order to maintain positions during replacement)
        secrets_sorted = sorted(secrets, key=lambda s: s.start_pos, reverse=True)

        redacted_text = text
        for secret in secrets_sorted:
            # Replace the secret with its redaction text
            redacted_text = (
                redacted_text[:secret.start_pos] +
                secret.replacement_text +
                redacted_text[secret.end_pos:]
            )

        return redacted_text

    def _calculate_overall_entropy(self, text: str) -> float:
        """Calculate overall entropy score for the text"""
        from .detectors import EntropyCalculator
        return EntropyCalculator.calculate_shannon_entropy(text)


class TierSpecificRedactor:
    """Specialized redactor for specific sensitivity tiers"""

    def __init__(self, tier: ContextSensitivity):
        self.tier = tier
        self.redactor = ContextualRedactor()

    def redact(self, text: str) -> RedactionResult:
        """Redact text using this tier's rules"""
        return self.redactor.redact(text, self.tier)


class BatchRedactor:
    """Batch processing for multiple texts with different tiers"""

    def __init__(self):
        self.redactor = ContextualRedactor()

    def redact_batch(self, texts_with_tiers: list[tuple]) -> list[RedactionResult]:
        """
        Redact multiple texts with their respective tiers.
        
        Args:
            texts_with_tiers: List of (text, ContextSensitivity) tuples
            
        Returns:
            List of RedactionResult objects
        """
        results = []
        for text, tier in texts_with_tiers:
            result = self.redactor.redact(text, tier)
            results.append(result)

        return results


# RedactionEngine is now defined in __init__.py to avoid duplication
