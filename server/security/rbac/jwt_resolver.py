from __future__ import annotations

import base64
import json
import threading
import time

try:
    import jwt
    from jwt import PyJWKClient
except Exception:  # pragma: no cover
    jwt = None
    PyJWKClient = None

from ..observability.tracing import start_span
from .metrics import (
    jwt_jwks_fetch_failures_total,
    jwt_neg_kid_cache_hits_total,
    jwt_unknown_kid_total,
)
from .subject_ctx import SubjectContext


class Backoff:
    def __init__(self, base=0.2, cap=5.0):
        self.base, self.cap = base, cap
        self.failures = 0
        self.lock = threading.Lock()
    def sleep(self):
        with self.lock:
            self.failures += 1
            delay = min(self.cap, self.base * (2 ** (self.failures - 1)))
        time.sleep(delay)
    def reset(self):
        with self.lock:
            self.failures = 0

class NegativeKidCache:
    def __init__(self, ttl_seconds: int = 600):
        self.ttl = ttl_seconds
        self._store: dict[str, float] = {}
        self._lock = threading.Lock()

    def add(self, kid: str) -> None:
        with self._lock:
            self._store[kid] = time.time() + self.ttl

    def contains(self, kid: str) -> bool:
        with self._lock:
            exp = self._store.get(kid)
            if not exp:
                return False
            if time.time() > exp:
                del self._store[kid]
                return False
            return True

class JWTClaimsResolver:
    def __init__(
        self,
        secret: str | None = None,
        algorithms: list[str] | None = None,
        jwks_url: str | None = None,
        audience: str | None = None,
        issuer: str | None = None,
        leeway_seconds: int = 120,
        negative_kid_ttl: int = 600,
        require_claims: list[str] | None = None,
        max_token_lifetime_s: int | None = None,
    ) -> None:
        self.secret = secret
        self.algorithms = algorithms or ["HS256"]
        self.jwks_url = jwks_url
        self.audience = audience
        self.issuer = issuer
        self.leeway = leeway_seconds
        self._neg_kid = NegativeKidCache(negative_kid_ttl)
        self._jwks_client = PyJWKClient(jwks_url, timeout=3) if (jwks_url and PyJWKClient) else None
        self._jwks_backoff = Backoff()
        self.require_claims = set(require_claims or ["sub", "org_id", "team_id", "roles", "exp"])
        self.max_token_lifetime_s = max_token_lifetime_s  # e.g., 3600 for 1h

    def _header(self, token: str) -> dict[str, object]:
        try:
            seg = token.split(".")[0]
            pad = "=" * (-len(seg) % 4)
            return json.loads(base64.urlsafe_b64decode(seg + pad).decode("utf-8"))
        except Exception:
            return {}

    def resolve(self, token: str) -> SubjectContext:
        with start_span("auth.validate_jwt") as span:
            if not token or not jwt:
                if span: span.set_attribute("auth.present", False)
                return SubjectContext()

            options = {"verify_aud": self.audience is not None}
            kwargs = {"algorithms": self.algorithms, "options": options, "leeway": self.leeway}
            if self.audience: kwargs["audience"] = self.audience
            if self.issuer: kwargs["issuer"] = self.issuer

            claims: dict[str, object] = {}
            used_jwks = False

            if self._jwks_client:
                used_jwks = True
                hdr = self._header(token)
                kid = hdr.get("kid") if isinstance(hdr, dict) else None
                if isinstance(kid, str) and self._neg_kid.contains(kid):
                    jwt_neg_kid_cache_hits_total.inc()
                    if span: span.set_attribute("auth.neg_kid_cache", True)
                    return SubjectContext(claims={})
                try:
                    signing_key = self._jwks_client.get_signing_key_from_jwt(token).key
                    self._jwks_backoff.reset()
                except Exception:
                    jwt_unknown_kid_total.inc()
                    jwt_jwks_fetch_failures_total.inc()
                    self._jwks_backoff.sleep()
                    if isinstance(kid, str):
                        self._neg_kid.add(kid)
                    return SubjectContext(claims={})
                try:
                    claims = jwt.decode(token, signing_key, **kwargs)  # type: ignore
                except Exception:
                    return SubjectContext(claims={})
            else:
                try:
                    claims = jwt.decode(token, self.secret, **kwargs)  # type: ignore
                except Exception:
                    return SubjectContext(claims={})

            # Required-claims enforcement + max token lifetime
            missing = [c for c in self.require_claims if c not in claims or claims.get(c) in (None, "", [])]
            if missing:
                if span: span.set_attribute("auth.missing_claims", ",".join(missing))
                return SubjectContext(claims={})

            if self.max_token_lifetime_s:
                iat = int(claims.get("iat", 0)) if isinstance(claims.get("iat"), int) else 0
                exp = int(claims.get("exp", 0)) if isinstance(claims.get("exp"), int) else 0
                if iat and exp and (exp - iat) > self.max_token_lifetime_s:
                    if span: span.set_attribute("auth.too_long_lifetime", True)
                    return SubjectContext(claims={})

            user_id = str(claims.get("sub")) if claims.get("sub") else None
            org_id = str(claims.get("org_id")) if claims.get("org_id") else None
            team_id = str(claims.get("team_id")) if claims.get("team_id") else None
            roles_obj = claims.get("roles", [])
            roles = [str(r) for r in roles_obj] if isinstance(roles_obj, (list, tuple)) else []

            if span:
                span.set_attribute("auth.alg", ",".join(self.algorithms))
                span.set_attribute("auth.used_jwks", used_jwks)
                span.set_attribute("auth.kid_present", "kid" in (self._header(token) or {}))

            return SubjectContext(user_id=user_id, org_id=org_id, team_id=team_id, roles=roles, claims=claims)
