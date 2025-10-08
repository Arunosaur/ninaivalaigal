"""
Configuration Management Module
Extracted from main.py for better code organization
"""

import json
import os
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
            "url": "postgresql://mem0user:mem0pass@localhost:5432/mem0db",  # pragma: allowlist secret  # noqa: E501
        },
        "database_url": "postgresql://mem0user:mem0pass@localhost:5432/mem0db",  # pragma: allowlist secret  # noqa: E501
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


def get_database_url() -> str:
    """Get database URL from configuration (legacy compatibility)"""
    return get_dynamic_database_url()
