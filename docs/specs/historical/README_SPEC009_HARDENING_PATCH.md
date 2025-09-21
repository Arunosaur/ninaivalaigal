# Spec 009 Hardening Patch (v2)

This patch adds:
- **RBAC metrics:** `rbac_denials_total{permission}`
- **JWKS resilience:** backoff + metrics (`jwt_unknown_kid_total`, `jwt_jwks_fetch_failures_total`, `jwt_neg_kid_cache_hits_total`)
- **Required-claims enforcement:** strict minimal claims + 401 vs 403 mapping
- **Tracing hooks:** spans `auth.validate_jwt` and `rbac.enforce`
- **Tests:** 401/403 semantics and denial counter sanity
- **Grafana row snippet:** RBAC denials correlation panels

## Wiring
- Replace your existing `server/security/rbac/jwt_resolver.py` and `decorators.py` with these versions
  (or merge changes), and add the new `metrics.py` + `observability/tracing.py` helpers.
- Import the RBAC panels JSON into your dashboard or paste the panels into your existing Grafana dashboard.

## Notes
- Metrics use bounded label sets (permission only).
- Tracing is no-op if OpenTelemetry is not installed.
- Prometheus client is optional; a shim is used in tests when unavailable.
