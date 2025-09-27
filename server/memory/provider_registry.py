"""
SPEC-020: Memory Provider Registry
Auto-discovery and configuration management for memory providers
"""

import asyncio
import json
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Type, Union

from .interfaces import MemoryProvider, MemoryProviderError
from .providers.mem0_http import Mem0HttpMemoryProvider
from .providers.postgres import PostgresMemoryProvider

logger = logging.getLogger(__name__)


class ProviderType(Enum):
    """Supported memory provider types"""

    POSTGRES = "postgres"
    MEM0_HTTP = "mem0_http"
    REDIS = "redis"
    VECTOR_DB = "vector_db"
    HYBRID = "hybrid"


class ProviderStatus(Enum):
    """Provider registration status"""

    REGISTERED = "registered"
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    UNKNOWN = "unknown"


@dataclass
class ProviderConfig:
    """Memory provider configuration"""

    name: str
    provider_type: ProviderType
    connection_string: str
    priority: int = 100
    enabled: bool = True
    health_check_interval: int = 30
    timeout: int = 30
    retry_attempts: int = 3
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "name": self.name,
            "provider_type": self.provider_type.value,
            "connection_string": self.connection_string,
            "priority": self.priority,
            "enabled": self.enabled,
            "health_check_interval": self.health_check_interval,
            "timeout": self.timeout,
            "retry_attempts": self.retry_attempts,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProviderConfig":
        """Create from dictionary"""
        return cls(
            name=data["name"],
            provider_type=ProviderType(data["provider_type"]),
            connection_string=data["connection_string"],
            priority=data.get("priority", 100),
            enabled=data.get("enabled", True),
            health_check_interval=data.get("health_check_interval", 30),
            timeout=data.get("timeout", 30),
            retry_attempts=data.get("retry_attempts", 3),
            metadata=data.get("metadata", {}),
        )


@dataclass
class RegisteredProvider:
    """Registered provider with runtime information"""

    config: ProviderConfig
    provider_class: Type[MemoryProvider]
    instance: Optional[MemoryProvider] = None
    status: ProviderStatus = ProviderStatus.REGISTERED
    last_health_check: Optional[datetime] = None
    error_message: Optional[str] = None
    metrics: Dict[str, Any] = field(default_factory=dict)


class MemoryProviderRegistry:
    """
    SPEC-020: Memory Provider Registry

    Manages registration, discovery, and lifecycle of memory providers
    with auto-discovery, health monitoring, and failover capabilities.
    """

    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or os.getenv(
            "MEMORY_PROVIDER_CONFIG", "memory_providers.json"
        )
        self.providers: Dict[str, RegisteredProvider] = {}
        self.active_providers: List[str] = []
        self.primary_provider: Optional[str] = None
        self._health_check_task: Optional[asyncio.Task] = None

        # Built-in provider classes
        self._builtin_providers = {
            ProviderType.POSTGRES: PostgresMemoryProvider,
            ProviderType.MEM0_HTTP: Mem0HttpMemoryProvider,
        }

    async def initialize(self) -> None:
        """Initialize the provider registry"""
        try:
            await self._load_configuration()
            await self._auto_discover_providers()
            await self._validate_providers()
            await self._start_health_monitoring()

            logger.info(
                f"Provider registry initialized with {len(self.providers)} providers"
            )

        except Exception as e:
            logger.error(f"Failed to initialize provider registry: {e}")
            raise MemoryProviderError(f"Registry initialization failed: {e}")

    async def register_provider(
        self,
        config: ProviderConfig,
        provider_class: Type[MemoryProvider],
        auto_activate: bool = True,
    ) -> bool:
        """Register a new memory provider"""
        try:
            if config.name in self.providers:
                logger.warning(
                    f"Provider {config.name} already registered, updating..."
                )

            registered_provider = RegisteredProvider(
                config=config,
                provider_class=provider_class,
                status=ProviderStatus.REGISTERED,
            )

            self.providers[config.name] = registered_provider

            if auto_activate and config.enabled:
                await self._activate_provider(config.name)

            await self._save_configuration()
            logger.info(
                f"Registered provider: {config.name} ({config.provider_type.value})"
            )

            return True

        except Exception as e:
            logger.error(f"Failed to register provider {config.name}: {e}")
            return False

    async def get_provider(self, name: str) -> Optional[MemoryProvider]:
        """Get an active provider instance by name"""
        if name not in self.providers:
            return None

        registered = self.providers[name]

        if registered.status != ProviderStatus.ACTIVE:
            return None

        if registered.instance is None:
            await self._activate_provider(name)

        return registered.instance

    async def get_primary_provider(self) -> Optional[MemoryProvider]:
        """Get the primary (highest priority active) provider"""
        if self.primary_provider:
            return await self.get_provider(self.primary_provider)

        # Find highest priority active provider
        active_providers = [
            (name, provider)
            for name, provider in self.providers.items()
            if provider.status == ProviderStatus.ACTIVE
        ]

        if not active_providers:
            return None

        # Sort by priority (lower number = higher priority)
        active_providers.sort(key=lambda x: x[1].config.priority)
        self.primary_provider = active_providers[0][0]

        return await self.get_provider(self.primary_provider)

    async def list_providers(
        self, status_filter: Optional[ProviderStatus] = None
    ) -> List[Dict[str, Any]]:
        """List all registered providers with their status"""
        providers = []

        for name, registered in self.providers.items():
            if status_filter and registered.status != status_filter:
                continue

            provider_info = {
                "name": name,
                "type": registered.config.provider_type.value,
                "status": registered.status.value,
                "priority": registered.config.priority,
                "enabled": registered.config.enabled,
                "last_health_check": (
                    registered.last_health_check.isoformat()
                    if registered.last_health_check
                    else None
                ),
                "error_message": registered.error_message,
                "metrics": registered.metrics,
            }
            providers.append(provider_info)

        return providers

    async def health_check_provider(self, name: str) -> bool:
        """Perform health check on a specific provider"""
        if name not in self.providers:
            return False

        registered = self.providers[name]

        try:
            if registered.instance is None:
                return False

            # Use provider's health_check method if available
            if hasattr(registered.instance, "health_check"):
                is_healthy = await registered.instance.health_check()
            else:
                # Fallback: try a simple operation
                await registered.instance.list_memories(limit=1)
                is_healthy = True

            registered.last_health_check = datetime.now(timezone.utc)

            if is_healthy:
                if registered.status == ProviderStatus.ERROR:
                    registered.status = ProviderStatus.ACTIVE
                    registered.error_message = None
                    logger.info(f"Provider {name} recovered from error state")
            else:
                registered.status = ProviderStatus.ERROR
                registered.error_message = "Health check failed"
                logger.warning(f"Provider {name} health check failed")

            return is_healthy

        except Exception as e:
            registered.status = ProviderStatus.ERROR
            registered.error_message = str(e)
            registered.last_health_check = datetime.now(timezone.utc)
            logger.error(f"Health check failed for provider {name}: {e}")
            return False

    async def failover_to_backup(self, failed_provider: str) -> Optional[str]:
        """Failover to backup provider when primary fails"""
        try:
            # Mark failed provider as inactive
            if failed_provider in self.providers:
                self.providers[failed_provider].status = ProviderStatus.INACTIVE
                logger.warning(
                    f"Provider {failed_provider} marked as inactive due to failure"
                )

            # Find next available provider by priority
            available_providers = [
                (name, provider)
                for name, provider in self.providers.items()
                if provider.status == ProviderStatus.ACTIVE and name != failed_provider
            ]

            if not available_providers:
                logger.error("No backup providers available for failover")
                return None

            # Sort by priority and select the best one
            available_providers.sort(key=lambda x: x[1].config.priority)
            backup_provider = available_providers[0][0]

            # Update primary provider
            self.primary_provider = backup_provider

            logger.info(
                f"Failover completed: switched from {failed_provider} to {backup_provider}"
            )
            return backup_provider

        except Exception as e:
            logger.error(f"Failover failed: {e}")
            return None

    async def get_provider_metrics(self, name: str) -> Dict[str, Any]:
        """Get performance metrics for a provider"""
        if name not in self.providers:
            return {}

        registered = self.providers[name]

        # Basic metrics
        metrics = {
            "name": name,
            "type": registered.config.provider_type.value,
            "status": registered.status.value,
            "uptime": None,
            "last_health_check": (
                registered.last_health_check.isoformat()
                if registered.last_health_check
                else None
            ),
            "error_count": registered.metrics.get("error_count", 0),
            "success_count": registered.metrics.get("success_count", 0),
            "average_response_time": registered.metrics.get("avg_response_time", 0.0),
        }

        # Calculate uptime if we have health check data
        if registered.last_health_check:
            uptime_seconds = (
                datetime.now(timezone.utc) - registered.last_health_check
            ).total_seconds()
            metrics["uptime"] = uptime_seconds

        return metrics

    async def shutdown(self) -> None:
        """Shutdown the provider registry"""
        try:
            # Stop health monitoring
            if self._health_check_task:
                self._health_check_task.cancel()
                try:
                    await self._health_check_task
                except asyncio.CancelledError:
                    pass

            # Shutdown all active providers
            for name, registered in self.providers.items():
                if registered.instance and hasattr(registered.instance, "shutdown"):
                    try:
                        await registered.instance.shutdown()
                    except Exception as e:
                        logger.error(f"Error shutting down provider {name}: {e}")

            logger.info("Provider registry shutdown complete")

        except Exception as e:
            logger.error(f"Error during registry shutdown: {e}")

    # Private methods
    async def _load_configuration(self) -> None:
        """Load provider configuration from file"""
        try:
            config_file = Path(self.config_path)

            if not config_file.exists():
                logger.info(f"Config file {self.config_path} not found, using defaults")
                await self._create_default_configuration()
                return

            with open(config_file, "r") as f:
                config_data = json.load(f)

            for provider_data in config_data.get("providers", []):
                config = ProviderConfig.from_dict(provider_data)

                # Get provider class
                provider_class = self._builtin_providers.get(config.provider_type)
                if provider_class:
                    registered = RegisteredProvider(
                        config=config, provider_class=provider_class
                    )
                    self.providers[config.name] = registered

            logger.info(f"Loaded {len(self.providers)} providers from configuration")

        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            await self._create_default_configuration()

    async def _auto_discover_providers(self) -> None:
        """Auto-discover available providers from environment"""
        try:
            # Auto-discover PostgreSQL provider
            postgres_url = (
                os.getenv("NINAIVALAIGAL_DATABASE_URL")
                or os.getenv("DATABASE_URL")
                or os.getenv("POSTGRES_URL")
            )

            if postgres_url and "postgres_primary" not in self.providers:
                config = ProviderConfig(
                    name="postgres_primary",
                    provider_type=ProviderType.POSTGRES,
                    connection_string=postgres_url,
                    priority=10,  # High priority
                    enabled=True,
                )

                registered = RegisteredProvider(
                    config=config, provider_class=PostgresMemoryProvider
                )
                self.providers["postgres_primary"] = registered
                logger.info("Auto-discovered PostgreSQL provider")

            # Auto-discover mem0 HTTP provider
            mem0_url = os.getenv("MEM0_URL")
            mem0_secret = os.getenv("MEMORY_SHARED_SECRET")

            if mem0_url and "mem0_http" not in self.providers:
                config = ProviderConfig(
                    name="mem0_http",
                    provider_type=ProviderType.MEM0_HTTP,
                    connection_string=mem0_url,
                    priority=20,  # Lower priority than PostgreSQL
                    enabled=bool(mem0_secret),
                    metadata={"auth_secret": mem0_secret},
                )

                registered = RegisteredProvider(
                    config=config, provider_class=Mem0HttpMemoryProvider
                )
                self.providers["mem0_http"] = registered
                logger.info("Auto-discovered mem0 HTTP provider")

        except Exception as e:
            logger.error(f"Auto-discovery failed: {e}")

    async def _validate_providers(self) -> None:
        """Validate all registered providers"""
        for name, registered in self.providers.items():
            try:
                if not registered.config.enabled:
                    registered.status = ProviderStatus.INACTIVE
                    continue

                # Try to create instance
                await self._activate_provider(name)

            except Exception as e:
                registered.status = ProviderStatus.ERROR
                registered.error_message = str(e)
                logger.error(f"Provider validation failed for {name}: {e}")

    async def _activate_provider(self, name: str) -> bool:
        """Activate a provider by creating its instance"""
        if name not in self.providers:
            return False

        registered = self.providers[name]

        try:
            # Create provider instance
            if registered.config.provider_type == ProviderType.POSTGRES:
                instance = PostgresMemoryProvider(registered.config.connection_string)
            elif registered.config.provider_type == ProviderType.MEM0_HTTP:
                instance = Mem0HttpMemoryProvider(
                    base_url=registered.config.connection_string,
                    auth_secret=registered.config.metadata.get("auth_secret", ""),
                )
            else:
                raise ValueError(
                    f"Unsupported provider type: {registered.config.provider_type}"
                )

            registered.instance = instance
            registered.status = ProviderStatus.ACTIVE

            if name not in self.active_providers:
                self.active_providers.append(name)

            logger.info(f"Activated provider: {name}")
            return True

        except Exception as e:
            registered.status = ProviderStatus.ERROR
            registered.error_message = str(e)
            logger.error(f"Failed to activate provider {name}: {e}")
            return False

    async def _start_health_monitoring(self) -> None:
        """Start background health monitoring task"""
        if self._health_check_task:
            return

        self._health_check_task = asyncio.create_task(self._health_monitoring_loop())

    async def _health_monitoring_loop(self) -> None:
        """Background health monitoring loop"""
        while True:
            try:
                for name in list(self.active_providers):
                    await self.health_check_provider(name)

                await asyncio.sleep(30)  # Check every 30 seconds

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health monitoring error: {e}")
                await asyncio.sleep(60)  # Wait longer on error

    async def _save_configuration(self) -> None:
        """Save current configuration to file"""
        try:
            config_data = {
                "providers": [
                    registered.config.to_dict()
                    for registered in self.providers.values()
                ]
            }

            config_file = Path(self.config_path)
            config_file.parent.mkdir(parents=True, exist_ok=True)

            with open(config_file, "w") as f:
                json.dump(config_data, f, indent=2)

        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")

    async def _create_default_configuration(self) -> None:
        """Create default provider configuration"""
        try:
            # Create default PostgreSQL provider if database URL is available
            postgres_url = os.getenv("NINAIVALAIGAL_DATABASE_URL") or os.getenv(
                "DATABASE_URL"
            )

            if postgres_url:
                config = ProviderConfig(
                    name="postgres_default",
                    provider_type=ProviderType.POSTGRES,
                    connection_string=postgres_url,
                    priority=10,
                    enabled=True,
                )

                registered = RegisteredProvider(
                    config=config, provider_class=PostgresMemoryProvider
                )
                self.providers["postgres_default"] = registered

            await self._save_configuration()
            logger.info("Created default provider configuration")

        except Exception as e:
            logger.error(f"Failed to create default configuration: {e}")


# Global registry instance
_provider_registry: Optional[MemoryProviderRegistry] = None


async def get_provider_registry() -> MemoryProviderRegistry:
    """Get the global provider registry instance"""
    global _provider_registry
    if _provider_registry is None:
        _provider_registry = MemoryProviderRegistry()
        await _provider_registry.initialize()
    return _provider_registry


async def reset_provider_registry() -> None:
    """Reset the global provider registry (useful for testing)"""
    global _provider_registry
    if _provider_registry:
        await _provider_registry.shutdown()
    _provider_registry = None
