from __future__ import annotations

from collections.abc import Callable
from functools import wraps

from fastapi import HTTPException, Request, status

from ..observability.tracing import start_span
from .jwt_resolver import JWTClaimsResolver
from .metrics import rbac_denials_total
from .subject_ctx import SubjectContext

_resolver: JWTClaimsResolver | None = None


def set_jwt_resolver(resolver: JWTClaimsResolver) -> None:
    global _resolver
    _resolver = resolver


def _extract_token(request: Request) -> str:
    auth = request.headers.get("authorization") or request.headers.get("Authorization")
    if not auth or not auth.lower().startswith("bearer "):
        return ""
    return auth.split(" ", 1)[1].strip()


def _get_ctx(request: Request) -> SubjectContext:
    if _resolver is None:
        return SubjectContext()
    token = _extract_token(request)
    return _resolver.resolve(token)


def _unauth(detail="Authentication required"):
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)


def _forbid(detail="Permission denied"):
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


def require_permission(*required: str):
    required_set = set(required)

    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            request: Request = kwargs.get("request") or next(
                (a for a in args if isinstance(a, Request)), None
            )
            if request is None:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Request not found",
                )

            with start_span("rbac.enforce") as span:
                ctx = _get_ctx(request)
                if not ctx.claims:
                    if span:
                        span.set_attribute("rbac.auth", "unauthenticated")
                    _unauth()

                roles = set(ctx.roles or [])
                if not roles:
                    if span:
                        span.set_attribute("rbac.roles", "none")
                    _unauth("Invalid or missing roles")

                granted = bool(roles & required_set)
                if not granted:
                    if span:
                        span.set_attribute("rbac.granted", False)
                    # increment per-permission counter (bounded)
                    for perm in required_set:
                        rbac_denials_total.labels(permission=perm).inc()
                    _forbid()

                if span:
                    span.set_attribute("rbac.granted", True)
                return await func(*args, **kwargs)

        return wrapper

    return decorator
