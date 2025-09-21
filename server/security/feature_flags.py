"""
Feature Flag System for Security Controls

Provides runtime configuration for security features with safe defaults
and audit logging for all flag changes.
"""

import json
import logging
import os
import time
from dataclasses import asdict, dataclass
from threading import Lock
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class FeatureFlag:
    """Individual feature flag configuration."""

    name: str
    enabled: bool
    description: str
    created_at: float
    updated_at: float
    updated_by: str = "system"


class FeatureFlagManager:
    """Manages security feature flags with audit logging."""

    def __init__(self, config_file: str | None = None):
        self.config_file = config_file or os.getenv(
            "FEATURE_FLAGS_CONFIG", "/etc/ninaivalaigal/feature-flags.json"
        )
        self.flags: dict[str, FeatureFlag] = {}
        self.lock = Lock()

        # Initialize default flags
        self._initialize_default_flags()

        # Load from config file if exists
        self._load_from_file()

    def _initialize_default_flags(self):
        """Initialize default security feature flags."""
        default_flags = [
            (
                "archive_checks_enabled",
                True,
                "Enable archive blocking on text endpoints",
            ),
            (
                "magic_byte_detection_enabled",
                True,
                "Enable magic byte detection for binaries",
            ),
            ("unicode_normalization_enabled", True, "Enable Unicode normalization"),
            (
                "compression_ratio_checks_enabled",
                True,
                "Enable compression ratio checks",
            ),
            ("filename_security_enabled", True, "Enable filename security validation"),
            ("multipart_size_limits_enabled", True, "Enable multipart size limits"),
            ("rbac_enforcement_enabled", True, "Enable RBAC permission enforcement"),
            ("log_scrubbing_enabled", True, "Enable sensitive data log scrubbing"),
            (
                "idempotency_checks_enabled",
                True,
                "Enable idempotency replay protection",
            ),
            (
                "fail_closed_policy_enabled",
                True,
                "Enable fail-closed security policies",
            ),
        ]

        current_time = time.time()
        for name, enabled, description in default_flags:
            self.flags[name] = FeatureFlag(
                name=name,
                enabled=enabled,
                description=description,
                created_at=current_time,
                updated_at=current_time,
                updated_by="system_init",
            )

    def _load_from_file(self):
        """Load feature flags from configuration file."""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file) as f:
                    config_data = json.load(f)

                for name, flag_data in config_data.get("flags", {}).items():
                    if name in self.flags:
                        # Update existing flag
                        self.flags[name].enabled = flag_data.get(
                            "enabled", self.flags[name].enabled
                        )
                        self.flags[name].updated_at = flag_data.get(
                            "updated_at", time.time()
                        )
                        self.flags[name].updated_by = flag_data.get(
                            "updated_by", "config_file"
                        )

                logger.info(f"Loaded feature flags from {self.config_file}")

        except Exception as e:
            logger.error(f"Failed to load feature flags from {self.config_file}: {e}")

    def _save_to_file(self):
        """Save current feature flags to configuration file."""
        try:
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)

            config_data = {
                "flags": {name: asdict(flag) for name, flag in self.flags.items()},
                "last_updated": time.time(),
            }

            with open(self.config_file, "w") as f:
                json.dump(config_data, f, indent=2)

            logger.info(f"Saved feature flags to {self.config_file}")

        except Exception as e:
            logger.error(f"Failed to save feature flags to {self.config_file}: {e}")

    def is_enabled(self, flag_name: str) -> bool:
        """Check if a feature flag is enabled."""
        with self.lock:
            flag = self.flags.get(flag_name)
            if flag is None:
                logger.warning(
                    f"Unknown feature flag: {flag_name}, defaulting to False"
                )
                return False
            return flag.enabled

    def set_flag(self, flag_name: str, enabled: bool, updated_by: str = "api") -> bool:
        """Set a feature flag value with audit logging."""
        with self.lock:
            if flag_name not in self.flags:
                logger.error(f"Cannot set unknown feature flag: {flag_name}")
                return False

            old_value = self.flags[flag_name].enabled
            self.flags[flag_name].enabled = enabled
            self.flags[flag_name].updated_at = time.time()
            self.flags[flag_name].updated_by = updated_by

            # Audit log
            logger.warning(
                f"Feature flag changed: {flag_name} {old_value} → {enabled} "
                f"by {updated_by} at {time.time()}"
            )

            # Save to file
            self._save_to_file()

            return True

    def get_all_flags(self) -> dict[str, dict[str, Any]]:
        """Get all feature flags with metadata."""
        with self.lock:
            return {name: asdict(flag) for name, flag in self.flags.items()}

    def get_flag_status(self, flag_name: str) -> dict[str, Any] | None:
        """Get detailed status of a specific flag."""
        with self.lock:
            flag = self.flags.get(flag_name)
            return asdict(flag) if flag else None

    def bulk_update(
        self, updates: dict[str, bool], updated_by: str = "bulk_api"
    ) -> dict[str, bool]:
        """Update multiple flags in a single operation."""
        results = {}

        with self.lock:
            for flag_name, enabled in updates.items():
                if flag_name in self.flags:
                    old_value = self.flags[flag_name].enabled
                    self.flags[flag_name].enabled = enabled
                    self.flags[flag_name].updated_at = time.time()
                    self.flags[flag_name].updated_by = updated_by

                    logger.warning(
                        f"Bulk flag change: {flag_name} {old_value} → {enabled} "
                        f"by {updated_by}"
                    )
                    results[flag_name] = True
                else:
                    logger.error(f"Unknown flag in bulk update: {flag_name}")
                    results[flag_name] = False

            # Save to file
            self._save_to_file()

        return results


# Global feature flag manager
_flag_manager = FeatureFlagManager()


# Convenience functions
def is_enabled(flag_name: str) -> bool:
    """Check if a feature flag is enabled."""
    return _flag_manager.is_enabled(flag_name)


def set_flag(flag_name: str, enabled: bool, updated_by: str = "api") -> bool:
    """Set a feature flag value."""
    return _flag_manager.set_flag(flag_name, enabled, updated_by)


def get_all_flags() -> dict[str, dict[str, Any]]:
    """Get all feature flags."""
    return _flag_manager.get_all_flags()


def get_flag_status(flag_name: str) -> dict[str, Any] | None:
    """Get status of a specific flag."""
    return _flag_manager.get_flag_status(flag_name)


# Security-specific flag checks
def archive_checks_enabled() -> bool:
    """Check if archive blocking is enabled."""
    return is_enabled("archive_checks_enabled")


def magic_byte_detection_enabled() -> bool:
    """Check if magic byte detection is enabled."""
    return is_enabled("magic_byte_detection_enabled")


def unicode_normalization_enabled() -> bool:
    """Check if Unicode normalization is enabled."""
    return is_enabled("unicode_normalization_enabled")


def compression_ratio_checks_enabled() -> bool:
    """Check if compression ratio checks are enabled."""
    return is_enabled("compression_ratio_checks_enabled")


def filename_security_enabled() -> bool:
    """Check if filename security validation is enabled."""
    return is_enabled("filename_security_enabled")


def rbac_enforcement_enabled() -> bool:
    """Check if RBAC enforcement is enabled."""
    return is_enabled("rbac_enforcement_enabled")


def fail_closed_policy_enabled() -> bool:
    """Check if fail-closed policies are enabled."""
    return is_enabled("fail_closed_policy_enabled")


# Emergency rollback function
def emergency_rollback(updated_by: str = "emergency") -> dict[str, bool]:
    """Emergency rollback - disable all non-critical security features."""
    rollback_flags = {
        "archive_checks_enabled": False,
        "magic_byte_detection_enabled": False,
        "compression_ratio_checks_enabled": False,
        "filename_security_enabled": False,
        # Keep these enabled for basic security
        # "unicode_normalization_enabled": True,
        # "rbac_enforcement_enabled": True,
        # "log_scrubbing_enabled": True,
    }

    logger.critical(f"EMERGENCY ROLLBACK initiated by {updated_by}")
    return _flag_manager.bulk_update(rollback_flags, f"emergency_rollback_{updated_by}")


# Health check integration
def get_feature_flag_health() -> dict[str, Any]:
    """Get feature flag health status for /healthz/config endpoint."""
    flags = get_all_flags()

    # Count enabled/disabled flags
    enabled_count = sum(1 for flag in flags.values() if flag["enabled"])
    total_count = len(flags)

    # Check for recent changes (last 5 minutes)
    recent_changes = []
    current_time = time.time()
    for name, flag in flags.items():
        if current_time - flag["updated_at"] < 300:  # 5 minutes
            recent_changes.append(
                {
                    "flag": name,
                    "enabled": flag["enabled"],
                    "updated_by": flag["updated_by"],
                    "updated_at": flag["updated_at"],
                }
            )

    return {
        "total_flags": total_count,
        "enabled_flags": enabled_count,
        "disabled_flags": total_count - enabled_count,
        "recent_changes": recent_changes,
        "critical_flags_status": {
            "archive_checks": is_enabled("archive_checks_enabled"),
            "rbac_enforcement": is_enabled("rbac_enforcement_enabled"),
            "fail_closed_policy": is_enabled("fail_closed_policy_enabled"),
        },
    }
