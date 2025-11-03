# SPDX-License-Identifier: Proprietary
"""Test configuration for core API unit tests."""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure the repository root (and its ``src`` compatibility package) are
# available before any unit test imports. Pytest imports ``conftest`` prior to
# the individual test modules, so this adjustment happens early in collection.
_HERE = Path(__file__).resolve()
for ancestor in _HERE.parents:
    if (ancestor / "pyproject.toml").exists():
        _REPO_ROOT = ancestor
        break
else:  # pragma: no cover - fallback for unusual layouts
    _REPO_ROOT = _HERE.parents[3]

for candidate in (
    _REPO_ROOT,
    _REPO_ROOT / "src",
    _REPO_ROOT / "shared" / "storage",
    _REPO_ROOT / "services" / "core-api" / "lib",
):
    path_str = str(candidate)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)

# IMPORTANT: Timezone Override for Auth Tests
# The src/auth.py test shim sets TZ=UTC when imported to ensure consistent
# JWT token expiration testing across different developer timezones.
# This affects ALL tests in this suite once src.auth is imported.
#
# Impact:
# - ✅ Auth unit tests: Correct (timezone-aware datetime now used)
# - ⚠️  Other tests: May see UTC instead of local timezone
#
# If a test suite REQUIRES local timezone behavior:
# 1. Run it in a separate pytest invocation (before auth tests)
# 2. Or mock datetime.now() with your expected timezone
# 3. Or restructure to avoid timezone-dependent assertions
#
# See: tests/auth/test_auth_core.py for timezone-aware testing examples


# Prometheus Registry Cleanup Fixture
# This fixes duplicate metrics registration errors when running multiple test files
# that import modules with Prometheus metrics.
import pytest

try:
    from prometheus_client import REGISTRY, CollectorRegistry

    @pytest.fixture(autouse=True)
    def clear_prometheus_registry():
        """
        Clear Prometheus registry before each test to prevent duplicate metric errors.

        This is necessary because Prometheus metrics are registered at module import time,
        and when multiple test files import modules that define the same metrics,
        we get "Duplicated timeseries" errors.

        By clearing the registry before each test, we ensure test isolation.
        """
        # Store original collectors
        original_collectors = list(REGISTRY._collector_to_names.keys())

        # Clear registry
        REGISTRY._collector_to_names.clear()
        REGISTRY._names_to_collectors.clear()

        yield

        # Restore original state (though for tests, we usually want it clean)
        REGISTRY._collector_to_names.clear()
        REGISTRY._names_to_collectors.clear()

except ImportError:
    # Prometheus client not available, skip fixture
    pass
