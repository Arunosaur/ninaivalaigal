"""
Redaction Configuration

Defines redaction rules by context sensitivity tier and configurable parameters.
"""

import os
from enum import Enum
from dataclasses import dataclass
from typing import Dict, List, Optional


class ContextSensitivity(Enum):
    """Context sensitivity tiers for redaction rules"""
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"
    SECRETS = "secrets"


@dataclass
class RedactionRule:
    """Configuration for a specific redaction rule"""
    name: str
    enabled: bool
    pattern: Optional[str] = None
    replacement: str = "<REDACTED>"
    min_confidence: float = 0.7
    description: str = ""


class RedactionConfig:
    """Centralized redaction configuration"""
    
    def __init__(self):
        self.enabled = os.getenv('REDACTION_ENABLED', 'true').lower() == 'true'
        self.default_tier = ContextSensitivity(os.getenv('REDACTION_DEFAULT_TIER', 'internal'))
        self.audit_enabled = os.getenv('REDACTION_AUDIT_ENABLED', 'true').lower() == 'true'
        self.min_entropy = float(os.getenv('REDACTION_MIN_ENTROPY', '4.5'))
        self.min_length = int(os.getenv('REDACTION_MIN_LENGTH', '20'))
    
    def get_rules_for_tier(self, tier: ContextSensitivity) -> List[str]:
        """Get applicable redaction rules for a sensitivity tier"""
        return REDACTION_RULES.get(tier, [])
    
    def get_tier_rules(self, tier: ContextSensitivity) -> 'TierRules':
        """Get tier rules object for compatibility"""
        rules = self.get_rules_for_tier(tier)
        return TierRules(allowed_patterns=[], redaction_patterns=rules)


@dataclass
class TierRules:
    """Tier rules for compatibility"""
    allowed_patterns: List[str]
    redaction_patterns: List[str]


# Redaction rules by sensitivity tier
REDACTION_RULES = {
    ContextSensitivity.PUBLIC: [
        'basic_profanity_filter',
    ],
    ContextSensitivity.INTERNAL: [
        'basic_profanity_filter',
        'email_partial_redaction',
        'phone_number_redaction',
    ],
    ContextSensitivity.CONFIDENTIAL: [
        'basic_profanity_filter',
        'email_full_redaction',
        'phone_number_redaction',
        'financial_data_redaction',
        'low_entropy_secrets',
        'aws_access_keys',
        'github_tokens',
        'openai_api_keys',
    ],
    ContextSensitivity.RESTRICTED: [
        'all_pii_redaction',
        'high_entropy_secrets',
        'credential_patterns',
        'compliance_sensitive_data',
        'aws_access_keys',
        'aws_secret_keys',
        'github_tokens',
        'openai_api_keys',
        'jwt_tokens',
        'database_urls',
        'credit_card_numbers',
    ],
    ContextSensitivity.SECRETS: [
        'mandatory_redaction',  # Never stored in raw form
        'placeholder_only',
        'all_high_entropy_strings',
        'all_credential_patterns',
    ]
}

# Rule definitions with patterns and configurations
RULE_DEFINITIONS = {
    'basic_profanity_filter': RedactionRule(
        name='basic_profanity_filter',
        enabled=True,
        replacement='<INAPPROPRIATE_CONTENT>',
        description='Filter basic inappropriate content'
    ),
    'email_partial_redaction': RedactionRule(
        name='email_partial_redaction',
        enabled=True,
        pattern=r'([a-zA-Z0-9._%+-]+)@([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
        replacement=r'\1@<REDACTED_DOMAIN>',
        description='Partially redact email addresses (keep username)'
    ),
    'email_full_redaction': RedactionRule(
        name='email_full_redaction',
        enabled=True,
        pattern=r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
        replacement='<REDACTED_EMAIL>',
        description='Fully redact email addresses'
    ),
    'phone_number_redaction': RedactionRule(
        name='phone_number_redaction',
        enabled=True,
        pattern=r'(\+1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}',
        replacement='<REDACTED_PHONE>',
        description='Redact phone numbers'
    ),
    'financial_data_redaction': RedactionRule(
        name='financial_data_redaction',
        enabled=True,
        replacement='<REDACTED_FINANCIAL>',
        description='Redact financial account numbers and routing numbers'
    ),
    'low_entropy_secrets': RedactionRule(
        name='low_entropy_secrets',
        enabled=True,
        min_confidence=0.6,
        replacement='<REDACTED_SECRET>',
        description='Redact low-entropy secrets (entropy >= 3.5)'
    ),
    'high_entropy_secrets': RedactionRule(
        name='high_entropy_secrets',
        enabled=True,
        min_confidence=0.8,
        replacement='<REDACTED_HIGH_ENTROPY>',
        description='Redact high-entropy secrets (entropy >= 4.5)'
    ),
    'aws_access_keys': RedactionRule(
        name='aws_access_keys',
        enabled=True,
        pattern=r'AKIA[0-9A-Z]{16}',
        replacement='<REDACTED_AWS_ACCESS_KEY>',
        min_confidence=0.95,
        description='AWS access key IDs'
    ),
    'aws_secret_keys': RedactionRule(
        name='aws_secret_keys',
        enabled=True,
        replacement='<REDACTED_AWS_SECRET_KEY>',
        min_confidence=0.8,
        description='AWS secret access keys'
    ),
    'github_tokens': RedactionRule(
        name='github_tokens',
        enabled=True,
        pattern=r'ghp_[a-zA-Z0-9]{36}',
        replacement='<REDACTED_GITHUB_TOKEN>',
        min_confidence=0.95,
        description='GitHub personal access tokens'
    ),
    'openai_api_keys': RedactionRule(
        name='openai_api_keys',
        enabled=True,
        pattern=r'sk-[a-zA-Z0-9]{48}',
        replacement='<REDACTED_OPENAI_API_KEY>',
        min_confidence=0.95,
        description='OpenAI API keys'
    ),
    'jwt_tokens': RedactionRule(
        name='jwt_tokens',
        enabled=True,
        pattern=r'eyJ[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+',
        replacement='<REDACTED_JWT_TOKEN>',
        min_confidence=0.9,
        description='JWT tokens'
    ),
    'database_urls': RedactionRule(
        name='database_urls',
        enabled=True,
        pattern=r'postgresql://[^:]+:[^@]+@[^/]+/\w+',
        replacement='<REDACTED_DATABASE_URL>',
        min_confidence=0.95,
        description='Database connection URLs'
    ),
    'credit_card_numbers': RedactionRule(
        name='credit_card_numbers',
        enabled=True,
        pattern=r'\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13}|3[0-9]{13}|6(?:011|5[0-9]{2})[0-9]{12})\b',
        replacement='<REDACTED_CREDIT_CARD>',
        min_confidence=0.9,
        description='Credit card numbers'
    ),
    'all_pii_redaction': RedactionRule(
        name='all_pii_redaction',
        enabled=True,
        replacement='<REDACTED_PII>',
        description='Comprehensive PII redaction'
    ),
    'credential_patterns': RedactionRule(
        name='credential_patterns',
        enabled=True,
        replacement='<REDACTED_CREDENTIAL>',
        description='Generic credential patterns'
    ),
    'compliance_sensitive_data': RedactionRule(
        name='compliance_sensitive_data',
        enabled=True,
        replacement='<REDACTED_COMPLIANCE>',
        description='GDPR/HIPAA sensitive data'
    ),
    'mandatory_redaction': RedactionRule(
        name='mandatory_redaction',
        enabled=True,
        replacement='<NEVER_STORED>',
        description='Data that should never be stored in raw form'
    ),
    'placeholder_only': RedactionRule(
        name='placeholder_only',
        enabled=True,
        replacement='<PLACEHOLDER>',
        description='Replace with placeholder only'
    ),
    'all_high_entropy_strings': RedactionRule(
        name='all_high_entropy_strings',
        enabled=True,
        replacement='<REDACTED_ENTROPY>',
        min_confidence=0.7,
        description='All high-entropy strings regardless of pattern'
    ),
    'all_credential_patterns': RedactionRule(
        name='all_credential_patterns',
        enabled=True,
        replacement='<REDACTED_ALL_CREDS>',
        description='All known credential patterns'
    )
}


# Global redaction configuration instance
redaction_config = RedactionConfig()
