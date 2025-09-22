"""
Configuration Management Module
Extracted from main.py for better code organization
"""

import json
import os
from typing import Dict, Any


def load_config() -> Dict[str, Any]:
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


def get_database_url() -> str:
    """Get database URL from configuration"""
    config = load_config()
    if isinstance(config, str):
        return config
    return config["database_url"]
