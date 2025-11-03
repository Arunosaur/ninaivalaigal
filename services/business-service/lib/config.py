#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""
Configuration Management Module
Extracted from main.py for better code organization
"""

import json
import os
from typing import Any, Optional


def _get_canonical_port(service: str, fallback: str) -> str:
    """Resolve canonical port using ports.nv.yaml offsets via get-port script."""
    nina_env = os.getenv("NINA_ENV", "dev")
    nina_runtime = os.getenv("NINA_RUNTIME", "docker")
    script_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "scripts", "get-port.sh")

    try:
        import subprocess

        result = subprocess.run(  # nosec B603
            [script_path, service, nina_env, nina_runtime],
            capture_output=True,
            text=True,
            timeout=5,
        )
        port = result.stdout.strip()
        if port:
            return port
    except Exception:
        pass

    return fallback


def _build_default_database_url(*, mode: str = "transaction") -> str:
    """Construct PgBouncer-backed database URL honoring session/transaction modes."""

    host = os.getenv("PGBOUNCER_HOST") or os.getenv("POSTGRES_HOST", "localhost")
    user = os.getenv("NINA_DB_USER") or os.getenv("POSTGRES_USER", "nina")
    password = os.getenv("NINA_DB_PASSWORD") or os.getenv("POSTGRES_PASSWORD", "dev_password_change_in_production")
    db_name = os.getenv("NINA_DB_NAME") or os.getenv("POSTGRES_DB", "ninaivalaigal_dev")

    if mode == "session":
        port_env_vars = ["PGBOUNCER_SESS_PORT", "PGBOUNCER_SESSION_PORT", "PGBOUNCER_PORT_SESSION"]
    else:
        port_env_vars = ["PGBOUNCER_TX_PORT", "PGBOUNCER_PORT", "PGBOUNCER_TRANSACTION_PORT"]

    port: Optional[str] = None
    for var in port_env_vars:
        value = os.getenv(var)
        if value:
            port = value
            break

    if not port:
        canonical = _get_canonical_port("pgbouncer", "6432")
        if mode == "session":
            try:
                port = str(int(canonical) + 1)
            except ValueError:
                port = "6433"
        else:
            port = canonical

    return f"postgresql://{user}:{password}@{host}:{port}/{db_name}"


DEFAULT_RUST_DATABASE_URL = _build_default_database_url(mode="transaction")
DEFAULT_RUST_DATABASE_URL_SESSION = _build_default_database_url(mode="session")


def load_config() -> dict[str, Any]:
    """
    Load configuration from file and environment variables
    Environment variables take precedence over file configuration
    """
    config_path = "../ninaivalaigal.config.json"
    default_config = {
        "storage": {
            "type": "postgresql",
            "url": DEFAULT_RUST_DATABASE_URL,
        },
        "database_url": DEFAULT_RUST_DATABASE_URL,
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
    """Get database URL with dynamic container IP resolution and environment awareness"""
    # Check if we have environment override first
    env_db_url = os.getenv("NINAIVALAIGAL_DATABASE_URL") or os.getenv("DATABASE_URL")
    if env_db_url:
        return env_db_url

    # Get environment and runtime for dynamic discovery
    nina_env = os.getenv("NINA_ENV", "dev")
    nina_runtime = os.getenv("NINA_RUNTIME", "docker")

    # Calculate dynamic port using our port assignment logic
    try:
        import subprocess

        script_path = os.path.join(os.path.dirname(__file__), "..", "scripts", "get-port.sh")
        postgres_port = subprocess.run(
            [script_path, "postgres", nina_env, nina_runtime],
            capture_output=True,
            text=True,
            timeout=5,
        ).stdout.strip()

        pgbouncer_port = subprocess.run(
            [script_path, "pgbouncer", nina_env, nina_runtime],
            capture_output=True,
            text=True,
            timeout=5,
        ).stdout.strip()
    except Exception:
        # Fallback to default ports
        postgres_port = "5432"
        pgbouncer_port = "6432"

    # Construct database name following our naming convention
    db_name = f"ninaivalaigal_{nina_env}"
    db_user = os.getenv("NINA_DB_USER", "ninaivalaigal_app")
    db_password = os.getenv("NINA_DB_PASSWORD", "secure_nina_password")

    # Try to get dynamic container IPs (works for both Apple Container CLI and Docker)
    try:
        # First try Apple Container CLI
        container_cmd = "container"
        if subprocess.run(["which", "container"], capture_output=True).returncode != 0:  # nosec B607
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
            # Try to get PgBouncer IP first (preferred for production)
            pgbouncer_container = f"ninaivalaigal-{nina_env}-pgbouncer"
            try:
                pgb_result = subprocess.run(
                    [container_cmd, "inspect", pgbouncer_container],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                if pgb_result.returncode == 0:
                    pgb_data = json.loads(pgb_result.stdout)
                    if pgb_data and len(pgb_data) > 0:
                        pgb_ip = pgb_data[0]["networks"][0]["address"].split("/")[0]
                        db_url = f"postgresql://{db_user}:{db_password}@" f"{pgb_ip}:{pgbouncer_port}/{db_name}"
                        print(f"🔗 Using PgBouncer at {pgb_ip}:{pgbouncer_port} " f"for {db_name}")
                        return db_url
            except (
                subprocess.TimeoutExpired,
                json.JSONDecodeError,
                KeyError,
                IndexError,
            ):
                pass

            # Direct connection to PostgreSQL is disabled to enforce PgBouncer usage.

    except subprocess.TimeoutExpired:
        pass

    # Fallback to localhost with pgbouncer port, ensuring all connections go through it.
    fallback_url = f"postgresql://{db_user}:{db_password}@localhost:{pgbouncer_port}/{db_name}"
    print(f"⚠️ Using fallback PgBouncer connection: localhost:{pgbouncer_port}/{db_name}")
    return fallback_url


def get_dynamic_redis_config() -> dict[str, Any]:
    """
    Get Redis configuration with dynamic container IP resolution
    Returns dict with host, port, password, db
    """
    # Check if we have environment override first
    env_redis_url = os.getenv("NINAIVALAIGAL_REDIS_URL") or os.getenv("REDIS_URL")
    if env_redis_url:
        # Parse redis://[:password@]host:port/db format
        import re

        match = re.match(r"redis://(?::(.+)@)?([^:]+):(\d+)/(\d+)", env_redis_url)
        if match:
            password, host, port, db = match.groups()
            return {
                "host": host,
                "port": int(port),
                "password": password or "secure_nina_password",
                "db": int(db),
            }

    # Get environment and runtime for dynamic discovery
    nina_env = os.getenv("NINA_ENV", "dev")
    redis_password = os.getenv("REDIS_PASSWORD", "secure_nina_password")
    redis_db = int(os.getenv("REDIS_DB", "0"))
    redis_port = 6379  # Redis standard port

    # Try to get dynamic container IP
    try:
        import subprocess

        # First try Apple Container CLI
        container_cmd = "container"
        if subprocess.run(["which", "container"], capture_output=True).returncode != 0:  # nosec B607
            # Fallback to Docker if container CLI not available
            container_cmd = "docker"

        # Try to get Redis container IP
        redis_container = f"ninaivalaigal-{nina_env}-redis"
        try:
            redis_result = subprocess.run(
                [container_cmd, "inspect", redis_container],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if redis_result.returncode == 0:
                redis_data = json.loads(redis_result.stdout)
                if redis_data and len(redis_data) > 0:
                    redis_ip = redis_data[0]["networks"][0]["address"].split("/")[0]
                    print(f"🔗 Using Redis at {redis_ip}:{redis_port} for {nina_env}")
                    return {
                        "host": redis_ip,
                        "port": redis_port,
                        "password": redis_password,
                        "db": redis_db,
                    }
        except (subprocess.TimeoutExpired, json.JSONDecodeError, KeyError, IndexError):
            pass

    except subprocess.TimeoutExpired:
        pass

    # Fallback to localhost
    print(f"⚠️ Using fallback Redis connection: localhost:{redis_port}")
    return {
        "host": "localhost",
        "port": redis_port,
        "password": redis_password,
        "db": redis_db,
    }


def get_database_url() -> str:
    """Get database URL from configuration (legacy compatibility)"""
    return get_dynamic_database_url()
