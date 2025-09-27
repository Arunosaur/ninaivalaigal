# Multipart Security Incident Response Runbook

## Alert: MultipartRejectsSpiking

**Severity**: Page
**Threshold**: >50 rejections in 10 minutes
**Response Time**: Immediate (5 minutes)

### Immediate Actions

1. **Assess Impact**
   ```bash
   # Check current rejection rate
   curl -s "http://prometheus:9090/api/v1/query?query=rate(multipart_reject_total[5m])" | jq '.data.result'

   # Check rejection reasons
   curl -s "http://prometheus:9090/api/v1/query?query=sum by (reason) (rate(multipart_reject_total[5m]))" | jq '.data.result'
   ```

2. **Identify Source**
   ```bash
   # Top rejecting tenants
   curl -s "http://prometheus:9090/api/v1/query?query=topk(10, sum by (tenant) (rate(multipart_reject_total[5m])))" | jq '.data.result'

   # Top rejecting endpoints
   curl -s "http://prometheus:9090/api/v1/query?query=topk(10, sum by (endpoint) (rate(multipart_reject_total[5m])))" | jq '.data.result'
   ```

3. **Check System Health**
   ```bash
   # Verify security middleware health
   curl https://api.ninaivalaigal.com/healthz/config | jq '.security_middleware'

   # Check feature flag status
   curl https://api.ninaivalaigal.com/healthz/config | jq '.feature_flags'
   ```

### Investigation Steps

1. **Sample Rejected Requests**
   ```bash
   # Check application logs for detailed rejection context
   kubectl logs -l app=ninaivalaigal --tail=100 | grep "multipart_reject"

   # Look for patterns in rejection reasons
   kubectl logs -l app=ninaivalaigal --tail=1000 | grep -E "(archive_blocked|invalid_encoding|magic_byte_detected)" | head -20
   ```

2. **Analyze Traffic Patterns**
   - Check if rejections correlate with deployment times
   - Look for unusual traffic spikes from specific tenants/IPs
   - Verify if legitimate file uploads are being blocked

3. **Validate Security Rules**
   - Confirm archive detection is working correctly
   - Check if new file types are triggering false positives
   - Verify Unicode normalization isn't breaking legitimate uploads

### Escalation Criteria

**Escalate to Security Team if**:
- Rejections indicate coordinated attack (same tenant, multiple endpoints)
- New attack vectors not covered by existing rules
- Legitimate business-critical uploads are being blocked

**Escalate to Engineering if**:
- System performance is degraded (P95 latency >50ms)
- Feature flags are not responding
- Security middleware health checks failing

### Resolution Actions

#### Option 1: Temporary Relief (Feature Flag)
```bash
# If legitimate traffic is affected, temporarily disable strict checks
curl -X POST https://api.ninaivalaigal.com/admin/feature-flags \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"archive_checks_enabled": false}'

# Monitor for 10 minutes to confirm relief
watch "curl -s 'http://prometheus:9090/api/v1/query?query=rate(multipart_reject_total[5m])' | jq '.data.result[0].value[1]'"
```

#### Option 2: Targeted Allowlist
```bash
# Add specific tenant/endpoint to allowlist if needed
curl -X POST https://api.ninaivalaigal.com/admin/security-allowlist \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"tenant": "affected-tenant", "endpoint": "/api/upload", "reason": "incident-12345"}'
```

#### Option 3: Rule Adjustment
```bash
# If false positives, adjust detection thresholds
curl -X PATCH https://api.ninaivalaigal.com/admin/security-config \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"magic_byte_threshold": 0.8, "compression_ratio_limit": 100}'
```

### Post-Incident Actions

1. **Document Findings**
   - Root cause of rejection spike
   - Whether it was attack, misconfiguration, or legitimate traffic
   - Actions taken and their effectiveness

2. **Update Detection Rules**
   - Add new patterns if attack vectors discovered
   - Adjust thresholds if false positives occurred
   - Update allowlists for known good patterns

3. **Review Monitoring**
   - Adjust alert thresholds if needed
   - Add new metrics for discovered patterns
   - Update runbook with lessons learned

---

## Alert: ArchiveUploadsOnTextEndpoints

**Severity**: Page
**Threshold**: >10 archive uploads blocked in 10 minutes
**Response Time**: Immediate (5 minutes)

### Immediate Actions

1. **Confirm Attack Vector**
   ```bash
   # Check specific archive types being blocked
   kubectl logs -l app=ninaivalaigal --tail=100 | grep "archive_blocked" | grep -E "(\.zip|\.tar|\.gz|\.rar)"

   # Identify source IPs/tenants
   kubectl logs -l app=ninaivalaigal --tail=100 | grep "archive_blocked" | awk '{print $5}' | sort | uniq -c | sort -nr
   ```

2. **Assess Threat Level**
   - **Low**: Single tenant, accidental uploads
   - **Medium**: Multiple tenants, possible misconfiguration
   - **High**: Coordinated attack, multiple IPs/tenants

3. **Immediate Containment**
   ```bash
   # If high threat, consider temporary IP blocking
   curl -X POST https://api.ninaivalaigal.com/admin/ip-block \
     -H "Authorization: Bearer $ADMIN_TOKEN" \
     -d '{"ip": "suspicious.ip.address", "duration": 3600, "reason": "archive-upload-attack"}'
   ```

### Investigation Steps

1. **Analyze Upload Patterns**
   - File names and extensions being uploaded
   - Upload endpoints being targeted
   - Timing patterns (automated vs manual)

2. **Check for Bypass Attempts**
   - Look for encoding variations (double extensions, Unicode tricks)
   - Check for MIME type spoofing attempts
   - Verify compression ratio checks are working

3. **Validate Business Impact**
   - Confirm no legitimate archive uploads are needed
   - Check with product team on expected file types
   - Verify customer impact is minimal

### Resolution Actions

#### High Confidence Attack
```bash
# Maintain strict blocking, add additional monitoring
curl -X POST https://api.ninaivalaigal.com/admin/security-config \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -d '{"archive_detection_strict": true, "log_all_attempts": true}'
```

#### Legitimate Use Case Discovered
```bash
# Create specific allowlist for business need
curl -X POST https://api.ninaivalaigal.com/admin/upload-policy \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -d '{"endpoint": "/api/backup-upload", "allow_archives": true, "require_auth": true}'
```

---

## Alert: InvalidEncodingAttacks

**Severity**: Ticket
**Response Time**: 1 hour

### Investigation Steps

1. **Analyze Encoding Patterns**
   ```bash
   # Check specific encoding issues
   kubectl logs -l app=ninaivalaigal --tail=500 | grep "invalid_encoding" | head -20

   # Look for bypass attempts
   grep -E "(overlong|surrogate|cesu)" /var/log/ninaivalaigal/security.log
   ```

2. **Determine Intent**
   - **Accidental**: Client library bugs, old software
   - **Malicious**: Deliberate bypass attempts, security testing

3. **Create Ticket**
   - Document encoding patterns observed
   - Include sample requests (redacted)
   - Recommend client fixes or rule updates

### Long-term Actions

1. **Client Education**
   - Update API documentation with encoding requirements
   - Provide client library examples
   - Add validation helpers

2. **Detection Improvement**
   - Add new encoding patterns to detection rules
   - Improve error messages for client debugging
   - Consider graduated response (warn → block)

---

## Emergency Contacts

- **Security Team**: security@ninaivalaigal.com, Slack: #security-incidents
- **SRE On-Call**: +1-555-SRE-CALL, PagerDuty: ninaivalaigal-sre
- **Engineering Manager**: eng-manager@ninaivalaigal.com
- **CTO (Critical Only)**: cto@ninaivalaigal.com

## Useful Commands Reference

```bash
# Quick health check
curl https://api.ninaivalaigal.com/healthz/config | jq '.security_middleware, .feature_flags'

# Current rejection rate
curl -s "http://prometheus:9090/api/v1/query?query=rate(multipart_reject_total[5m])"

# Feature flag emergency disable
curl -X POST https://api.ninaivalaigal.com/admin/feature-flags \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -d '{"archive_checks_enabled": false}'

# View recent security logs
kubectl logs -l app=ninaivalaigal --tail=100 --since=10m | grep -E "(multipart_reject|security_violation)"
```
