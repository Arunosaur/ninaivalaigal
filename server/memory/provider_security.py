"""
SPEC-020: Memory Provider Security Manager
Secure provider registration with RBAC and API key support
"""

import asyncio
import base64
import hashlib
import hmac
import json
import logging
import secrets
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Set

from ..auth_utils import get_current_user
from ..database.operations.rbac_ops import RBACOps
from .provider_registry import ProviderConfig, ProviderType

logger = logging.getLogger(__name__)


class SecurityLevel(Enum):
    """Security levels for provider access"""

    PUBLIC = "public"  # No authentication required
    API_KEY = "api_key"  # API key authentication  # pragma: allowlist secret
    RBAC = "rbac"  # Role-based access control
    MUTUAL_TLS = "mutual_tls"  # Mutual TLS authentication
    HYBRID = "hybrid"  # Multiple authentication methods


class ProviderPermission(Enum):
    """Provider-specific permissions"""

    REGISTER = "provider:register"
    CONFIGURE = "provider:configure"
    ACTIVATE = "provider:activate"
    DEACTIVATE = "provider:deactivate"
    DELETE = "provider:delete"
    VIEW_METRICS = "provider:view_metrics"
    MANAGE_KEYS = "provider:manage_keys"
    ADMIN = "provider:admin"


@dataclass
class APIKey:
    """API key for provider authentication"""

    key_id: str
    key_hash: str
    provider_name: str
    permissions: Set[ProviderPermission]
    created_by: int
    created_at: datetime
    expires_at: Optional[datetime] = None
    last_used: Optional[datetime] = None
    usage_count: int = 0
    is_active: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SecurityPolicy:
    """Security policy for provider operations"""

    provider_name: str
    security_level: SecurityLevel
    required_permissions: Set[ProviderPermission]
    allowed_users: Set[int] = field(default_factory=set)
    allowed_roles: Set[str] = field(default_factory=set)
    ip_whitelist: Set[str] = field(default_factory=set)
    rate_limits: Dict[str, int] = field(default_factory=dict)
    audit_enabled: bool = True


@dataclass
class SecurityAuditLog:
    """Security audit log entry"""

    timestamp: datetime
    provider_name: str
    operation: str
    user_id: Optional[int]
    api_key_id: Optional[str]
    source_ip: Optional[str]
    success: bool
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class MemoryProviderSecurityManager:
    """
    SPEC-020: Memory Provider Security Manager

    Manages secure provider registration, authentication, authorization,
    and audit logging with RBAC integration and API key management.
    """

    def __init__(self, rbac_ops: Optional[RBACOps] = None):
        self.rbac_ops = rbac_ops
        self.api_keys: Dict[str, APIKey] = {}
        self.security_policies: Dict[str, SecurityPolicy] = {}
        self.audit_logs: List[SecurityAuditLog] = []
        self.max_audit_logs = 10000

        # Security configuration
        self.key_expiry_days = 365
        self.max_keys_per_provider = 10
        self.audit_retention_days = 90

        # Initialize default policies
        self._initialize_default_policies()

    async def register_provider_securely(
        self,
        config: ProviderConfig,
        user_id: int,
        security_level: SecurityLevel = SecurityLevel.RBAC,
        source_ip: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Securely register a new memory provider with authentication

        Args:
            config: Provider configuration
            user_id: User performing the registration
            security_level: Required security level
            source_ip: Source IP address for audit

        Returns:
            Registration result with security information
        """
        try:
            # Check permissions
            if not await self._check_provider_permission(
                user_id, ProviderPermission.REGISTER, config.name, source_ip
            ):
                await self._audit_log(
                    config.name,
                    "register",
                    user_id,
                    None,
                    source_ip,
                    False,
                    "Insufficient permissions for provider registration",
                )
                raise PermissionError("Insufficient permissions to register provider")

            # Validate security level
            if not await self._validate_security_level(
                config.name, security_level, user_id
            ):
                await self._audit_log(
                    config.name,
                    "register",
                    user_id,
                    None,
                    source_ip,
                    False,
                    "Invalid security level for provider",
                )
                raise ValueError("Invalid security level for provider")

            # Create security policy
            policy = SecurityPolicy(
                provider_name=config.name,
                security_level=security_level,
                required_permissions={ProviderPermission.REGISTER},
                allowed_users={user_id},
                audit_enabled=True,
            )

            # Generate API key if required
            api_key_info = None
            if security_level in [SecurityLevel.API_KEY, SecurityLevel.HYBRID]:
                api_key_info = await self._generate_api_key(
                    config.name, user_id, {ProviderPermission.CONFIGURE}
                )

            # Store security policy
            self.security_policies[config.name] = policy

            # Audit successful registration
            await self._audit_log(
                config.name,
                "register",
                user_id,
                api_key_info["key_id"] if api_key_info else None,
                source_ip,
                True,
                "Provider registered successfully",
            )

            result = {
                "provider_name": config.name,
                "security_level": security_level.value,
                "registration_successful": True,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }

            if api_key_info:
                result["api_key"] = api_key_info

            logger.info(
                f"Securely registered provider {config.name} for user {user_id}"
            )
            return result

        except Exception as e:
            await self._audit_log(
                config.name, "register", user_id, None, source_ip, False, str(e)
            )
            logger.error(f"Failed to register provider {config.name}: {e}")
            raise

    async def authenticate_provider_access(
        self,
        provider_name: str,
        operation: str,
        user_id: Optional[int] = None,
        api_key: Optional[str] = None,
        source_ip: Optional[str] = None,
    ) -> bool:
        """
        Authenticate access to a provider operation

        Args:
            provider_name: Name of the provider
            operation: Operation being performed
            user_id: User ID (for RBAC authentication)
            api_key: API key (for API key authentication)
            source_ip: Source IP address

        Returns:
            True if authentication successful, False otherwise
        """
        try:
            policy = self.security_policies.get(provider_name)
            if not policy:
                # No policy means public access (for backward compatibility)
                return True

            # Check IP whitelist
            if policy.ip_whitelist and source_ip:
                if source_ip not in policy.ip_whitelist:
                    await self._audit_log(
                        provider_name,
                        operation,
                        user_id,
                        None,
                        source_ip,
                        False,
                        "IP address not in whitelist",
                    )
                    return False

            # Authenticate based on security level
            if policy.security_level == SecurityLevel.PUBLIC:
                return True

            elif policy.security_level == SecurityLevel.API_KEY:
                if not api_key:
                    await self._audit_log(
                        provider_name,
                        operation,
                        user_id,
                        None,
                        source_ip,
                        False,
                        "API key required but not provided",
                    )
                    return False

                return await self._validate_api_key(api_key, provider_name, operation)

            elif policy.security_level == SecurityLevel.RBAC:
                if not user_id:
                    await self._audit_log(
                        provider_name,
                        operation,
                        None,
                        None,
                        source_ip,
                        False,
                        "User authentication required but not provided",
                    )
                    return False

                # Map operation to permission
                permission = self._map_operation_to_permission(operation)
                return await self._check_provider_permission(
                    user_id, permission, provider_name, source_ip
                )

            elif policy.security_level == SecurityLevel.HYBRID:
                # Require both API key and RBAC
                if not api_key or not user_id:
                    await self._audit_log(
                        provider_name,
                        operation,
                        user_id,
                        None,
                        source_ip,
                        False,
                        "Both API key and user authentication required",
                    )
                    return False

                api_key_valid = await self._validate_api_key(
                    api_key, provider_name, operation
                )
                permission = self._map_operation_to_permission(operation)
                rbac_valid = await self._check_provider_permission(
                    user_id, permission, provider_name, source_ip
                )

                return api_key_valid and rbac_valid

            else:
                await self._audit_log(
                    provider_name,
                    operation,
                    user_id,
                    None,
                    source_ip,
                    False,
                    f"Unsupported security level: {policy.security_level}",
                )
                return False

        except Exception as e:
            logger.error(f"Authentication error for provider {provider_name}: {e}")
            await self._audit_log(
                provider_name, operation, user_id, None, source_ip, False, str(e)
            )
            return False

    async def generate_provider_api_key(
        self,
        provider_name: str,
        user_id: int,
        permissions: Set[ProviderPermission],
        expires_days: Optional[int] = None,
        source_ip: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Generate a new API key for a provider"""
        try:
            # Check permissions
            if not await self._check_provider_permission(
                user_id, ProviderPermission.MANAGE_KEYS, provider_name, source_ip
            ):
                raise PermissionError("Insufficient permissions to manage API keys")

            # Check key limits
            existing_keys = [
                k
                for k in self.api_keys.values()
                if k.provider_name == provider_name and k.is_active
            ]

            if len(existing_keys) >= self.max_keys_per_provider:
                raise ValueError(
                    f"Maximum number of API keys ({self.max_keys_per_provider}) reached for provider"
                )

            # Generate API key
            api_key_info = await self._generate_api_key(
                provider_name, user_id, permissions, expires_days
            )

            await self._audit_log(
                provider_name,
                "generate_api_key",
                user_id,
                api_key_info["key_id"],
                source_ip,
                True,
                "API key generated successfully",
            )

            return api_key_info

        except Exception as e:
            await self._audit_log(
                provider_name,
                "generate_api_key",
                user_id,
                None,
                source_ip,
                False,
                str(e),
            )
            raise

    async def revoke_provider_api_key(
        self, key_id: str, user_id: int, source_ip: Optional[str] = None
    ) -> bool:
        """Revoke an API key"""
        try:
            api_key = self.api_keys.get(key_id)
            if not api_key:
                return False

            # Check permissions
            if not await self._check_provider_permission(
                user_id,
                ProviderPermission.MANAGE_KEYS,
                api_key.provider_name,
                source_ip,
            ):
                raise PermissionError("Insufficient permissions to revoke API key")

            # Revoke key
            api_key.is_active = False

            await self._audit_log(
                api_key.provider_name,
                "revoke_api_key",
                user_id,
                key_id,
                source_ip,
                True,
                "API key revoked successfully",
            )

            return True

        except Exception as e:
            await self._audit_log(
                "unknown", "revoke_api_key", user_id, key_id, source_ip, False, str(e)
            )
            raise

    async def list_provider_api_keys(
        self, provider_name: str, user_id: int, source_ip: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """List API keys for a provider"""
        try:
            # Check permissions
            if not await self._check_provider_permission(
                user_id, ProviderPermission.VIEW_METRICS, provider_name, source_ip
            ):
                raise PermissionError("Insufficient permissions to view API keys")

            keys = []
            for api_key in self.api_keys.values():
                if api_key.provider_name == provider_name:
                    keys.append(
                        {
                            "key_id": api_key.key_id,
                            "permissions": [p.value for p in api_key.permissions],
                            "created_at": api_key.created_at.isoformat(),
                            "expires_at": (
                                api_key.expires_at.isoformat()
                                if api_key.expires_at
                                else None
                            ),
                            "last_used": (
                                api_key.last_used.isoformat()
                                if api_key.last_used
                                else None
                            ),
                            "usage_count": api_key.usage_count,
                            "is_active": api_key.is_active,
                        }
                    )

            return keys

        except Exception as e:
            await self._audit_log(
                provider_name, "list_api_keys", user_id, None, source_ip, False, str(e)
            )
            raise

    async def get_security_audit_logs(
        self,
        provider_name: Optional[str] = None,
        user_id: Optional[int] = None,
        hours: int = 24,
        admin_user_id: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Get security audit logs"""
        try:
            # Check admin permissions
            if admin_user_id and not await self._check_provider_permission(
                admin_user_id, ProviderPermission.ADMIN, provider_name or "system"
            ):
                raise PermissionError("Admin permissions required to view audit logs")

            # Filter logs
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
            filtered_logs = []

            for log in self.audit_logs:
                if log.timestamp < cutoff_time:
                    continue

                if provider_name and log.provider_name != provider_name:
                    continue

                if user_id and log.user_id != user_id:
                    continue

                filtered_logs.append(
                    {
                        "timestamp": log.timestamp.isoformat(),
                        "provider_name": log.provider_name,
                        "operation": log.operation,
                        "user_id": log.user_id,
                        "api_key_id": log.api_key_id,
                        "source_ip": log.source_ip,
                        "success": log.success,
                        "error_message": log.error_message,
                        "metadata": log.metadata,
                    }
                )

            return sorted(filtered_logs, key=lambda x: x["timestamp"], reverse=True)

        except Exception as e:
            logger.error(f"Failed to get audit logs: {e}")
            return []

    async def update_security_policy(
        self,
        provider_name: str,
        policy_updates: Dict[str, Any],
        user_id: int,
        source_ip: Optional[str] = None,
    ) -> bool:
        """Update security policy for a provider"""
        try:
            # Check permissions
            if not await self._check_provider_permission(
                user_id, ProviderPermission.ADMIN, provider_name, source_ip
            ):
                raise PermissionError(
                    "Admin permissions required to update security policy"
                )

            policy = self.security_policies.get(provider_name)
            if not policy:
                raise ValueError(
                    f"No security policy found for provider {provider_name}"
                )

            # Update policy fields
            if "security_level" in policy_updates:
                policy.security_level = SecurityLevel(policy_updates["security_level"])

            if "ip_whitelist" in policy_updates:
                policy.ip_whitelist = set(policy_updates["ip_whitelist"])

            if "rate_limits" in policy_updates:
                policy.rate_limits.update(policy_updates["rate_limits"])

            if "audit_enabled" in policy_updates:
                policy.audit_enabled = policy_updates["audit_enabled"]

            await self._audit_log(
                provider_name,
                "update_security_policy",
                user_id,
                None,
                source_ip,
                True,
                "Security policy updated successfully",
            )

            return True

        except Exception as e:
            await self._audit_log(
                provider_name,
                "update_security_policy",
                user_id,
                None,
                source_ip,
                False,
                str(e),
            )
            raise

    # Private methods
    async def _generate_api_key(
        self,
        provider_name: str,
        user_id: int,
        permissions: Set[ProviderPermission],
        expires_days: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Generate a new API key"""
        try:
            # Generate key components
            key_id = secrets.token_urlsafe(16)
            raw_key = secrets.token_urlsafe(32)

            # Create key hash for storage
            key_hash = hashlib.sha256(raw_key.encode()).hexdigest()

            # Set expiration
            expires_at = None
            if expires_days:
                expires_at = datetime.now(timezone.utc) + timedelta(days=expires_days)
            elif self.key_expiry_days:
                expires_at = datetime.now(timezone.utc) + timedelta(
                    days=self.key_expiry_days
                )

            # Create API key object
            api_key = APIKey(
                key_id=key_id,
                key_hash=key_hash,
                provider_name=provider_name,
                permissions=permissions,
                created_by=user_id,
                created_at=datetime.now(timezone.utc),
                expires_at=expires_at,
            )

            # Store API key
            self.api_keys[key_id] = api_key

            # Return key information (including raw key - only time it's exposed)
            return {
                "key_id": key_id,
                "api_key": f"{key_id}.{raw_key}",  # Format: key_id.raw_key
                "permissions": [p.value for p in permissions],
                "created_at": api_key.created_at.isoformat(),
                "expires_at": expires_at.isoformat() if expires_at else None,
            }

        except Exception as e:
            logger.error(f"Failed to generate API key: {e}")
            raise

    async def _validate_api_key(
        self, api_key_string: str, provider_name: str, operation: str
    ) -> bool:
        """Validate an API key"""
        try:
            # Parse API key format: key_id.raw_key
            if "." not in api_key_string:
                return False

            key_id, raw_key = api_key_string.split(".", 1)

            # Get stored API key
            api_key = self.api_keys.get(key_id)
            if not api_key:
                return False

            # Check if key is active
            if not api_key.is_active:
                return False

            # Check expiration
            if api_key.expires_at and datetime.now(timezone.utc) > api_key.expires_at:
                api_key.is_active = False
                return False

            # Check provider match
            if api_key.provider_name != provider_name:
                return False

            # Validate key hash
            key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
            if not hmac.compare_digest(api_key.key_hash, key_hash):
                return False

            # Check permissions
            required_permission = self._map_operation_to_permission(operation)
            if required_permission not in api_key.permissions:
                return False

            # Update usage statistics
            api_key.last_used = datetime.now(timezone.utc)
            api_key.usage_count += 1

            return True

        except Exception as e:
            logger.error(f"API key validation error: {e}")
            return False

    async def _check_provider_permission(
        self,
        user_id: int,
        permission: ProviderPermission,
        provider_name: str,
        source_ip: Optional[str] = None,
    ) -> bool:
        """Check if user has provider permission"""
        try:
            # Check security policy
            policy = self.security_policies.get(provider_name)
            if policy:
                # Check allowed users
                if policy.allowed_users and user_id not in policy.allowed_users:
                    return False

                # Check required permissions
                if permission not in policy.required_permissions:
                    # Permission not required by policy
                    return True

            # Use RBAC if available
            if self.rbac_ops:
                return await self.rbac_ops.check_permission(user_id, permission.value)

            # Default: allow if no RBAC system
            return True

        except Exception as e:
            logger.error(f"Permission check error: {e}")
            return False

    async def _validate_security_level(
        self, provider_name: str, security_level: SecurityLevel, user_id: int
    ) -> bool:
        """Validate if user can set the requested security level"""
        try:
            # Admin users can set any security level
            if self.rbac_ops and await self.rbac_ops.check_permission(
                user_id, ProviderPermission.ADMIN.value
            ):
                return True

            # Regular users can only set basic security levels
            allowed_levels = {
                SecurityLevel.PUBLIC,
                SecurityLevel.API_KEY,
                SecurityLevel.RBAC,
            }
            return security_level in allowed_levels

        except Exception as e:
            logger.error(f"Security level validation error: {e}")
            return False

    def _map_operation_to_permission(self, operation: str) -> ProviderPermission:
        """Map operation string to provider permission"""
        operation_mapping = {
            "register": ProviderPermission.REGISTER,
            "configure": ProviderPermission.CONFIGURE,
            "activate": ProviderPermission.ACTIVATE,
            "deactivate": ProviderPermission.DEACTIVATE,
            "delete": ProviderPermission.DELETE,
            "view_metrics": ProviderPermission.VIEW_METRICS,
            "manage_keys": ProviderPermission.MANAGE_KEYS,
            "remember": ProviderPermission.CONFIGURE,
            "recall": ProviderPermission.CONFIGURE,
            "list": ProviderPermission.VIEW_METRICS,
            "health_check": ProviderPermission.VIEW_METRICS,
        }

        return operation_mapping.get(operation, ProviderPermission.CONFIGURE)

    async def _audit_log(
        self,
        provider_name: str,
        operation: str,
        user_id: Optional[int],
        api_key_id: Optional[str],
        source_ip: Optional[str],
        success: bool,
        error_message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Add entry to security audit log"""
        try:
            log_entry = SecurityAuditLog(
                timestamp=datetime.now(timezone.utc),
                provider_name=provider_name,
                operation=operation,
                user_id=user_id,
                api_key_id=api_key_id,
                source_ip=source_ip,
                success=success,
                error_message=error_message,
                metadata=metadata or {},
            )

            self.audit_logs.append(log_entry)

            # Maintain log size limit
            if len(self.audit_logs) > self.max_audit_logs:
                self.audit_logs = self.audit_logs[-self.max_audit_logs :]

            # Log to system logger for external monitoring
            log_level = logging.INFO if success else logging.WARNING
            logger.log(
                log_level,
                f"Provider security audit: {operation} on {provider_name} by user {user_id} "
                f"from {source_ip} - {'SUCCESS' if success else 'FAILED'}",
            )

        except Exception as e:
            logger.error(f"Failed to write audit log: {e}")

    def _initialize_default_policies(self) -> None:
        """Initialize default security policies"""
        try:
            # Default policy for system operations
            default_policy = SecurityPolicy(
                provider_name="system",
                security_level=SecurityLevel.RBAC,
                required_permissions={
                    ProviderPermission.REGISTER,
                    ProviderPermission.CONFIGURE,
                    ProviderPermission.ADMIN,
                },
                audit_enabled=True,
            )

            self.security_policies["system"] = default_policy

        except Exception as e:
            logger.error(f"Failed to initialize default policies: {e}")


# Global security manager instance
_security_manager: Optional[MemoryProviderSecurityManager] = None


async def get_security_manager() -> MemoryProviderSecurityManager:
    """Get the global security manager instance"""
    global _security_manager
    if _security_manager is None:
        # Initialize with RBAC if available
        try:
            from ..database import get_db_pool
            from ..database.operations.rbac_ops import RBACOps

            pool = await get_db_pool()
            rbac_ops = RBACOps(pool)
            _security_manager = MemoryProviderSecurityManager(rbac_ops)
        except Exception:
            # Fallback without RBAC
            _security_manager = MemoryProviderSecurityManager()

    return _security_manager


async def reset_security_manager() -> None:
    """Reset the global security manager (useful for testing)"""
    global _security_manager
    _security_manager = None
