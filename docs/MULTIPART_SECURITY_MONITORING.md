# Multipart Security Monitoring & Canary Deployment Guide

## Executive Summary

This document outlines the monitoring, alerting, and canary deployment strategy for the v1.1.0 multipart security hardening system. The implementation provides comprehensive upload vector protection with production-ready monitoring and clear rollback procedures.

## Production-Ready Features ✅

### Security Hardening
- **Hardened Starlette adapter** with stream-time enforcement, early abort, part-count cap
- **Archive blocking** on text endpoints with UTF-8-only + CTE guards  
- **Magic-byte detection** (PE/ELF/Mach-O/Java/MP4) with clear 413/415/400 mapping
- **Binary endpoint archive safety** with compression-ratio checks and entry caps
- **Filename security** with Unicode normalization, RFC 5987 parsing, traversal prevention

### Operational Readiness
- **35/35 passing tests** with consolidated security guide and migration docs
- **/healthz/config** surfaces live limits with boot-time validation
- **7 bounded reject reasons** for clear operational visibility
- **RBAC protection** with snapshot + pre-commit gate preventing silent privilege drift

## Canary Deployment Plan (1-2 days)

### Phase 1: Canary Deployment
```bash
# Deploy to canary environment
kubectl apply -f k8s/canary-deployment.yml

# Verify canary health
curl https://canary.ninaivalaigal.com/healthz/config
```

### Phase 2: Monitoring Setup
```bash
# Apply Prometheus alert rules
kubectl apply -f monitoring/prometheus-alerts.yml

# Import Grafana dashboard
curl -X POST https://grafana.example.com/api/dashboards/db \
  -H "Content-Type: application/json" \
  -d @monitoring/grafana-dashboard.json
```

### Phase 3: Traffic Routing
```bash
# Route 5% traffic to canary
kubectl patch ingress ninaivalaigal --patch '{"spec":{"rules":[{"host":"api.ninaivalaigal.com","http":{"paths":[{"path":"/","backend":{"serviceName":"ninaivalaigal-canary","servicePort":80,"weight":5}}]}}]}}'
```

## Key Metrics to Monitor

### Primary Metrics
| Metric | Description | Alert Threshold |
|--------|-------------|-----------------|
| `multipart_reject_total{reason}` | Rejections by reason | >50 in 10m (page) |
| `multipart_parts_total` | Total parts processed | Baseline tracking |
| `multipart_bytes_total` | Total bytes processed | Baseline tracking |
| `multipart_processing_duration_seconds` | Processing latency | P95 <5ms target |

### Rejection Reasons
- `archive_blocked` - Archive uploads on text endpoints
- `invalid_encoding` - UTF-8 bypass attempts  
- `magic_byte_detected` - Binary file detection
- `size_limit_exceeded` - Part/file size violations
- `part_count_exceeded` - Too many multipart parts
- `filename_unsafe` - Path traversal/unsafe names
- `compression_ratio_suspicious` - Zip bomb detection

## Prometheus Alert Rules

### Critical Alerts (Page Severity)
```yaml
# Spike in adapter rejections
- alert: MultipartRejectsSpiking
  expr: increase(multipart_reject_total[10m]) > 50
  for: 10m
  labels:
    severity: page

# Archive uploads on text endpoints  
- alert: ArchiveUploadsOnTextEndpoints
  expr: increase(multipart_reject_total{reason="archive_blocked"}[10m]) > 10
  for: 10m
  labels:
    severity: page
```

### Warning Alerts (Ticket Severity)
```yaml
# Invalid encodings (client bug/attack)
- alert: InvalidEncodingAttacks
  expr: increase(multipart_reject_total{reason="invalid_encoding"}[10m]) > 10
  for: 10m
  labels:
    severity: ticket
```

## Operational Queries

### Top Rejecting Tenants
```promql
topk(10, sum by (tenant) (rate(multipart_reject_total[5m])))
```

### Top Rejecting Endpoints
```promql
topk(10, sum by (endpoint) (rate(multipart_reject_total[5m])))
```

### Rejection Reasons Breakdown
```promql
sum by (reason) (rate(multipart_reject_total[5m]))
```

### Performance Monitoring
```promql
# P50/P95 latency
histogram_quantile(0.50, rate(multipart_processing_duration_seconds_bucket[5m]))
histogram_quantile(0.95, rate(multipart_processing_duration_seconds_bucket[5m]))

# Throughput
rate(multipart_parts_total[5m])
```

## Rollback Procedures

### Emergency Rollback (Feature Flag)
```bash
# Disable archive checks (block → warn)
curl -X POST https://api.ninaivalaigal.com/admin/feature-flags \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -d '{"archive_checks_enabled": false}'

# Verify flag status
curl https://api.ninaivalaigal.com/healthz/config | jq '.feature_flags'
```

### Full Rollback (Deployment)
```bash
# Rollback to previous version
kubectl rollout undo deployment/ninaivalaigal

# Verify rollback
kubectl rollout status deployment/ninaivalaigal
```

### Partial Rollback (Traffic Shift)
```bash
# Reduce canary traffic to 0%
kubectl patch ingress ninaivalaigal --patch '{"spec":{"rules":[{"host":"api.ninaivalaigal.com","http":{"paths":[{"path":"/","backend":{"serviceName":"ninaivalaigal-stable","servicePort":80,"weight":100}}]}}]}}'
```

## Troubleshooting Guide

### High Rejection Rate
1. **Check rejection reasons**: `sum by (reason) (rate(multipart_reject_total[5m]))`
2. **Identify top tenants**: `topk(10, sum by (tenant) (rate(multipart_reject_total[5m])))`
3. **Sample rejected requests**: Check application logs for detailed rejection context
4. **Consider feature flag**: Temporarily disable strict checks if legitimate traffic affected

### Performance Issues
1. **Check P95 latency**: Target <5ms for multipart processing
2. **Monitor memory usage**: Large files may cause memory pressure
3. **Check Redis health**: Idempotency store performance impacts
4. **Review part count limits**: High part counts increase processing time

### Archive Upload Attacks
1. **Immediate response**: Verify archive blocking is active
2. **Investigate source**: Check tenant/IP patterns in logs
3. **Escalate if needed**: Contact security team for attack analysis
4. **Document patterns**: Update detection rules if new attack vectors found

## Dashboard Links

- **Security Overview**: https://grafana.example.com/d/security-overview
- **Multipart Processing**: https://grafana.example.com/d/multipart-security  
- **Performance Metrics**: https://grafana.example.com/d/performance-overview
- **Canary Health**: https://grafana.example.com/d/canary-deployment

## Runbook References

- [Multipart Security Incidents](./runbooks/multipart-security.md)
- [Archive Upload Attacks](./runbooks/archive-upload-attacks.md)
- [Encoding Attack Response](./runbooks/encoding-attacks.md)
- [Canary Rollback Procedures](./runbooks/canary-rollback.md)
- [Performance Tuning](./runbooks/performance-tuning.md)

## Contact Information

- **Security Team**: security@ninaivalaigal.com
- **SRE On-Call**: +1-555-SRE-CALL
- **Escalation**: CTO (critical security incidents)

---

**Status**: Production Ready ✅  
**Last Updated**: 2025-09-16  
**Next Review**: 2025-10-16
