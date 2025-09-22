"""
Configuration Management Module
Extracted from main.py for better code organization
"""

import json
import os
import subprocess
from typing import Any


def load_config() -> dict[str, Any]:
    """
    Load configuration from file and environment variables
    Environment variables take precedence over file configuration
    """
    config_path = "../ninaivalaigal.config.json"
    default_config = {
        "storage": {
            "type": "postgresql",
            "url": "postgresql://mem0user:mem0pass@localhost:5432/mem0db",  # pragma: allowlist secret
        },
        "database_url": "postgresql://mem0user:mem0pass@localhost:5432/mem0db",  # pragma: allowlist secret
    }

    # Load from environment variables first (highest priority)
    env_database_url = os.getenv("NINAIVALAIGAL_DATABASE_URL")
    env_jwt_secret = os.getenv("NINAIVALAIGAL_JWT_SECRET")

    # Load from config file
    config = default_config.copy()

    if os.path.exists(config_path):
        with open(config_path) as f:
            file_config = json.load(f)
            # Merge with defaults
            for key, value in default_config.items():
                if key not in file_config:
                    file_config[key] = value
            config = file_config

    # Override with environment variables (highest priority)
    if env_database_url:
        config["database_url"] = env_database_url
    if env_jwt_secret:
        config["jwt_secret"] = env_jwt_secret

    return config


def get_dynamic_database_url() -> str:
    """Get database URL with dynamic container IP resolution"""
    # Check if we have environment override first
    env_db_url = os.getenv("NINAIVALAIGAL_DATABASE_URL") or os.getenv("DATABASE_URL")
    if env_db_url:
        return env_db_url

    # Try to get dynamic container IPs (works for both Apple Container CLI and Docker)
    try:
        # First try Apple Container CLI
        container_cmd = "container"
        if subprocess.run(["which", "container"], capture_output=True).returncode != 0:
            # Fallback to Docker if container CLI not available
            container_cmd = "docker"

        # Check if we're running in container mode (containers available)
        result = subprocess.run(
            [container_cmd, "ps" if container_cmd == "docker" else "list"],
            capture_output=True,
            text=True,
            timeout=5,
        )

        if result.returncode == 0:
            # Try to get PgBouncer IP first (preferred for connection pooling)
            try:
                pgb_result = subprocess.run(
                    [container_cmd, "inspect", "nv-pgbouncer"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                if pgb_result.returncode == 0:
                    pgb_data = json.loads(pgb_result.stdout)
                    if pgb_data and len(pgb_data) > 0:
                        pgb_ip = pgb_data[0]["networks"][0]["address"].split("/")[0]
                        db_url = (
                            f"postgresql://nina:change_me_securely@{pgb_ip}:6432/nina"
                        )
                        print(f"🔗 Using PgBouncer at {pgb_ip}:6432")
                        return db_url
            except (
                subprocess.TimeoutExpired,
                json.JSONDecodeError,
                KeyError,
                IndexError,
            ):
                pass

            # Fallback to direct database connection
            try:
                db_result = subprocess.run(
                    [container_cmd, "inspect", "nv-db"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                if db_result.returncode == 0:
                    db_data = json.loads(db_result.stdout)
                    if db_data and len(db_data) > 0:
                        db_ip = db_data[0]["networks"][0]["address"].split("/")[0]
                        db_url = (
                            f"postgresql://nina:change_me_securely@{db_ip}:5432/nina"
                        )
                        print(f"🔗 Using direct DB at {db_ip}:5432")
                        return db_url
            except (
                subprocess.TimeoutExpired,
                json.JSONDecodeError,
                KeyError,
                IndexError,
            ):
                pass

    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    # Final fallback to localhost (for development)
    print("⚠️ Falling back to localhost database connection")
    return "postgresql://nina:change_me_securely@localhost:5433/nina"


def get_database_url() -> str:
    """Get database URL from configuration (legacy compatibility)"""
    return get_dynamic_database_url()
