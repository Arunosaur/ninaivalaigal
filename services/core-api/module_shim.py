#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
"""
Module Shim Utility

Merges shared contract modules with local service implementations,
allowing imports like:
- from auth.v1.models import Token (shared contracts)
- from auth import create_refresh_token (local implementation)

Usage in local_run.py or other entry points:
    from module_shim import merge_auth_module
    merge_auth_module()
"""

import importlib.util
import sys
from pathlib import Path
from typing import Any


def merge_auth_module() -> None:
    """
    Merge shared auth contracts with local auth implementation.

    Sets up sys.path and creates a merged auth module that:
    1. Preserves auth.v1.models from shared contracts
    2. Adds local auth.py functions (create_refresh_token, etc.)
    3. Maintains package metadata for submodule resolution
    """

    # Get project root
    project_root = Path(__file__).resolve().parent.parent.parent

    # Add shared contracts to Python path
    shared_contracts_path = project_root / "shared" / "contracts" / "python"
    if shared_contracts_path.exists() and str(shared_contracts_path) not in sys.path:
        sys.path.insert(0, str(shared_contracts_path))

    # Add service directory to Python path
    service_path = Path(__file__).resolve().parent
    if str(service_path) not in sys.path:
        sys.path.insert(0, str(service_path))

    try:
        # Import shared contracts auth module first (has auth.v1.models)
        import auth as shared_auth

        # Load local auth.py implementation
        local_auth_path = service_path / "auth.py"
        if not local_auth_path.exists():
            raise FileNotFoundError(f"Local auth.py not found at {local_auth_path}")

        spec = importlib.util.spec_from_file_location("auth_local", local_auth_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Could not load spec from {local_auth_path}")

        local_auth = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(local_auth)

        # Merge: Copy local implementation attributes to shared auth module
        for attr_name in dir(local_auth):
            if not attr_name.startswith("_"):
                # Only copy if not already in shared auth (preserve contracts)
                if not hasattr(shared_auth, attr_name):
                    setattr(shared_auth, attr_name, getattr(local_auth, attr_name))

        # Ensure auth module is properly registered in sys.modules
        sys.modules["auth"] = shared_auth

        print("✅ Auth module merged: contracts + local implementation")

    except ImportError as e:
        print(f"⚠️  Warning: Could not merge auth modules: {e}")
        print("   Falling back to local auth.py only")
        # Fallback: just use local auth.py
        import auth  # noqa: F401


def merge_module(
    module_name: str, shared_contracts_subpath: str, local_module_path: Path, prefer_local: bool = False
) -> Any:
    """
    Generic module merger for any shared contract + local implementation.

    Args:
        module_name: Name of module to merge (e.g., "auth", "rbac")
        shared_contracts_subpath: Path within shared/contracts/python
        local_module_path: Path to local implementation file
        prefer_local: If True, local attributes override shared contracts

    Returns:
        Merged module object

    Example:
        merge_module(
            "rbac",
            "rbac/v1",
            Path(__file__).parent / "rbac_impl.py"
        )
    """
    project_root = Path(__file__).resolve().parent.parent.parent

    # Add shared contracts to path
    shared_path = project_root / "shared" / "contracts" / "python"
    if shared_path.exists() and str(shared_path) not in sys.path:
        sys.path.insert(0, str(shared_path))

    # Add local directory to path
    local_dir = local_module_path.parent
    if str(local_dir) not in sys.path:
        sys.path.insert(0, str(local_dir))

    # Import shared module
    shared_module = importlib.import_module(module_name)

    # Load local module
    spec = importlib.util.spec_from_file_location(f"{module_name}_local", local_module_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load {local_module_path}")

    local_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(local_module)

    # Merge attributes
    for attr_name in dir(local_module):
        if attr_name.startswith("_"):
            continue

        if prefer_local or not hasattr(shared_module, attr_name):
            setattr(shared_module, attr_name, getattr(local_module, attr_name))

    # Register in sys.modules
    sys.modules[module_name] = shared_module

    return shared_module


# Convenience function for common use case
def setup_service_modules() -> None:
    """
    Setup all common service module shims.

    Call this at the start of local_run.py or test setup.
    """
    merge_auth_module()
    # Add other modules as needed:
    # merge_rbac_module()
    # merge_database_module()
    print("✅ Service modules initialized")


if __name__ == "__main__":
    # Test the shim
    setup_service_modules()

    # Verify imports work
    from auth import authenticate_user, create_refresh_token
    from auth.v1.models import Token

    print(f"✅ Token model available: {Token}")
    print(f"✅ create_refresh_token available: {create_refresh_token}")
    print(f"✅ authenticate_user available: {authenticate_user}")
