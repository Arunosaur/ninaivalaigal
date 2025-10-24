# SPDX-License-Identifier: Proprietary
"""Test configuration for core API unit tests."""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure the repository root (and its ``src`` compatibility package) are
# available before any unit test imports. Pytest imports ``conftest`` prior to
# the individual test modules, so this adjustment happens early in collection.
_REPO_ROOT = Path(__file__).resolve().parents[2]
for candidate in (_REPO_ROOT, _REPO_ROOT / "src"):
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
