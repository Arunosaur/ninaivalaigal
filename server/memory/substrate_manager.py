"""
SPEC-012: Memory Substrate Manager
Complete memory provider architecture with health monitoring and management
"""

import asyncio
import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Protocol

from .factory import get_memory_provider
from .interfaces import (
    MemoryProvider,
    MemoryProviderConnectionError,
    MemoryProviderError,
)

logger = logging.getLogger(__name__)


class ProviderStatus(Enum):
    """Memory provider status enumeration"""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class ProviderHealth:
    """Memory provider health information"""

    status: ProviderStatus
    response_time_ms: float
    last_check: datetime
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class SubstrateMetrics:
    """Memory substrate performance metrics"""

    total_memories: int
    active_providers: int
    average_response_time_ms: float
    error_rate: float
    uptime_percentage: float
    last_updated: datetime


class MemorySubstrateManager:
    """
    SPEC-012: Memory Substrate Manager

    Manages multiple memory providers with health monitoring,
    failover capabilities, and performance metrics.
    """

    def __init__(self):
        self.providers: Dict[str, MemoryProvider] = {}
        self.health_status: Dict[str, ProviderHealth] = {}
        self.primary_provider: Optional[str] = None
        self.fallback_providers: List[str] = []
        self._monitoring_task: Optional[asyncio.Task] = None
        self._metrics: Optional[SubstrateMetrics] = None

    async def initialize(self, config: Optional[Dict[str, Any]] = None) -> None:
        """Initialize memory substrate with configuration"""
        try:
            config = config or {}

            # Initialize primary provider
            primary_config = config.get("primary", {"type": "native"})
            primary_provider = get_memory_provider(
                provider_type=primary_config.get("type", "native"),
                **primary_config.get("options", {}),
            )

            self.providers["primary"] = primary_provider
            self.primary_provider = "primary"

            # Initialize fallback providers if configured
            fallback_configs = config.get("fallbacks", [])
            for i, fallback_config in enumerate(fallback_configs):
                provider_name = f"fallback_{i}"
                fallback_provider = get_memory_provider(
                    provider_type=fallback_config.get("type"),
                    **fallback_config.get("options", {}),
                )
                self.providers[provider_name] = fallback_provider
                self.fallback_providers.append(provider_name)

            # Start health monitoring
            await self._start_health_monitoring()

            logger.info(
                f"Memory substrate initialized with {len(self.providers)} providers"
            )

        except Exception as e:
            logger.error(f"Failed to initialize memory substrate: {e}")
            raise MemoryProviderError(f"Substrate initialization failed: {e}")

    async def remember(
        self,
        text: str,
        meta: Optional[Dict[str, Any]] = None,
        user_id: Optional[int] = None,
        context_id: Optional[str] = None,
        retry_fallbacks: bool = True,
    ) -> Dict[str, Any]:
        """Store memory with automatic failover"""
        providers_to_try = [self.primary_provider] if self.primary_provider else []
        if retry_fallbacks:
            providers_to_try.extend(self.fallback_providers)

        last_error = None

        for provider_name in providers_to_try:
            if provider_name not in self.providers:
                continue

            provider = self.providers[provider_name]

            try:
                start_time = datetime.now(timezone.utc)
                result = await provider.remember(
                    text=text, meta=meta, user_id=user_id, context_id=context_id
                )

                # Update health metrics
                response_time = (
                    datetime.now(timezone.utc) - start_time
                ).total_seconds() * 1000
                await self._update_provider_health(provider_name, True, response_time)

                # Add substrate metadata
                result_dict = dict(result)
                result_dict["substrate_metadata"] = {
                    "provider": provider_name,
                    "response_time_ms": response_time,
                    "timestamp": start_time.isoformat(),
                }

                return result_dict

            except Exception as e:
                last_error = e
                await self._update_provider_health(provider_name, False, error=str(e))
                logger.warning(
                    f"Provider {provider_name} failed for remember operation: {e}"
                )
                continue

        # All providers failed
        raise MemoryProviderError(
            f"All memory providers failed. Last error: {last_error}"
        )

    async def recall(
        self,
        query: str,
        k: int = 5,
        user_id: Optional[int] = None,
        context_id: Optional[str] = None,
        retry_fallbacks: bool = True,
    ) -> List[Dict[str, Any]]:
        """Recall memories with automatic failover"""
        providers_to_try = [self.primary_provider] if self.primary_provider else []
        if retry_fallbacks:
            providers_to_try.extend(self.fallback_providers)

        last_error = None

        for provider_name in providers_to_try:
            if provider_name not in self.providers:
                continue

            provider = self.providers[provider_name]

            try:
                start_time = datetime.now(timezone.utc)
                results = await provider.recall(
                    query=query, k=k, user_id=user_id, context_id=context_id
                )

                # Update health metrics
                response_time = (
                    datetime.now(timezone.utc) - start_time
                ).total_seconds() * 1000
                await self._update_provider_health(provider_name, True, response_time)

                # Add substrate metadata to each result
                enhanced_results = []
                for result in results:
                    result_dict = dict(result)
                    result_dict["substrate_metadata"] = {
                        "provider": provider_name,
                        "response_time_ms": response_time,
                        "timestamp": start_time.isoformat(),
                    }
                    enhanced_results.append(result_dict)

                return enhanced_results

            except Exception as e:
                last_error = e
                await self._update_provider_health(provider_name, False, error=str(e))
                logger.warning(
                    f"Provider {provider_name} failed for recall operation: {e}"
                )
                continue

        # All providers failed
        raise MemoryProviderError(
            f"All memory providers failed. Last error: {last_error}"
        )

    async def delete(
        self,
        memory_id: str,
        user_id: Optional[int] = None,
        retry_fallbacks: bool = True,
    ) -> bool:
        """Delete memory with automatic failover"""
        providers_to_try = [self.primary_provider] if self.primary_provider else []
        if retry_fallbacks:
            providers_to_try.extend(self.fallback_providers)

        success_count = 0
        last_error = None

        for provider_name in providers_to_try:
            if provider_name not in self.providers:
                continue

            provider = self.providers[provider_name]

            try:
                start_time = datetime.now(timezone.utc)
                success = await provider.delete(id=memory_id, user_id=user_id)

                # Update health metrics
                response_time = (
                    datetime.now(timezone.utc) - start_time
                ).total_seconds() * 1000
                await self._update_provider_health(provider_name, True, response_time)

                if success:
                    success_count += 1

            except Exception as e:
                last_error = e
                await self._update_provider_health(provider_name, False, error=str(e))
                logger.warning(
                    f"Provider {provider_name} failed for delete operation: {e}"
                )
                continue

        if success_count == 0 and last_error:
            raise MemoryProviderError(
                f"All delete operations failed. Last error: {last_error}"
            )

        return success_count > 0

    async def list_memories(
        self,
        user_id: Optional[int] = None,
        context_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
        retry_fallbacks: bool = True,
    ) -> List[Dict[str, Any]]:
        """List memories with automatic failover"""
        providers_to_try = [self.primary_provider] if self.primary_provider else []
        if retry_fallbacks:
            providers_to_try.extend(self.fallback_providers)

        last_error = None

        for provider_name in providers_to_try:
            if provider_name not in self.providers:
                continue

            provider = self.providers[provider_name]

            try:
                start_time = datetime.now(timezone.utc)
                results = await provider.list_memories(
                    user_id=user_id, context_id=context_id, limit=limit, offset=offset
                )

                # Update health metrics
                response_time = (
                    datetime.now(timezone.utc) - start_time
                ).total_seconds() * 1000
                await self._update_provider_health(provider_name, True, response_time)

                # Add substrate metadata
                enhanced_results = []
                for result in results:
                    result_dict = dict(result)
                    result_dict["substrate_metadata"] = {
                        "provider": provider_name,
                        "response_time_ms": response_time,
                        "timestamp": start_time.isoformat(),
                    }
                    enhanced_results.append(result_dict)

                return enhanced_results

            except Exception as e:
                last_error = e
                await self._update_provider_health(provider_name, False, error=str(e))
                logger.warning(
                    f"Provider {provider_name} failed for list operation: {e}"
                )
                continue

        # All providers failed
        raise MemoryProviderError(
            f"All memory providers failed. Last error: {last_error}"
        )

    async def get_health_status(self) -> Dict[str, ProviderHealth]:
        """Get health status of all providers"""
        # Trigger immediate health check for all providers
        await self._check_all_providers_health()
        return self.health_status.copy()

    async def get_substrate_metrics(self) -> SubstrateMetrics:
        """Get substrate performance metrics"""
        if not self._metrics:
            await self._calculate_metrics()
        return self._metrics

    async def get_provider_info(self) -> Dict[str, Any]:
        """Get information about configured providers"""
        return {
            "primary_provider": self.primary_provider,
            "fallback_providers": self.fallback_providers,
            "total_providers": len(self.providers),
            "health_status": {
                name: status.status.value for name, status in self.health_status.items()
            },
        }

    async def switch_primary_provider(self, provider_name: str) -> bool:
        """Switch primary provider (admin operation)"""
        if provider_name not in self.providers:
            raise ValueError(f"Provider {provider_name} not found")

        # Check if provider is healthy
        health = self.health_status.get(provider_name)
        if health and health.status == ProviderStatus.UNHEALTHY:
            raise ValueError(f"Cannot switch to unhealthy provider {provider_name}")

        old_primary = self.primary_provider
        self.primary_provider = provider_name

        # Move old primary to fallbacks if it wasn't already there
        if old_primary and old_primary not in self.fallback_providers:
            self.fallback_providers.append(old_primary)

        # Remove new primary from fallbacks
        if provider_name in self.fallback_providers:
            self.fallback_providers.remove(provider_name)

        logger.info(f"Switched primary provider from {old_primary} to {provider_name}")
        return True

    async def shutdown(self) -> None:
        """Shutdown substrate manager"""
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass

        logger.info("Memory substrate manager shutdown complete")

    # Private methods
    async def _start_health_monitoring(self) -> None:
        """Start background health monitoring task"""
        if self._monitoring_task:
            return

        self._monitoring_task = asyncio.create_task(self._health_monitoring_loop())

    async def _health_monitoring_loop(self) -> None:
        """Background health monitoring loop"""
        while True:
            try:
                await self._check_all_providers_health()
                await self._calculate_metrics()
                await asyncio.sleep(30)  # Check every 30 seconds
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health monitoring error: {e}")
                await asyncio.sleep(60)  # Wait longer on error

    async def _check_all_providers_health(self) -> None:
        """Check health of all providers"""
        tasks = []
        for provider_name in self.providers:
            task = asyncio.create_task(self._check_provider_health(provider_name))
            tasks.append(task)

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def _check_provider_health(self, provider_name: str) -> None:
        """Check health of a specific provider"""
        if provider_name not in self.providers:
            return

        provider = self.providers[provider_name]
        start_time = datetime.now(timezone.utc)

        try:
            # Use provider's health_check method if available
            if hasattr(provider, "health_check"):
                is_healthy = await provider.health_check()
            else:
                # Fallback: try a simple operation
                await provider.list_memories(limit=1)
                is_healthy = True

            response_time = (
                datetime.now(timezone.utc) - start_time
            ).total_seconds() * 1000

            status = ProviderStatus.HEALTHY if is_healthy else ProviderStatus.DEGRADED
            self.health_status[provider_name] = ProviderHealth(
                status=status,
                response_time_ms=response_time,
                last_check=datetime.now(timezone.utc),
            )

        except Exception as e:
            response_time = (
                datetime.now(timezone.utc) - start_time
            ).total_seconds() * 1000
            self.health_status[provider_name] = ProviderHealth(
                status=ProviderStatus.UNHEALTHY,
                response_time_ms=response_time,
                last_check=datetime.now(timezone.utc),
                error_message=str(e),
            )

    async def _update_provider_health(
        self,
        provider_name: str,
        success: bool,
        response_time: Optional[float] = None,
        error: Optional[str] = None,
    ) -> None:
        """Update provider health based on operation result"""
        if success:
            status = ProviderStatus.HEALTHY
        else:
            status = ProviderStatus.UNHEALTHY

        self.health_status[provider_name] = ProviderHealth(
            status=status,
            response_time_ms=response_time or 0.0,
            last_check=datetime.now(timezone.utc),
            error_message=error,
        )

    async def _calculate_metrics(self) -> None:
        """Calculate substrate performance metrics"""
        try:
            healthy_providers = sum(
                1
                for health in self.health_status.values()
                if health.status == ProviderStatus.HEALTHY
            )

            total_providers = len(self.providers)

            avg_response_time = 0.0
            if self.health_status:
                avg_response_time = sum(
                    health.response_time_ms for health in self.health_status.values()
                ) / len(self.health_status)

            error_rate = 0.0
            if total_providers > 0:
                unhealthy_providers = sum(
                    1
                    for health in self.health_status.values()
                    if health.status == ProviderStatus.UNHEALTHY
                )
                error_rate = (unhealthy_providers / total_providers) * 100

            uptime_percentage = (
                (healthy_providers / total_providers * 100)
                if total_providers > 0
                else 0.0
            )

            self._metrics = SubstrateMetrics(
                total_memories=0,  # TODO: Implement total memory count
                active_providers=healthy_providers,
                average_response_time_ms=avg_response_time,
                error_rate=error_rate,
                uptime_percentage=uptime_percentage,
                last_updated=datetime.now(timezone.utc),
            )

        except Exception as e:
            logger.error(f"Failed to calculate metrics: {e}")


# Global substrate manager instance
_substrate_manager: Optional[MemorySubstrateManager] = None


async def get_substrate_manager() -> MemorySubstrateManager:
    """Get the global substrate manager instance"""
    global _substrate_manager
    if _substrate_manager is None:
        _substrate_manager = MemorySubstrateManager()
        await _substrate_manager.initialize()
    return _substrate_manager


async def reset_substrate_manager() -> None:
    """Reset the global substrate manager (useful for testing)"""
    global _substrate_manager
    if _substrate_manager:
        await _substrate_manager.shutdown()
    _substrate_manager = None
