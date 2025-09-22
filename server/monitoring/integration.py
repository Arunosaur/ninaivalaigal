"""
Monitoring Integration Module
Integrates dashboard with FastAPI application and performance systems
"""

import asyncio
from typing import Optional

import structlog
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from ..performance import get_performance_manager, initialize_performance_optimizations
from .dashboard import cleanup_dashboard, router as dashboard_router

logger = structlog.get_logger(__name__)


class MonitoringIntegration:
    """
    Comprehensive monitoring integration for ninaivalaigal platform.
    
    Integrates:
    - Real-time performance dashboard
    - WebSocket streaming for live metrics
    - Performance optimization suite
    - Alert management system
    """
    
    def __init__(self):
        self.initialized = False
        self.dashboard_enabled = False
    
    async def initialize(
        self,
        app: FastAPI,
        database_url: str,
        redis_client=None,
        graph_reasoner=None,
        enable_dashboard: bool = True,
    ):
        """Initialize comprehensive monitoring integration."""
        if self.initialized:
            logger.warning("Monitoring integration already initialized")
            return
        
        try:
            # Initialize performance optimizations first
            performance_manager = await initialize_performance_optimizations(
                app=app,
                database_url=database_url,
                redis_client=redis_client,
                graph_reasoner=graph_reasoner,
            )
            
            # Add dashboard routes if enabled
            if enable_dashboard:
                await self._setup_dashboard(app)
                self.dashboard_enabled = True
            
            # Add monitoring middleware
            await self._setup_monitoring_middleware(app, performance_manager)
            
            # Setup cleanup handlers
            self._setup_cleanup_handlers(app)
            
            self.initialized = True
            
            logger.info(
                "Monitoring integration initialized",
                dashboard_enabled=self.dashboard_enabled,
                features=[
                    "performance_optimization",
                    "real_time_metrics",
                    "dashboard" if enable_dashboard else None,
                    "websocket_streaming",
                    "alert_management",
                ]
            )
            
        except Exception as e:
            logger.error("Monitoring integration initialization failed", error=str(e))
            raise
    
    async def _setup_dashboard(self, app: FastAPI):
        """Setup dashboard routes and static files."""
        try:
            # Include dashboard router
            app.include_router(dashboard_router)
            
            # Add static files for dashboard assets (if needed)
            # app.mount("/static", StaticFiles(directory="server/monitoring/static"), name="static")
            
            logger.info("Dashboard routes configured")
            
        except Exception as e:
            logger.error("Dashboard setup failed", error=str(e))
            raise
    
    async def _setup_monitoring_middleware(self, app: FastAPI, performance_manager):
        """Setup monitoring-specific middleware."""
        try:
            # The performance manager already adds the necessary middleware
            # We can add additional monitoring-specific middleware here if needed
            
            @app.middleware("http")
            async def monitoring_middleware(request, call_next):
                """Additional monitoring middleware for dashboard-specific metrics."""
                # Add any dashboard-specific request tracking here
                response = await call_next(request)
                
                # Could add dashboard-specific metrics collection here
                # For now, the performance middleware handles everything
                
                return response
            
            logger.info("Monitoring middleware configured")
            
        except Exception as e:
            logger.error("Monitoring middleware setup failed", error=str(e))
            raise
    
    def _setup_cleanup_handlers(self, app: FastAPI):
        """Setup cleanup handlers for application shutdown."""
        @app.on_event("shutdown")
        async def shutdown_monitoring():
            """Cleanup monitoring resources on application shutdown."""
            try:
                if self.dashboard_enabled:
                    await cleanup_dashboard()
                
                # Cleanup performance manager
                performance_manager = get_performance_manager()
                if performance_manager.initialized:
                    await performance_manager.cleanup()
                
                logger.info("Monitoring cleanup completed")
                
            except Exception as e:
                logger.error("Monitoring cleanup failed", error=str(e))
    
    async def get_monitoring_status(self) -> dict:
        """Get comprehensive monitoring system status."""
        if not self.initialized:
            return {"error": "Monitoring integration not initialized"}
        
        try:
            performance_manager = get_performance_manager()
            
            # Get performance stats
            perf_stats = await performance_manager.get_comprehensive_stats()
            
            # Get dashboard status
            dashboard_status = {
                "enabled": self.dashboard_enabled,
                "endpoint": "/dashboard" if self.dashboard_enabled else None,
                "websocket_endpoint": "/dashboard/ws" if self.dashboard_enabled else None,
            }
            
            return {
                "monitoring_integration": {
                    "initialized": self.initialized,
                    "dashboard": dashboard_status,
                    "features": [
                        "real_time_metrics",
                        "performance_optimization",
                        "websocket_streaming",
                        "alert_management",
                        "dashboard_visualization" if self.dashboard_enabled else None,
                    ]
                },
                "performance_stats": perf_stats,
                "system_health": await performance_manager.health_check(),
            }
            
        except Exception as e:
            logger.error("Failed to get monitoring status", error=str(e))
            return {"error": str(e)}


# Global monitoring integration instance
_monitoring_integration: Optional[MonitoringIntegration] = None


def get_monitoring_integration() -> MonitoringIntegration:
    """Get the global monitoring integration instance."""
    global _monitoring_integration
    
    if _monitoring_integration is None:
        _monitoring_integration = MonitoringIntegration()
    
    return _monitoring_integration


async def initialize_comprehensive_monitoring(
    app: FastAPI,
    database_url: str,
    redis_client=None,
    graph_reasoner=None,
    enable_dashboard: bool = True,
):
    """
    Initialize comprehensive monitoring for the FastAPI application.
    
    This is the main entry point for setting up all monitoring capabilities:
    - Performance optimization suite
    - Real-time dashboard
    - WebSocket streaming
    - Alert management
    """
    integration = get_monitoring_integration()
    await integration.initialize(
        app=app,
        database_url=database_url,
        redis_client=redis_client,
        graph_reasoner=graph_reasoner,
        enable_dashboard=enable_dashboard,
    )
    return integration


# Utility functions for easy integration

async def add_monitoring_to_app(
    app: FastAPI,
    database_url: str,
    redis_client=None,
    graph_reasoner=None,
    dashboard: bool = True,
):
    """
    Convenient function to add comprehensive monitoring to a FastAPI app.
    
    Usage:
        from server.monitoring.integration import add_monitoring_to_app
        
        app = FastAPI()
        await add_monitoring_to_app(
            app=app,
            database_url="postgresql://...",
            redis_client=redis_client,
            dashboard=True
        )
    """
    return await initialize_comprehensive_monitoring(
        app=app,
        database_url=database_url,
        redis_client=redis_client,
        graph_reasoner=graph_reasoner,
        enable_dashboard=dashboard,
    )


def get_dashboard_url(base_url: str = "http://localhost:8000") -> str:
    """Get the dashboard URL for the application."""
    return f"{base_url}/dashboard"


def get_websocket_url(base_url: str = "ws://localhost:8000") -> str:
    """Get the WebSocket URL for real-time metrics."""
    return f"{base_url}/dashboard/ws"
