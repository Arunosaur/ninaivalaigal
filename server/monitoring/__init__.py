"""
Real-time Performance Monitoring Dashboard Package
Provides comprehensive visualization and monitoring of system performance
"""

from .dashboard import DashboardManager, cleanup_dashboard, router

__all__ = ["DashboardManager", "cleanup_dashboard", "router"]
