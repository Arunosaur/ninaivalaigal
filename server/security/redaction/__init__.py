"""
Redaction package for sensitive data detection and redaction
"""

from .audit import AuditEventType, RedactionAuditEvent, RedactionAuditLogger
from .config import ContextSensitivity, redaction_config
from .detectors import CombinedSecretDetector, ContextAwareDetector, SecretMatch
from .processors import ContextualRedactor, RedactionResult

# Create global audit logger instance
redaction_audit_logger = RedactionAuditLogger()


class RedactionEngine:
    """Main redaction engine that combines detection and processing"""

    def __init__(self):
        self.detector = CombinedSecretDetector()
        self.processor = ContextualRedactor()

    def redact(self, text: str, sensitivity_tier: ContextSensitivity) -> RedactionResult:
        """Redact sensitive data from text"""
        # Process redaction using the contextual processor (which handles detection internally)
        return self.processor.redact(text, sensitivity_tier)


__all__ = [
    'CombinedSecretDetector',
    'SecretMatch',
    'ContextAwareDetector',
    'ContextualRedactor',
    'RedactionResult',
    'RedactionEngine',
    'RedactionAuditLogger',
    'RedactionAuditEvent',
    'AuditEventType',
    'ContextSensitivity',
    'redaction_config',
    'redaction_audit_logger'
]
