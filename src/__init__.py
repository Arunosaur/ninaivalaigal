# SPDX-License-Identifier: Proprietary
"""Project-wide compatibility namespace used by legacy unit tests."""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure the core API service directory is importable before consumers reach for
# modules like ``auth``. This mirrors the runtime environment in which the
# FastAPI service executes, while keeping the tests hermetic.
_CORE_API_DIR = Path(__file__).resolve().parent.parent / "services" / "core-api"
core_dir = str(_CORE_API_DIR)
if core_dir not in sys.path:
    sys.path.insert(0, core_dir)

__all__: list[str] = []
