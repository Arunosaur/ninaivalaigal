#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""Local development entrypoint for the Core API service."""

import importlib
import importlib.util
import os
import sys
import types
from pathlib import Path

import uvicorn

ROOT = Path(__file__).resolve().parent
SHARED_CONTRACTS = ROOT.parent.parent / "shared" / "contracts"

# Ensure shared contracts and service paths are importable (shared first).
sys.path = [p for p in sys.path if Path(p).resolve() != ROOT]
sys.path.insert(0, str(SHARED_CONTRACTS))
sys.path.insert(1, str(ROOT))

# Load the shared `auth` package so `auth.v1` imports resolve.
contracts_auth = importlib.import_module("auth")

# Load the service's local auth module under a temporary name.
local_auth_spec = importlib.util.spec_from_file_location("_core_api_auth", ROOT / "auth.py")
if local_auth_spec is None or local_auth_spec.loader is None:  # pragma: no cover - sanity check
    raise RuntimeError("Unable to load core API auth module")

local_auth = importlib.util.module_from_spec(local_auth_spec)

# Temporarily expose contracts module as `auth` so `from auth.v1` works during load.
previous_auth = sys.modules.get("auth")
sys.modules["auth"] = contracts_auth
local_auth_spec.loader.exec_module(local_auth)

# Merge shared contracts onto the local auth module so `import auth` returns service logic.
local_auth.__dict__.setdefault("contracts", contracts_auth)
local_auth.__dict__.setdefault("contract_models", contracts_auth)
for name, value in contracts_auth.__dict__.items():
    if name.startswith("__") and name not in {"__path__", "__package__", "__spec__"}:
        continue
    if not hasattr(local_auth, name):
        setattr(local_auth, name, value)

# Ensure Python treats the merged module as a package for submodule imports like `auth.v1`.
if hasattr(contracts_auth, "__path__"):
    local_auth.__path__ = contracts_auth.__path__  # type: ignore[attr-defined]
if getattr(contracts_auth, "__spec__", None) is not None:
    local_auth.__spec__ = contracts_auth.__spec__

sys.modules["auth"] = local_auth
if previous_auth is not None:
    sys.modules.setdefault("contracts.auth", contracts_auth)

import main  # noqa: E402  pylint: disable=wrong-import-position

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=int(os.getenv("PORT", "18000")))
