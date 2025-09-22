"""
Real-time Performance Monitoring Dashboard
Provides comprehensive visualization of system performance metrics
"""

import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import structlog
from fastapi import APIRouter, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from ..performance import get_performance_manager

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/dashboard", tags=["monitoring"])
templates = Jinja2Templates(directory="server/monitoring/templates")


class DashboardManager:
    """Manages real-time dashboard connections and data streaming."""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.metrics_history: List[Dict[str, Any]] = []
        self.max_history_size = 1000  # Keep last 1000 data points
        self.update_interval = 5  # Update every 5 seconds
        self.is_running = False
        self.background_task: Optional[asyncio.Task] = None
    
    async def connect(self, websocket: WebSocket):
        """Accept new WebSocket connection."""
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info("Dashboard client connected", total_connections=len(self.active_connections))
        
        # Start background task if not running
        if not self.is_running:
            await self.start_background_updates()
    
    def disconnect(self, websocket: WebSocket):
        """Remove WebSocket connection."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info("Dashboard client disconnected", total_connections=len(self.active_connections))
        
        # Stop background task if no connections
        if not self.active_connections and self.is_running:
            self.stop_background_updates()
    
    async def start_background_updates(self):
        """Start background task for metrics collection."""
        if self.background_task is None or self.background_task.done():
            self.is_running = True
            self.background_task = asyncio.create_task(self._background_metrics_collector())
            logger.info("Dashboard background updates started")
    
    def stop_background_updates(self):
        """Stop background task."""
        self.is_running = False
        if self.background_task and not self.background_task.done():
            self.background_task.cancel()
        logger.info("Dashboard background updates stopped")
    
    async def _background_metrics_collector(self):
        """Background task to collect and broadcast metrics."""
        while self.is_running and self.active_connections:
            try:
                # Collect metrics from performance manager
                metrics = await self._collect_current_metrics()
                
                # Add timestamp
                metrics["timestamp"] = datetime.now().isoformat()
                
                # Store in history
                self.metrics_history.append(metrics)
                if len(self.metrics_history) > self.max_history_size:
                    self.metrics_history.pop(0)
                
                # Broadcast to all connected clients
                await self._broadcast_metrics(metrics)
                
                # Wait for next update
                await asyncio.sleep(self.update_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Error in background metrics collector", error=str(e))
                await asyncio.sleep(self.update_interval)
    
    async def _collect_current_metrics(self) -> Dict[str, Any]:
        """Collect current system metrics."""
        try:
            performance_manager = get_performance_manager()
            
            # Get comprehensive stats
            stats = await performance_manager.get_comprehensive_stats()
            
            # Extract key metrics for dashboard
            dashboard_metrics = {
                "system": {
                    "timestamp": time.time(),
                    "uptime": stats.get("overall", {}).get("uptime_seconds", 0),
                },
                "api": {
                    "total_requests": stats.get("overall", {}).get("total_requests", 0),
                    "avg_response_time_ms": stats.get("overall", {}).get("avg_response_time_ms", 0),
                    "requests_per_second": stats.get("overall", {}).get("requests_per_second", 0),
                },
                "database": {
                    "pool_size": stats.get("database", {}).get("pool_size", 0),
                    "checked_out_connections": stats.get("database", {}).get("checked_out_connections", 0),
                    "connections_per_second": stats.get("database", {}).get("connections_per_second", 0),
                    "error_rate": stats.get("database", {}).get("error_rate", 0),
                },
                "redis": {
                    "connected_clients": stats.get("redis", {}).get("connected_clients", 0),
                    "used_memory_human": stats.get("redis", {}).get("used_memory_human", "0B"),
                    "cache_hit_rate": stats.get("redis", {}).get("cache_hit_rate", 0),
                    "ops_per_second": stats.get("redis", {}).get("instantaneous_ops_per_sec", 0),
                },
                "cache": {
                    "query_cache_keys": stats.get("query_cache", {}).get("total_keys", 0),
                    "response_cache_keys": stats.get("response_cache", {}).get("total_keys", 0),
                },
                "graph": {
                    "queries_executed": stats.get("graph_optimizer", {}).get("query_metrics", {}).get("graph_queries_executed", 0),
                    "avg_query_time_ms": stats.get("graph_optimizer", {}).get("query_metrics", {}).get("avg_query_time_ms", 0),
                    "cache_hit_rate": stats.get("graph_optimizer", {}).get("cache_performance", {}).get("hit_rate", 0),
                },
                "health": await self._get_health_status(),
            }
            
            return dashboard_metrics
            
        except Exception as e:
            logger.error("Failed to collect metrics", error=str(e))
            return self._get_fallback_metrics()
    
    async def _get_health_status(self) -> Dict[str, str]:
        """Get overall system health status."""
        try:
            performance_manager = get_performance_manager()
            health = await performance_manager.health_check()
            
            return {
                "overall": health.get("overall_status", "unknown"),
                "database": health.get("components", {}).get("database", {}).get("status", "unknown"),
                "redis": health.get("components", {}).get("redis", {}).get("status", "unknown"),
                "issues": len(health.get("issues", [])),
            }
        except Exception:
            return {
                "overall": "unknown",
                "database": "unknown", 
                "redis": "unknown",
                "issues": 0,
            }
    
    def _get_fallback_metrics(self) -> Dict[str, Any]:
        """Return fallback metrics when collection fails."""
        return {
            "system": {"timestamp": time.time(), "uptime": 0},
            "api": {"total_requests": 0, "avg_response_time_ms": 0, "requests_per_second": 0},
            "database": {"pool_size": 0, "checked_out_connections": 0, "connections_per_second": 0, "error_rate": 0},
            "redis": {"connected_clients": 0, "used_memory_human": "0B", "cache_hit_rate": 0, "ops_per_second": 0},
            "cache": {"query_cache_keys": 0, "response_cache_keys": 0},
            "graph": {"queries_executed": 0, "avg_query_time_ms": 0, "cache_hit_rate": 0},
            "health": {"overall": "unknown", "database": "unknown", "redis": "unknown", "issues": 0},
        }
    
    async def _broadcast_metrics(self, metrics: Dict[str, Any]):
        """Broadcast metrics to all connected clients."""
        if not self.active_connections:
            return
        
        message = json.dumps({
            "type": "metrics_update",
            "data": metrics
        })
        
        # Send to all connections, remove dead ones
        dead_connections = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.warning("Failed to send to client", error=str(e))
                dead_connections.append(connection)
        
        # Clean up dead connections
        for connection in dead_connections:
            self.disconnect(connection)
    
    def get_metrics_history(self, minutes: int = 60) -> List[Dict[str, Any]]:
        """Get metrics history for specified time period."""
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        
        return [
            metric for metric in self.metrics_history
            if datetime.fromisoformat(metric["timestamp"]) > cutoff_time
        ]


# Global dashboard manager
dashboard_manager = DashboardManager()


@router.get("/", response_class=HTMLResponse)
async def dashboard_home(request: Request):
    """Serve the main dashboard page."""
    return templates.TemplateResponse("dashboard.html", {"request": request})


@router.get("/api/metrics/current")
async def get_current_metrics():
    """Get current system metrics."""
    metrics = await dashboard_manager._collect_current_metrics()
    return {
        "status": "success",
        "data": metrics,
        "timestamp": datetime.now().isoformat(),
    }


@router.get("/api/metrics/history")
async def get_metrics_history(minutes: int = 60):
    """Get metrics history for specified time period."""
    history = dashboard_manager.get_metrics_history(minutes)
    return {
        "status": "success",
        "data": history,
        "count": len(history),
        "time_range_minutes": minutes,
    }


@router.get("/api/alerts")
async def get_active_alerts():
    """Get active system alerts based on thresholds."""
    try:
        performance_manager = get_performance_manager()
        stats = await performance_manager.get_comprehensive_stats()
        
        alerts = []
        
        # Check API response time
        avg_response_time = stats.get("overall", {}).get("avg_response_time_ms", 0)
        if avg_response_time > 200:
            alerts.append({
                "severity": "warning" if avg_response_time < 500 else "critical",
                "component": "api",
                "message": f"High average response time: {avg_response_time:.1f}ms",
                "threshold": 200,
                "current_value": avg_response_time,
            })
        
        # Check database error rate
        db_error_rate = stats.get("database", {}).get("error_rate", 0)
        if db_error_rate > 0.05:  # 5% error rate
            alerts.append({
                "severity": "critical",
                "component": "database",
                "message": f"High database error rate: {db_error_rate:.2%}",
                "threshold": 0.05,
                "current_value": db_error_rate,
            })
        
        # Check cache hit rate
        cache_hit_rate = stats.get("redis", {}).get("cache_hit_rate", 0)
        if cache_hit_rate < 0.7:  # Less than 70% hit rate
            alerts.append({
                "severity": "warning",
                "component": "cache",
                "message": f"Low cache hit rate: {cache_hit_rate:.2%}",
                "threshold": 0.7,
                "current_value": cache_hit_rate,
            })
        
        return {
            "status": "success",
            "data": alerts,
            "count": len(alerts),
        }
        
    except Exception as e:
        logger.error("Failed to get alerts", error=str(e))
        return {
            "status": "error",
            "message": str(e),
            "data": [],
        }


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time metrics streaming."""
    await dashboard_manager.connect(websocket)
    
    try:
        while True:
            # Keep connection alive and handle client messages
            message = await websocket.receive_text()
            data = json.loads(message)
            
            # Handle client requests
            if data.get("type") == "get_history":
                minutes = data.get("minutes", 60)
                history = dashboard_manager.get_metrics_history(minutes)
                await websocket.send_text(json.dumps({
                    "type": "history_data",
                    "data": history
                }))
            
    except WebSocketDisconnect:
        dashboard_manager.disconnect(websocket)
    except Exception as e:
        logger.error("WebSocket error", error=str(e))
        dashboard_manager.disconnect(websocket)


# Cleanup function for application shutdown
async def cleanup_dashboard():
    """Clean up dashboard resources."""
    dashboard_manager.stop_background_updates()
    dashboard_manager.active_connections.clear()
    logger.info("Dashboard cleanup completed")
