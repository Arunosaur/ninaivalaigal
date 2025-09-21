"""
Tier-Aware Security Middleware

Surfaces tier threshold into detector calls and middleware configuration
for fail-closed policy enforcement based on data sensitivity tiers.
"""

import logging
from collections.abc import Callable
from enum import IntEnum
from typing import Any

from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send


class DataTier(IntEnum):
    """Data sensitivity tiers for fail-closed policy."""

    PUBLIC = 1
    INTERNAL = 2
    CONFIDENTIAL = 3
    RESTRICTED = 4
    TOP_SECRET = 5


class TierAwareDetectorWrapper:
    """Wrapper that injects tier context into detector calls."""

    def __init__(
        self,
        detector_fn: Callable[[str], str],
        fail_closed_threshold: int = 3,
        fallback_tier: int = 2,
    ):
        self.detector_fn = detector_fn
        self.fail_closed_threshold = fail_closed_threshold
        self.fallback_tier = fallback_tier
        self.logger = logging.getLogger("tier.detector")

    def __call__(
        self, text: str, tier: int | None = None, context: dict[str, Any] | None = None
    ) -> str:
        """
        Call detector with tier awareness.

        Args:
            text: Text to process
            tier: Data sensitivity tier (1-5)
            context: Additional context for logging
        """
        effective_tier = tier or self.fallback_tier

        try:
            # Log tier-aware processing
            self.logger.debug(f"Processing text with tier {effective_tier}")

            # Call original detector
            result = self.detector_fn(text)

            # Log successful processing
            self.logger.info(f"Detector succeeded for tier {effective_tier}")
            return result

        except Exception as e:
            # Apply tier-based failure policy
            if effective_tier >= self.fail_closed_threshold:
                # Fail closed for high tiers
                self.logger.error(
                    f"Detector failed for tier {effective_tier} (>= {self.fail_closed_threshold}), "
                    f"failing closed: {e}"
                )
                raise TierPolicyViolation(
                    f"Security detector failed for tier {effective_tier}: {e}",
                    tier=effective_tier,
                    threshold=self.fail_closed_threshold,
                )
            else:
                # Best effort for low tiers
                self.logger.warning(
                    f"Detector failed for tier {effective_tier} (< {self.fail_closed_threshold}), "
                    f"continuing with fallback: {e}"
                )
                return text  # Return original text as fallback


class TierPolicyViolation(Exception):
    """Exception raised when tier policy is violated."""

    def __init__(self, message: str, tier: int, threshold: int):
        super().__init__(message)
        self.tier = tier
        self.threshold = threshold


class TierAwareMiddleware:
    """Middleware that extracts and injects tier context."""

    def __init__(
        self,
        app: ASGIApp,
        detector_wrapper: TierAwareDetectorWrapper,
        tier_extractor: Callable[[Scope], int] | None = None,
    ):
        self.app = app
        self.detector_wrapper = detector_wrapper
        self.tier_extractor = tier_extractor or self._default_tier_extractor
        self.logger = logging.getLogger("tier.middleware")

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope.get("type") != "http":
            await self.app(scope, receive, send)
            return

        # Extract tier from request
        tier = self.tier_extractor(scope)

        # Inject tier into scope for downstream middleware
        scope["security_tier"] = tier

        # Log tier assignment
        path = scope.get("path", "unknown")
        self.logger.info(f"Assigned tier {tier} to {path}")

        # Handle tier policy violations
        async def send_wrapper(message: Message) -> None:
            try:
                await send(message)
            except TierPolicyViolation as e:
                # Convert tier violation to HTTP error
                error_response = JSONResponse(
                    content={
                        "error": "Security policy violation",
                        "message": "Request blocked by security policy",
                        "tier": e.tier,
                        "policy": f"fail_closed_threshold_{e.threshold}",
                    },
                    status_code=422,  # Unprocessable Entity
                )
                await error_response(scope, receive, send)
                return

        await self.app(scope, receive, send_wrapper)

    def _default_tier_extractor(self, scope: Scope) -> int:
        """Default tier extraction based on path patterns."""
        path = scope.get("path", "")
        method = scope.get("method", "GET")

        # High-tier paths
        if "/admin/" in path or "/api/v1/users/" in path:
            return DataTier.RESTRICTED

        # Confidential paths
        if "/api/v1/memories/" in path or "/api/v1/contexts/" in path:
            return DataTier.CONFIDENTIAL

        # Internal paths
        if "/api/" in path and method in ["POST", "PUT", "DELETE"]:
            return DataTier.INTERNAL

        # Public by default
        return DataTier.PUBLIC


class TierConfiguration:
    """Configuration for tier-based security policies."""

    def __init__(self):
        self.tier_policies: dict[int, dict[str, Any]] = {
            DataTier.PUBLIC: {
                "fail_closed": False,
                "log_level": "INFO",
                "cache_ttl": 3600,
                "rate_limit": 1000,
            },
            DataTier.INTERNAL: {
                "fail_closed": False,
                "log_level": "INFO",
                "cache_ttl": 1800,
                "rate_limit": 500,
            },
            DataTier.CONFIDENTIAL: {
                "fail_closed": True,
                "log_level": "WARNING",
                "cache_ttl": 900,
                "rate_limit": 100,
            },
            DataTier.RESTRICTED: {
                "fail_closed": True,
                "log_level": "ERROR",
                "cache_ttl": 300,
                "rate_limit": 50,
            },
            DataTier.TOP_SECRET: {
                "fail_closed": True,
                "log_level": "CRITICAL",
                "cache_ttl": 60,
                "rate_limit": 10,
            },
        }

    def get_policy(self, tier: int) -> dict[str, Any]:
        """Get policy configuration for tier."""
        return self.tier_policies.get(tier, self.tier_policies[DataTier.PUBLIC])

    def should_fail_closed(self, tier: int) -> bool:
        """Check if tier should fail closed on errors."""
        return self.get_policy(tier)["fail_closed"]


def create_tier_aware_detector(
    detector_fn: Callable[[str], str], fail_closed_threshold: int = 3
) -> TierAwareDetectorWrapper:
    """Create tier-aware detector wrapper."""
    return TierAwareDetectorWrapper(detector_fn, fail_closed_threshold)


def extract_tier_from_jwt(scope: Scope) -> int:
    """Extract tier from JWT claims in Authorization header."""
    try:
        headers = dict(scope.get("headers", []))
        auth_header = headers.get(b"authorization", b"").decode()

        if not auth_header.startswith("Bearer "):
            return DataTier.PUBLIC

        token = auth_header[7:]

        # Import here to avoid circular dependency
        from server.security.rbac.context import get_subject_ctx

        context = get_subject_ctx(token)
        tier_str = context.tier or "public"

        # Map tier strings to integers
        tier_mapping = {
            "public": DataTier.PUBLIC,
            "internal": DataTier.INTERNAL,
            "confidential": DataTier.CONFIDENTIAL,
            "restricted": DataTier.RESTRICTED,
            "top_secret": DataTier.TOP_SECRET,
        }

        return tier_mapping.get(tier_str.lower(), DataTier.PUBLIC)

    except Exception:
        # Fallback to public tier on any error
        return DataTier.PUBLIC


def extract_tier_from_path(scope: Scope) -> int:
    """Extract tier from request path patterns."""
    path = scope.get("path", "")
    method = scope.get("method", "GET")

    # Define path-based tier rules
    tier_rules = [
        (r"/admin/", DataTier.TOP_SECRET),
        (r"/api/v1/users/\d+/private", DataTier.RESTRICTED),
        (r"/api/v1/(memories|contexts)/", DataTier.CONFIDENTIAL),
        (r"/api/v1/", DataTier.INTERNAL if method != "GET" else DataTier.PUBLIC),
        (r"/public/", DataTier.PUBLIC),
    ]

    import re

    for pattern, tier in tier_rules:
        if re.search(pattern, path):
            return tier

    return DataTier.PUBLIC


# Metrics and monitoring
class TierMetrics:
    """Metrics collector for tier-based processing."""

    def __init__(self):
        self.counters = {
            "requests_by_tier": {},
            "failures_by_tier": {},
            "policy_violations": {},
        }

    def record_request(self, tier: int):
        """Record request for tier."""
        self.counters["requests_by_tier"][tier] = (
            self.counters["requests_by_tier"].get(tier, 0) + 1
        )

    def record_failure(self, tier: int, error_type: str):
        """Record failure for tier."""
        key = f"{tier}_{error_type}"
        self.counters["failures_by_tier"][key] = (
            self.counters["failures_by_tier"].get(key, 0) + 1
        )

    def record_policy_violation(self, tier: int, threshold: int):
        """Record policy violation."""
        key = f"tier_{tier}_threshold_{threshold}"
        self.counters["policy_violations"][key] = (
            self.counters["policy_violations"].get(key, 0) + 1
        )

    def get_metrics(self) -> dict[str, Any]:
        """Get all metrics."""
        return {
            "tier_requests_total": self.counters["requests_by_tier"],
            "tier_failures_total": self.counters["failures_by_tier"],
            "tier_policy_violations_total": self.counters["policy_violations"],
        }


# Global metrics instance
_tier_metrics = TierMetrics()


def get_tier_metrics() -> dict[str, Any]:
    """Get tier processing metrics."""
    return _tier_metrics.get_metrics()


# Test utilities
def test_tier_awareness():
    """Test tier-aware processing."""

    def mock_detector(text: str) -> str:
        if "fail" in text:
            raise Exception("Mock detector failure")
        return text.replace("secret", "[REDACTED]")

    # Test with different thresholds
    wrapper_strict = TierAwareDetectorWrapper(mock_detector, fail_closed_threshold=3)
    wrapper_lenient = TierAwareDetectorWrapper(mock_detector, fail_closed_threshold=5)

    test_cases = [
        ("normal text", DataTier.PUBLIC, True),
        ("secret data", DataTier.CONFIDENTIAL, True),
        ("fail secret", DataTier.PUBLIC, True),  # Should not fail (tier < threshold)
        ("fail secret", DataTier.RESTRICTED, False),  # Should fail (tier >= threshold)
    ]

    results = []
    for text, tier, should_succeed in test_cases:
        try:
            result = wrapper_strict(text, tier=tier)
            success = True
            output = result
        except TierPolicyViolation:
            success = False
            output = "POLICY_VIOLATION"
        except Exception as e:
            success = False
            output = f"ERROR: {e}"

        results.append(
            {
                "text": text,
                "tier": tier,
                "expected_success": should_succeed,
                "actual_success": success,
                "output": output,
                "test_passed": success == should_succeed,
            }
        )

    return results
