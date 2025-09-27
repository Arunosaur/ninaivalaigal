# Production Deployment Checklist

## Ninaivalaigal Security Middleware - Production Readiness

This checklist ensures safe and secure deployment of the Ninaivalaigal security middleware suite to production environments.

## Pre-Deployment Requirements

### 1. Environment Variables Configuration

**Required Production Variables:**
```bash
# Application Environment
APP_ENV=production

# JWT Configuration
NINAIVALAIGAL_JWKS_URL=https://your-auth-provider.com/.well-known/jwks.json
NINAIVALAIGAL_JWT_AUDIENCE=your-api-audience
NINAIVALAIGAL_JWT_ISSUER=https://your-auth-provider.com

# Redis Configuration
REDIS_URL=redis://your-redis-host:6379/0

# Security Configuration
FAIL_CLOSED_TIER_THRESHOLD=3
SECURITY_GUARD_PROFILE=edge-decompress
MAX_BODY_BYTES=10485760

# Feature Toggles
ENABLE_COMPRESSION_GUARD=true
ENABLE_MULTIPART_ADAPTER=true
ENABLE_GLOBAL_SCRUBBING=true

# Idempotency Configuration
IDEMPOTENCY_TTL_SECONDS=3600
```

**Optional Production Variables:**
```bash
# Monitoring and Observability
PROMETHEUS_METRICS_PORT=9090
LOG_LEVEL=INFO

# Advanced Security
BINARY_MASQUERADE_BYTE_CAP=262144
JWKS_NEGATIVE_CACHE_TTL=300
```

### 2. Infrastructure Prerequisites

- [ ] **Redis Instance**: High-availability Redis cluster with persistence enabled
- [ ] **JWKS Endpoint**: Accessible HTTPS endpoint for JWT key verification
- [ ] **Load Balancer**: Configured with proper health check endpoints
- [ ] **Monitoring**: Prometheus/Grafana stack for metrics collection
- [ ] **Logging**: Centralized logging with structured JSON format

### 3. Security Validation

Run the configuration validator before deployment:

```bash
# Test configuration validation
python -c "
from server.security.config.validator import load_security_config, validate_or_raise
cfg = load_security_config()
validate_or_raise(cfg)
print('✅ Configuration validation passed')
"
```

## Deployment Steps

### Step 1: Pre-Deployment Testing

- [ ] **Run Complete Test Suite**
  ```bash
  python -m pytest tests/test_rbac_policy_snapshot.py \
                   tests/test_middleware_order_parity.py \
                   tests/test_policy_version_gate.py \
                   tests/test_subject_ctx_provider_injection.py \
                   tests/test_config_validator.py -v
  ```

- [ ] **Policy Snapshot Validation**
  ```bash
  python tests/test_rbac_policy_snapshot.py
  ```

- [ ] **Middleware Order Parity Check**
  ```bash
  python tests/test_middleware_order_parity.py
  ```

### Step 2: Configuration Deployment

- [ ] **Deploy Environment Variables** to production environment
- [ ] **Validate Configuration** using health endpoints:
  ```bash
  curl https://your-api.com/healthz/config/validate
  ```

- [ ] **Verify JWKS Connectivity**:
  ```bash
  curl -f $NINAIVALAIGAL_JWKS_URL
  ```

- [ ] **Test Redis Connectivity**:
  ```bash
  redis-cli -u $REDIS_URL ping
  ```

### Step 3: Application Deployment

- [ ] **Deploy Application** with security middleware enabled
- [ ] **Verify Health Endpoints**:
  ```bash
  curl https://your-api.com/healthz/config
  curl https://your-api.com/health
  ```

- [ ] **Test Authentication Flow**:
  ```bash
  # Test with valid JWT
  curl -H "Authorization: Bearer $VALID_JWT" https://your-api.com/protected-endpoint

  # Test without JWT (should fail gracefully)
  curl https://your-api.com/protected-endpoint
  ```

### Step 4: Security Verification

- [ ] **Binary Masquerade Detection Test**:
  ```bash
  # Upload binary file with text content-type (should be blocked)
  curl -X POST -H "Content-Type: text/plain" \
       --data-binary @/bin/ls \
       https://your-api.com/upload
  ```

- [ ] **Compression Guard Test**:
  ```bash
  # Send malformed compressed data (should be blocked)
  curl -X POST -H "Content-Encoding: gzip" \
       -H "Content-Type: application/json" \
       --data "invalid-gzip-data" \
       https://your-api.com/api/endpoint
  ```

- [ ] **Idempotency Key Test**:
  ```bash
  # Send duplicate requests with same idempotency key
  IDEM_KEY="test-$(date +%s)"
  curl -X POST -H "Idempotency-Key: $IDEM_KEY" \
       -H "Content-Type: application/json" \
       --data '{"test": "data"}' \
       https://your-api.com/api/endpoint

  # Second request should return cached response
  curl -X POST -H "Idempotency-Key: $IDEM_KEY" \
       -H "Content-Type: application/json" \
       --data '{"test": "data"}' \
       https://your-api.com/api/endpoint
  ```

## Post-Deployment Monitoring

### 1. Metrics to Monitor

**Security Metrics:**
- `security_guard_profile_total` - Guard profile activation counts
- `binary_masquerade_detections_total` - Binary masquerade detection events
- `jwt_verification_failures_total` - JWT verification failure rate
- `idempotency_key_collisions_total` - Idempotency key collision rate
- `fail_closed_activations_total` - Fail-closed policy activations

**Performance Metrics:**
- `middleware_processing_duration_seconds` - Middleware processing latency
- `redis_operation_duration_seconds` - Redis operation latency
- `jwks_fetch_duration_seconds` - JWKS fetch latency

**Error Metrics:**
- `security_middleware_errors_total` - Security middleware error rate
- `config_validation_failures_total` - Configuration validation failures

### 2. Alerting Rules

**Critical Alerts:**
- JWT verification failure rate > 5%
- Redis connectivity failures
- Configuration validation failures
- Fail-closed activations (indicates security threats)

**Warning Alerts:**
- Binary masquerade detection rate > 1%
- JWKS fetch latency > 1s
- Idempotency key collision rate > 0.1%

### 3. Log Monitoring

Monitor for these log patterns:
- `"level":"ERROR","component":"security-middleware"`
- `"event":"fail_closed_activated"`
- `"event":"binary_masquerade_detected"`
- `"event":"jwt_verification_failed"`

## Rollback Procedures

### Emergency Rollback

If critical security issues are detected:

1. **Immediate Actions:**
   ```bash
   # Disable security middleware (emergency only)
   export ENABLE_SECURITY_MIDDLEWARE=false

   # Scale down to previous version
   kubectl rollout undo deployment/ninaivalaigal-api
   ```

2. **Gradual Rollback:**
   ```bash
   # Disable specific features
   export ENABLE_COMPRESSION_GUARD=false
   export ENABLE_MULTIPART_ADAPTER=false
   export ENABLE_GLOBAL_SCRUBBING=false
   ```

### Configuration Rollback

```bash
# Revert to previous configuration
kubectl rollout undo configmap/ninaivalaigal-config
kubectl rollout restart deployment/ninaivalaigal-api
```

## Security Audit Checklist

### 1. Policy Compliance

- [ ] **RBAC Policy Snapshot** matches approved baseline
- [ ] **Middleware Order** matches production specification
- [ ] **Fail-Closed Tier Threshold** set to ≥ 3 in production
- [ ] **JWT Verification** enabled with proper JWKS endpoint

### 2. Data Protection

- [ ] **Global Log Scrubbing** enabled to redact secrets
- [ ] **Binary Upload Protection** active with masquerade detection
- [ ] **Compression Attack Protection** enabled
- [ ] **Idempotency Store** properly secured with TTL

### 3. Operational Security

- [ ] **Health Endpoints** do not expose sensitive information
- [ ] **Error Messages** do not leak internal details
- [ ] **Monitoring** captures security events without exposing secrets
- [ ] **Configuration Validation** prevents unsafe deployments

## Compliance Documentation

### 1. Required Documentation

- [ ] **Security Architecture Review** - Complete system design
- [ ] **Threat Model Analysis** - Identified threats and mitigations
- [ ] **Penetration Test Results** - External security assessment
- [ ] **Code Review Report** - Security-focused code review

### 2. Audit Trail

- [ ] **Deployment Logs** - Complete deployment history
- [ ] **Configuration Changes** - All security configuration modifications
- [ ] **Policy Updates** - RBAC policy change history
- [ ] **Security Incidents** - Any security-related events

## Success Criteria

Deployment is considered successful when:

- [ ] All tests pass (17/17 test suite)
- [ ] Configuration validation passes
- [ ] Health endpoints return healthy status
- [ ] Security features are active and monitoring
- [ ] No critical alerts triggered in first 24 hours
- [ ] Performance metrics within acceptable ranges
- [ ] Security audit requirements satisfied

## Emergency Contacts

**Security Team:**
- Primary: security-team@company.com
- Secondary: security-oncall@company.com

**DevOps Team:**
- Primary: devops-team@company.com
- Secondary: infrastructure-oncall@company.com

**Product Team:**
- Primary: product-team@company.com

---

**Deployment Approved By:**
- [ ] Security Lead: _________________ Date: _________
- [ ] DevOps Lead: _________________ Date: _________
- [ ] Product Lead: _________________ Date: _________

**Post-Deployment Sign-off:**
- [ ] Security Verification Complete: _________________ Date: _________
- [ ] Monitoring Active: _________________ Date: _________
- [ ] Documentation Updated: _________________ Date: _________
