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
from typing import Any


def _build_default_database_url() -> str:
    """Build database URL from environment variables."""
    host = os.getenv("PGBOUNCER_HOST") or os.getenv("POSTGRES_HOST", "localhost")
    user = os.getenv("NINA_DB_USER") or os.getenv("POSTGRES_USER", "nina")
    password = os.getenv("NINA_DB_PASSWORD") or os.getenv("POSTGRES_PASSWORD", "dev_password_change_in_production")
    db_name = os.getenv("NINA_DB_NAME") or os.getenv("POSTGRES_DB", "ninaivalaigal_dev")

    # Try PgBouncer port first, then direct PostgreSQL
    port = os.getenv("PGBOUNCER_PORT") or os.getenv("PGBOUNCER_TX_PORT", "6432")

    return f"postgresql://{user}:{password}@{host}:{port}/{db_name}"


def load_config() -> dict[str, Any]:
    """
    Load configuration from file and environment variables
    Environment variables take precedence over file configuration
    """
    config_path = "../ninaivalaigal.config.json"
    default_db_url = _build_default_database_url()
    default_config = {
        "storage": {
            "type": "postgresql",
            "url": default_db_url,
        },
        "database_url": default_db_url,
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
            session_port = (
                os.getenv("PGBOUNCER_SESS_PORT")
                or os.getenv("PGBOUNCER_SESSION_PORT")
                or os.getenv("PGBOUNCER_PORT_SESSION")
            )
            if not session_port:
                try:
                    session_port = str(int(pgbouncer_port) + 1)
                except ValueError:
                    session_port = "6433"

            pgbouncer_candidates = [
                (f"ninaivalaigal-{nina_env}-pgbouncer-tx", pgbouncer_port),
                (f"ninaivalaigal-{nina_env}-pgbouncer-session", session_port),
                (f"ninaivalaigal-{nina_env}-pgbouncer-sess", session_port),
            ]

            for container_name, candidate_port in pgbouncer_candidates:
                try:
                    pgb_result = subprocess.run(
                        [container_cmd, "inspect", container_name],
                        capture_output=True,
                        text=True,
                        timeout=5,
                    )
                    if pgb_result.returncode == 0:
                        pgb_data = json.loads(pgb_result.stdout)
                        if pgb_data and len(pgb_data) > 0:
                            network_info = pgb_data[0]["networks"]
                            if network_info:
                                pgb_ip = network_info[0]["address"].split("/")[0]
                                db_url = (
                                    f"postgresql://{db_user}:{db_password}@"
                                    f"{pgb_ip}:{candidate_port}/{db_name}"
                                )
                                print(
                                    f"🔗 Using PgBouncer ({container_name}) at {pgb_ip}:{candidate_port} "
                                    f"for {db_name}"
                                )
                                return db_url
                except (
                    subprocess.TimeoutExpired,
                    json.JSONDecodeError,
                    KeyError,
                    IndexError,
                ):
                    continue

            # Fallback to direct PostgreSQL connection
            postgres_container = f"ninaivalaigal-{nina_env}-db"
            try:
                pg_result = subprocess.run(
                    [container_cmd, "inspect", postgres_container],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                if pg_result.returncode == 0:
                    pg_data = json.loads(pg_result.stdout)
                    if pg_data and len(pg_data) > 0:
                        pg_ip = pg_data[0]["networks"][0]["address"].split("/")[0]
                        db_url = f"postgresql://{db_user}:{db_password}@" f"{pg_ip}:{postgres_port}/{db_name}"
                        print(f"🔗 Using PostgreSQL at {pg_ip}:{postgres_port} " f"for {db_name}")
                        return db_url
            except (
                subprocess.TimeoutExpired,
                json.JSONDecodeError,
                KeyError,
                IndexError,
            ):
                pass

    except subprocess.TimeoutExpired:
        pass

    # Fallback to localhost with calculated ports and proper naming
    fallback_url = f"postgresql://{db_user}:{db_password}@localhost:{postgres_port}/{db_name}"
    print(f"⚠️ Using fallback connection: localhost:{postgres_port}/{db_name}")
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
