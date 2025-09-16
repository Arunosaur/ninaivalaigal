# Security Policy

## Privacy Commitments

**We never store raw secrets.** Redaction happens before persistence and before logs/traces.

### Data Protection Guarantees

1. **Pre-Persistence Redaction**: All sensitive data is redacted before being stored in any database, cache, or persistent storage system.

2. **Pre-Logging Redaction**: All application logs, audit trails, and telemetry data undergo automatic redaction to prevent sensitive data leakage.

3. **Memory Safety**: Sensitive data is not retained in application memory beyond the immediate processing window required for redaction.

4. **Transport Security**: All data in transit is protected using TLS 1.3+ encryption with perfect forward secrecy.

## Supported Detectors

Our security middleware automatically detects and redacts the following types of sensitive information:

### API Keys and Tokens
- **OpenAI API Keys**: `sk-*` patterns (48+ characters)
- **AWS Access Keys**: `AKIA*` patterns (20 characters)
- **GitHub Personal Access Tokens**: `ghp_*` patterns (36+ characters)
- **Slack Bot Tokens**: `xoxb-*` patterns
- **JWT Tokens**: Standard three-part JWT format
- **Generic High-Entropy Tokens**: Configurable entropy threshold detection

### Credentials and Certificates
- **PEM-encoded Keys**: Private keys, certificates, and certificate signing requests
- **SSH Keys**: RSA, DSA, ECDSA, and Ed25519 key formats
- **Database Connection Strings**: MySQL, PostgreSQL, MongoDB, Redis patterns

### Personal Identifiable Information (PII)
- **Email Addresses**: Full or partial redaction based on sensitivity tier
- **Phone Numbers**: US and international formats
- **Credit Card Numbers**: All major card types (Visa, MasterCard, Amex, etc.)
- **Social Security Numbers**: US SSN patterns
- **IP Addresses**: IPv4 and IPv6 addresses

### Custom Patterns
- **Configurable Regex Patterns**: Support for organization-specific secret formats
- **Context-Aware Detection**: Sensitivity tier-based detection rules
- **Entropy-Based Detection**: Automatic high-entropy string identification

## How to Request New Detectors

To request support for additional secret types or patterns:

1. **Create an Issue**: Open a GitHub issue with the label `security-enhancement`
2. **Provide Pattern Details**: Include example patterns (with fake/sanitized data)
3. **Specify Use Case**: Describe the business need and sensitivity level
4. **Security Review**: Our security team will review and prioritize the request

### Issue Template for New Detectors
```markdown
## New Detector Request

**Secret Type**: [e.g., "Stripe API Keys"]
**Pattern Description**: [e.g., "sk_live_* or sk_test_* followed by 24 characters"]
**Example Pattern** (sanitized): [e.g., "sk_test_XXXX...XXXX (24 chars)"]
**Sensitivity Tier**: [PUBLIC/INTERNAL/CONFIDENTIAL/RESTRICTED/SECRETS]
**Business Justification**: [Why this detector is needed]
**Compliance Requirement**: [Any regulatory requirements]
```

## Security Architecture

### Multi-Layer Protection

1. **Content-Type Guards**: Prevent processing of binary files and oversized payloads
2. **Request Redaction**: Incoming HTTP request bodies are redacted before reaching application logic
3. **Response Redaction**: Outgoing HTTP response bodies are redacted before client delivery
4. **Log Scrubbing**: Application logs are automatically scrubbed of sensitive field names and values
5. **Audit Trail**: Immutable audit logging of all redaction events for compliance

### Sensitivity Tiers

Our redaction system operates on five sensitivity tiers:

- **PUBLIC**: Basic content filtering, no secret detection
- **INTERNAL**: Email partial redaction, phone number masking
- **CONFIDENTIAL**: API key detection, full email redaction, financial data protection
- **RESTRICTED**: All PII redaction, high-entropy secret detection, comprehensive credential protection
- **SECRETS**: Mandatory redaction enforcement, placeholder-only storage, maximum security processing

### Performance Characteristics

- **Small Payloads** (<1KB): <1ms processing overhead
- **Medium Payloads** (1-100KB): 2-5ms processing overhead
- **Large Payloads** (>1MB): Streaming processing with constant memory usage
- **Throughput Impact**: <5% degradation under normal load conditions

## Compliance and Standards

### Regulatory Compliance
- **GDPR**: Automated PII detection and redaction for EU data protection
- **CCPA**: California Consumer Privacy Act compliance for personal information
- **HIPAA**: Healthcare data protection patterns and audit requirements
- **PCI DSS**: Credit card data redaction and secure handling
- **SOX**: Financial data protection and audit trail requirements

### Security Standards
- **SOC 2 Type II**: Comprehensive audit logging and access controls
- **ISO 27001**: Information security management system compliance
- **NIST Cybersecurity Framework**: Risk-based security controls
- **OWASP Top 10**: Protection against common web application vulnerabilities

## Incident Response

### Security Incident Reporting

If you discover a security vulnerability or potential data exposure:

1. **Do NOT** create a public GitHub issue
2. **Email**: security@ninaivalaigal.com with details
3. **Include**: Steps to reproduce, potential impact, and suggested fixes
4. **Response Time**: We will acknowledge within 24 hours and provide updates every 72 hours

### Vulnerability Disclosure Policy

We follow responsible disclosure practices:

- **Initial Response**: 24 hours
- **Triage and Assessment**: 72 hours  
- **Fix Development**: 30 days for critical, 90 days for non-critical
- **Public Disclosure**: After fix deployment and customer notification

## Security Configuration

### Environment Variables

```bash
# Core redaction settings
REDACTION_ENABLED=true
REDACTION_DEFAULT_TIER=CONFIDENTIAL
REDACTION_AUDIT_ENABLED=true

# Detection thresholds
REDACTION_MIN_ENTROPY=4.0
REDACTION_MIN_LENGTH=8

# Performance tuning
REDACTION_CHUNK_SIZE=8192
REDACTION_OVERLAP_SIZE=64

# Content-type restrictions
REDACTION_ALLOWED_TYPES="text/,application/json,application/x-www-form-urlencoded"
REDACTION_MAX_BODY_SIZE=10485760  # 10MB
```

### Deployment Security

#### Production Checklist
- [ ] Enable comprehensive audit logging
- [ ] Configure appropriate sensitivity tiers for all endpoints
- [ ] Set up security monitoring and alerting
- [ ] Implement log retention policies
- [ ] Configure rate limiting and DDoS protection
- [ ] Enable TLS 1.3+ with HSTS headers
- [ ] Implement proper authentication and authorization
- [ ] Regular security assessments and penetration testing

#### Security Headers
Our middleware automatically adds security headers:
- `Strict-Transport-Security`: Force HTTPS connections
- `X-Content-Type-Options`: Prevent MIME type sniffing
- `X-Frame-Options`: Prevent clickjacking attacks
- `X-XSS-Protection`: Enable XSS filtering
- `Content-Security-Policy`: Restrict resource loading
- `Referrer-Policy`: Control referrer information leakage

## Monitoring and Alerting

### Security Metrics
- `redaction.secrets.detected`: Number of secrets found and redacted
- `redaction.requests.total`: Total redaction requests processed
- `redaction.errors.total`: Redaction processing failures
- `redaction.processing.duration`: Average processing time per request

### Alert Conditions
- High-entropy secret detection above baseline
- Redaction processing failures
- Unusual redaction patterns or volumes
- Performance degradation beyond thresholds
- Potential bypass attempts or security violations

## Contact Information

- **Security Team**: security@ninaivalaigal.com
- **General Support**: support@ninaivalaigal.com
- **Documentation**: https://docs.ninaivalaigal.com/security
- **Status Page**: https://status.ninaivalaigal.com

---

*This security policy is reviewed quarterly and updated as needed. Last updated: September 2025*
