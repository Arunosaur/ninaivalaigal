from __future__ import annotations
try:
    from prometheus_client import Counter
except Exception:  # pragma: no cover
    # lightweight shim if prometheus_client isn't installed in test envs
    class _C:
        def __init__(self, *a, **k): pass
        def labels(self, *a, **k): return self
        def inc(self, *a, **k): pass
    def Counter(*a, **k): return _C()

# RBAC denials by permission (bounded cardinality: permission name only)
rbac_denials_total = Counter(
    "rbac_denials_total",
    "Count of RBAC permission denials",
    ["permission"]
)

# JWT/JWKS operational metrics
jwt_unknown_kid_total = Counter(
    "jwt_unknown_kid_total",
    "JWT header had unknown kid during JWKS verification"
)
jwt_jwks_fetch_failures_total = Counter(
    "jwt_jwks_fetch_failures_total",
    "Failures when fetching JWKS signing keys"
)
jwt_neg_kid_cache_hits_total = Counter(
    "jwt_neg_kid_cache_hits_total",
    "Count of negative-kid cache hits (recently unknown kid)"
)
