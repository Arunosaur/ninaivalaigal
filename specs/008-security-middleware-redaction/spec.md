# Spec 008: Security Middleware & Redaction Pipeline

## Overview
Implement a centralized security middleware system with intelligent redaction capabilities that preserves business context while removing sensitive data across all platform interfaces (FastAPI, CLI, IDE clients).

## Objectives
- Create two-layer redaction approach (Memory Value + Secret Hygiene)
- Implement HTTP security headers and rate limiting
- Build entropy + context-aware secret detection
- Establish comprehensive audit trail for redaction events
- Centralize redaction logic for consistent application

## Architecture

### Two-Layer Redaction System

#### Layer 1: Memory Value Layer
Preserves high-value business context:
- Commands and decision-making flows
- Architectural notes and problem-solving context
- User interactions and workflow patterns
- Non-sensitive technical discussions

#### Layer 2: Secret Hygiene Layer
Removes sensitive data before storage:
- API keys, JWTs, database passwords
- OAuth tokens and session identifiers
- Personal identifiable information (PII)
- Financial and compliance-sensitive data

### Component Structure
```
server/security/
├── __init__.py
├── redaction/
│   ├── __init__.py
│   ├── detectors.py          # Entropy + pattern detection
│   ├── processors.py         # Redaction logic
│   ├── audit.py             # Redaction audit trail
│   └── config.py            # Redaction rules configuration
├── middleware/
│   ├── __init__.py
│   ├── security_headers.py   # HTTP security headers
│   ├── rate_limiting.py     # Enhanced rate limiting
│   └── redaction_middleware.py
└── utils/
    ├── __init__.py
    └── entropy.py           # Entropy calculation utilities
```

## Technical Specifications

### 1. Redaction Detectors

#### Entropy-Based Detection
```python
class EntropyDetector:
    def __init__(self, min_entropy=4.5, min_length=20):
        self.min_entropy = min_entropy
        self.min_length = min_length
    
    def calculate_entropy(self, text: str) -> float:
        """Calculate Shannon entropy of text"""
        # Implementation for entropy calculation
        
    def is_high_entropy_secret(self, text: str) -> bool:
        """Detect high-entropy strings that may be secrets"""
        return (len(text) >= self.min_length and 
                self.calculate_entropy(text) >= self.min_entropy)
```

#### Context-Aware Pattern Detection
```python
class ContextAwareDetector:
    PROVIDER_PATTERNS = {
        'aws': r'AKIA[0-9A-Z]{16}',
        'github': r'ghp_[a-zA-Z0-9]{36}',
        'openai': r'sk-[a-zA-Z0-9]{48}',
        'jwt': r'eyJ[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+',
        'database_url': r'postgresql://[^:]+:[^@]+@[^/]+/\w+',
        'email': r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
    }
    
    def detect_secrets(self, text: str) -> List[SecretMatch]:
        """Detect secrets using provider-specific patterns"""
```

### 2. Redaction Processors

#### Contextual Redaction
```python
class ContextualRedactor:
    def redact_with_context(self, text: str, context_tier: ContextSensitivity) -> RedactionResult:
        """Apply tier-appropriate redaction rules"""
        redaction_rules = self.get_rules_for_tier(context_tier)
        
        result = RedactionResult(
            original_text=text,
            redacted_text="",
            redactions_applied=[],
            context_tier=context_tier
        )
        
        for rule in redaction_rules:
            result = rule.apply(result)
            
        return result
```

#### Redaction Rules by Tier
```python
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
    ],
    ContextSensitivity.RESTRICTED: [
        'all_pii_redaction',
        'high_entropy_secrets',
        'credential_patterns',
        'compliance_sensitive_data',
    ],
    ContextSensitivity.SECRETS: [
        'mandatory_redaction',  # Never stored in raw form
        'placeholder_only',
    ]
}
```

### 3. Security Headers Middleware

```python
class SecurityHeadersMiddleware:
    def __init__(self):
        self.headers = {
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY', 
            'X-XSS-Protection': '1; mode=block',
            'Strict-Transport-Security': 'max-age=63072000; includeSubDomains; preload',
            'Content-Security-Policy': "default-src 'self'; script-src 'self' 'unsafe-inline'",
            'Referrer-Policy': 'strict-origin-when-cross-origin',
            'Permissions-Policy': 'geolocation=(), microphone=(), camera=()',
        }
```

### 4. Enhanced Rate Limiting

```python
class EnhancedRateLimiter:
    def __init__(self):
        self.endpoint_limits = {
            '/auth/login': RateLimiter(max_requests=5, window_seconds=300),
            '/auth/signup': RateLimiter(max_requests=3, window_seconds=600),
            '/memory': RateLimiter(max_requests=100, window_seconds=60),
            '/contexts': RateLimiter(max_requests=50, window_seconds=60),
            '/rbac/': RateLimiter(max_requests=20, window_seconds=300),
        }
        
    async def check_rate_limit_with_rbac(self, request: Request) -> bool:
        """Rate limiting with RBAC context awareness"""
        rbac_context = getattr(request.state, 'rbac_context', None)
        
        # Higher limits for admin users
        if rbac_context and rbac_context.has_role(Role.ADMIN):
            return await self.check_admin_rate_limit(request)
        
        return await self.check_standard_rate_limit(request)
```

### 5. Audit Trail System

```python
class RedactionAuditLogger:
    def log_redaction_event(self, event: RedactionEvent):
        """Log redaction events for audit trail"""
        audit_entry = {
            'timestamp': datetime.utcnow(),
            'user_id': event.user_id,
            'context_id': event.context_id,
            'redaction_applied': True,
            'redaction_type': event.redaction_type,
            'sensitivity_tier': event.sensitivity_tier,
            'patterns_matched': event.patterns_matched,
            'entropy_score': event.entropy_score,
            'request_id': event.request_id,
        }
        
        # Store in dedicated audit table
        self.audit_repository.create_redaction_audit(audit_entry)
```

## Database Schema Changes

### Redaction Audit Table
```sql
CREATE TABLE redaction_audits (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    user_id INTEGER REFERENCES users(id),
    context_id INTEGER REFERENCES contexts(id),
    request_id VARCHAR(255),
    redaction_applied BOOLEAN NOT NULL,
    redaction_type VARCHAR(100),
    sensitivity_tier VARCHAR(50),
    patterns_matched JSONB,
    entropy_score FLOAT,
    original_length INTEGER,
    redacted_length INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_redaction_audits_user_id ON redaction_audits(user_id);
CREATE INDEX idx_redaction_audits_timestamp ON redaction_audits(timestamp);
CREATE INDEX idx_redaction_audits_context_id ON redaction_audits(context_id);
```

### Memory Table Enhancement
```sql
ALTER TABLE memories ADD COLUMN redaction_applied BOOLEAN DEFAULT FALSE;
ALTER TABLE memories ADD COLUMN original_entropy_score FLOAT;
ALTER TABLE memories ADD COLUMN sensitivity_tier VARCHAR(50) DEFAULT 'internal';
ALTER TABLE memories ADD COLUMN redaction_audit_id INTEGER REFERENCES redaction_audits(id);
```

## Implementation Plan

### Phase 1: Core Redaction Engine (Week 1)
1. Implement entropy calculation utilities
2. Create context-aware pattern detectors
3. Build redaction processors with tier support
4. Add redaction audit logging
5. Create unit tests for redaction logic

### Phase 2: Middleware Integration (Week 2)  
1. Implement security headers middleware
2. Enhance rate limiting with RBAC awareness
3. Create redaction middleware for FastAPI
4. Integrate with existing RBAC system
5. Add performance monitoring

## Configuration

### Environment Variables
```bash
# Redaction Configuration
REDACTION_ENABLED=true
REDACTION_DEFAULT_TIER=internal
REDACTION_AUDIT_ENABLED=true
REDACTION_MIN_ENTROPY=4.5
REDACTION_MIN_LENGTH=20

# Security Headers
SECURITY_HEADERS_ENABLED=true
CSP_POLICY="default-src 'self'; script-src 'self' 'unsafe-inline'"
HSTS_MAX_AGE=63072000

# Rate Limiting
RATE_LIMITING_ENABLED=true
RATE_LIMITING_REDIS_URL=redis://localhost:6379/1
```

### Redaction Rules Configuration
```yaml
# server/security/redaction/rules.yaml
redaction_rules:
  patterns:
    aws_access_key:
      pattern: "AKIA[0-9A-Z]{16}"
      replacement: "<REDACTED_AWS_KEY>"
      tier: "secrets"
    
    github_token:
      pattern: "ghp_[a-zA-Z0-9]{36}"
      replacement: "<REDACTED_GITHUB_TOKEN>"
      tier: "secrets"
    
    email_address:
      pattern: "[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}"
      replacement: "<REDACTED_EMAIL>"
      tier: "confidential"
  
  entropy_thresholds:
    secrets: 5.0
    confidential: 4.5
    internal: 4.0
    public: 3.5
```

## Testing Strategy

### Unit Tests
```python
class TestRedactionEngine:
    def test_entropy_calculation(self):
        """Test entropy calculation accuracy"""
        
    def test_aws_key_detection(self):
        """Test AWS access key pattern detection"""
        
    def test_context_tier_redaction(self):
        """Test tier-appropriate redaction rules"""
        
    def test_audit_trail_generation(self):
        """Test redaction audit logging"""
```

### Integration Tests
```python
class TestRedactionMiddleware:
    def test_fastapi_integration(self):
        """Test redaction in FastAPI endpoints"""
        
    def test_memory_storage_redaction(self):
        """Test redaction before memory storage"""
        
    def test_rbac_context_preservation(self):
        """Test RBAC context maintained through redaction"""
```

### Performance Tests
```python
class TestRedactionPerformance:
    def test_large_payload_redaction(self):
        """Test redaction performance on large payloads"""
        
    def test_concurrent_redaction_requests(self):
        """Test redaction under concurrent load"""
```

## Security Considerations

### Redaction Bypass Prevention
- All input paths must go through redaction middleware
- Redaction logic centralized to prevent inconsistencies
- Audit trail immutable and tamper-evident
- Regular pattern updates for new secret types

### Performance Impact
- Lazy loading of redaction rules
- Caching of compiled regex patterns
- Async processing for large payloads
- Circuit breaker for redaction service failures

## Migration & Rollback Plan

### Migration Steps
1. Deploy redaction module without enforcement
2. Enable audit logging in read-only mode
3. Gradually enable redaction by endpoint
4. Monitor performance and accuracy
5. Full enforcement rollout

### Rollback Procedures
```sql
-- Rollback redaction audit table
DROP TABLE IF EXISTS redaction_audits;

-- Rollback memory table changes
ALTER TABLE memories DROP COLUMN IF EXISTS redaction_applied;
ALTER TABLE memories DROP COLUMN IF EXISTS original_entropy_score;
ALTER TABLE memories DROP COLUMN IF EXISTS sensitivity_tier;
ALTER TABLE memories DROP COLUMN IF EXISTS redaction_audit_id;
```

### Feature Flags
```python
# Feature flag configuration
REDACTION_FEATURES = {
    'entropy_detection': True,
    'pattern_matching': True,
    'audit_logging': True,
    'middleware_enforcement': False,  # Gradual rollout
}
```

## Success Criteria

### Functional Requirements
- [ ] 99.9% secret detection accuracy on test dataset
- [ ] <50ms redaction latency for typical payloads
- [ ] Complete audit trail for all redaction events
- [ ] Zero false positives on business context preservation
- [ ] Consistent redaction across all platform interfaces

### Security Requirements
- [ ] No secrets stored in raw form in database
- [ ] All HTTP security headers properly configured
- [ ] Rate limiting prevents abuse patterns
- [ ] Redaction bypass attempts logged and blocked
- [ ] Compliance with GDPR/HIPAA redaction requirements

### Performance Requirements
- [ ] <10% performance impact on API response times
- [ ] Redaction scales to 1000+ concurrent requests
- [ ] Memory usage remains under 100MB per worker
- [ ] Audit log storage optimized for long-term retention

This specification provides a comprehensive foundation for implementing enterprise-grade security middleware with intelligent redaction capabilities while maintaining the business value of captured interactions.
