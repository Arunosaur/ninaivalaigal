from __future__ import annotations
import time, json, base64, threading
from typing import Dict, Optional, List

try:
    import jwt  # PyJWT
    from jwt import PyJWKClient
except Exception:  # pragma: no cover
    jwt = None
    PyJWKClient = None

from .subject_ctx import SubjectContext

class NegativeKidCache:
    def __init__(self, ttl_seconds: int = 600):
        self.ttl = ttl_seconds
        self._store: Dict[str, float] = {}
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
    def __init__(self, secret: Optional[str] = None, algorithms: Optional[List[str]] = None,
                 jwks_url: Optional[str] = None, audience: Optional[str] = None,
                 issuer: Optional[str] = None, leeway_seconds: int = 120,
                 negative_kid_ttl: int = 600) -> None:
        self.secret = secret
        self.algorithms = algorithms or ["HS256"]
        self.jwks_url = jwks_url
        self.audience = audience
        self.issuer = issuer
        self.leeway = leeway_seconds
        self._neg_kid = NegativeKidCache(negative_kid_ttl)
        self._jwks_client = PyJWKClient(jwks_url) if (jwks_url and PyJWKClient) else None

    def _header(self, token: str) -> Dict[str, object]:
        try:
            seg = token.split(".")[0]
            pad = "=" * (-len(seg) % 4)
            return json.loads(base64.urlsafe_b64decode(seg + pad).decode("utf-8"))
        except Exception:
            return {}

    def resolve(self, token: str) -> SubjectContext:
        if not token:
            return SubjectContext()
        options = {"verify_aud": self.audience is not None}
        kwargs = {"algorithms": self.algorithms, "options": options, "leeway": self.leeway}
        if self.audience:
            kwargs["audience"] = self.audience
        if self.issuer:
            kwargs["issuer"] = self.issuer

        claims: Dict[str, object] = {}
        if self._jwks_client:
            hdr = self._header(token)
            kid = hdr.get("kid") if isinstance(hdr, dict) else None
            if isinstance(kid, str) and self._neg_kid.contains(kid):
                return SubjectContext(claims={})
            try:
                signing_key = self._jwks_client.get_signing_key_from_jwt(token).key
            except Exception:
                if isinstance(kid, str):
                    self._neg_kid.add(kid)
                return SubjectContext(claims={})
            try:
                claims = jwt.decode(token, signing_key, **kwargs)  # type: ignore
            except Exception:
                return SubjectContext(claims={})
        else:
            if not jwt:  # pragma: no cover
                return SubjectContext()
            try:
                claims = jwt.decode(token, self.secret, **kwargs)  # type: ignore
            except Exception:
                return SubjectContext(claims={})

        user_id = str(claims.get("sub")) if claims.get("sub") else None
        org_id = str(claims.get("org_id")) if claims.get("org_id") else None
        team_id = str(claims.get("team_id")) if claims.get("team_id") else None
        roles_obj = claims.get("roles", [])
        roles = [str(r) for r in roles_obj] if isinstance(roles_obj, (list, tuple)) else []

        return SubjectContext(user_id=user_id, org_id=org_id, team_id=team_id, roles=roles, claims=claims)
