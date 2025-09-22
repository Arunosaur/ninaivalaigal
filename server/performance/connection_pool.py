"""
Database Connection Pool Optimization
Provides enhanced connection pooling with monitoring and health checks
"""

import time
from typing import Dict, Optional

import structlog
from sqlalchemy import create_engine, event, pool
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool

logger = structlog.get_logger(__name__)


class ConnectionPoolMonitor:
    """Monitor and optimize database connection pool performance."""

    def __init__(self):
        self.stats = {
            "connections_created": 0,
            "connections_closed": 0,
            "connections_checked_out": 0,
            "connections_checked_in": 0,
            "connection_errors": 0,
            "pool_overflows": 0,
            "pool_timeouts": 0,
        }
        self.start_time = time.time()

    def get_pool_stats(self, engine: Engine) -> Dict:
        """Get comprehensive connection pool statistics."""
        pool_obj = engine.pool

        stats = {
            "pool_size": pool_obj.size(),
            "checked_out_connections": pool_obj.checkedout(),
            "overflow_connections": pool_obj.overflow(),
            "checked_in_connections": pool_obj.checkedin(),
            "runtime_seconds": time.time() - self.start_time,
            **self.stats,
        }

        # Calculate rates
        runtime = stats["runtime_seconds"]
        if runtime > 0:
            stats["connections_per_second"] = stats["connections_created"] / runtime
            stats["error_rate"] = stats["connection_errors"] / max(
                1, stats["connections_created"]
            )

        return stats

    def log_pool_status(self, engine: Engine, level: str = "info"):
        """Log current pool status."""
        stats = self.get_pool_stats(engine)

        log_func = getattr(logger, level)
        log_func("Database connection pool status", **stats)


class OptimizedDatabaseManager:
    """Enhanced database manager with optimized connection pooling."""

    def __init__(
        self,
        database_url: str,
        pool_size: int = 20,
        max_overflow: int = 30,
        pool_timeout: int = 30,
        pool_recycle: int = 3600,  # 1 hour
        pool_pre_ping: bool = True,
    ):
        self.database_url = database_url
        self.monitor = ConnectionPoolMonitor()

        # Create optimized engine with connection pooling
        self.engine = create_engine(
            database_url,
            poolclass=QueuePool,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_timeout=pool_timeout,
            pool_recycle=pool_recycle,
            pool_pre_ping=pool_pre_ping,
            # Connection optimization
            connect_args={
                "connect_timeout": 10,
                "application_name": "ninaivalaigal_api",
            },
            # Logging for debugging
            echo=False,  # Set to True for SQL debugging
        )

        # Set up event listeners for monitoring
        self._setup_event_listeners()

        # Create session factory
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine,
            expire_on_commit=False,  # Optimize for caching
        )

        logger.info(
            "Database connection pool initialized",
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_timeout=pool_timeout,
            pool_recycle=pool_recycle,
        )

    def _setup_event_listeners(self):
        """Set up SQLAlchemy event listeners for monitoring."""

        @event.listens_for(self.engine, "connect")
        def on_connect(dbapi_connection, connection_record):
            self.monitor.stats["connections_created"] += 1
            logger.debug("Database connection created")

        @event.listens_for(self.engine, "close")
        def on_close(dbapi_connection, connection_record):
            self.monitor.stats["connections_closed"] += 1
            logger.debug("Database connection closed")

        @event.listens_for(self.engine, "checkout")
        def on_checkout(dbapi_connection, connection_record, connection_proxy):
            self.monitor.stats["connections_checked_out"] += 1
            logger.debug("Database connection checked out")

        @event.listens_for(self.engine, "checkin")
        def on_checkin(dbapi_connection, connection_record):
            self.monitor.stats["connections_checked_in"] += 1
            logger.debug("Database connection checked in")

        @event.listens_for(pool.Pool, "connect")
        def on_pool_connect(dbapi_connection, connection_record):
            # Set connection-level optimizations
            if hasattr(dbapi_connection, "autocommit"):
                dbapi_connection.autocommit = False

    def get_session(self):
        """Get a database session with automatic cleanup."""
        return self.SessionLocal()

    def get_pool_stats(self) -> Dict:
        """Get connection pool statistics."""
        return self.monitor.get_pool_stats(self.engine)

    def health_check(self) -> Dict:
        """Perform database and connection pool health check."""
        try:
            start_time = time.time()

            # Test basic connectivity
            with self.engine.connect() as conn:
                result = conn.execute("SELECT 1").scalar()

            connection_time = time.time() - start_time
            pool_stats = self.get_pool_stats()

            # Determine health status
            health_status = "healthy"
            issues = []

            # Check for potential issues
            if pool_stats["error_rate"] > 0.1:  # More than 10% error rate
                issues.append("High connection error rate")
                health_status = "degraded"

            if pool_stats["checked_out_connections"] > pool_stats["pool_size"] * 0.8:
                issues.append("High connection pool utilization")
                health_status = "degraded"

            if connection_time > 1.0:  # More than 1 second
                issues.append("Slow connection establishment")
                health_status = "degraded"

            return {
                "status": health_status,
                "connection_time_ms": round(connection_time * 1000, 2),
                "pool_stats": pool_stats,
                "issues": issues,
                "test_result": result,
            }

        except Exception as e:
            self.monitor.stats["connection_errors"] += 1
            logger.error("Database health check failed", error=str(e))

            return {
                "status": "unhealthy",
                "error": str(e),
                "pool_stats": self.get_pool_stats(),
            }

    def optimize_pool_size(self) -> Dict:
        """Analyze usage patterns and suggest pool size optimizations."""
        stats = self.get_pool_stats()

        recommendations = []
        current_pool_size = stats["pool_size"]
        avg_checked_out = stats["checked_out_connections"]

        # Analyze utilization patterns
        utilization_rate = avg_checked_out / max(1, current_pool_size)

        if utilization_rate > 0.8:
            recommendations.append(
                {
                    "type": "increase_pool_size",
                    "current": current_pool_size,
                    "suggested": current_pool_size + 10,
                    "reason": f"High utilization rate: {utilization_rate:.2%}",
                }
            )
        elif utilization_rate < 0.3 and current_pool_size > 10:
            recommendations.append(
                {
                    "type": "decrease_pool_size",
                    "current": current_pool_size,
                    "suggested": max(10, current_pool_size - 5),
                    "reason": f"Low utilization rate: {utilization_rate:.2%}",
                }
            )

        # Check for overflow usage
        if stats["overflow_connections"] > 0:
            recommendations.append(
                {
                    "type": "increase_max_overflow",
                    "current": "unknown",
                    "suggested": stats["overflow_connections"] + 10,
                    "reason": "Pool overflow detected",
                }
            )

        # Check error rates
        if stats["error_rate"] > 0.05:
            recommendations.append(
                {
                    "type": "investigate_errors",
                    "reason": f"High error rate: {stats['error_rate']:.2%}",
                }
            )

        return {
            "current_stats": stats,
            "utilization_rate": utilization_rate,
            "recommendations": recommendations,
            "analysis_time": time.time(),
        }

    def close(self):
        """Close the database connection pool."""
        if hasattr(self, "engine"):
            self.engine.dispose()
            logger.info("Database connection pool closed")


# Global instance for application use
_optimized_db_manager: Optional[OptimizedDatabaseManager] = None


def get_optimized_db_manager(
    database_url: Optional[str] = None,
) -> OptimizedDatabaseManager:
    """Get or create the optimized database manager instance."""
    global _optimized_db_manager

    if _optimized_db_manager is None and database_url:
        _optimized_db_manager = OptimizedDatabaseManager(database_url)

    if _optimized_db_manager is None:
        raise RuntimeError("Database manager not initialized. Provide database_url.")

    return _optimized_db_manager


def close_optimized_db_manager():
    """Close the optimized database manager."""
    global _optimized_db_manager

    if _optimized_db_manager:
        _optimized_db_manager.close()
        _optimized_db_manager = None
