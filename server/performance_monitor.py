#!/usr/bin/env python3
"""
mem0 Performance Monitoring and Metrics Collection
Provides comprehensive performance monitoring for server, database, client, and shell components
"""

import json
import logging
import threading
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from typing import Any

import psutil


@dataclass
class PerformanceMetric:
    """Represents a single performance metric"""
    name: str
    value: Any
    timestamp: datetime
    tags: dict[str, str]
    metric_type: str  # 'gauge', 'counter', 'histogram', 'summary'

@dataclass
class PerformanceSnapshot:
    """Snapshot of system performance at a point in time"""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    disk_usage_percent: float
    network_connections: int
    active_threads: int
    open_files: int

class PerformanceMonitor:
    """Central performance monitoring system for mem0"""

    def __init__(self, retention_hours: int = 24):
        self.metrics: list[PerformanceMetric] = []
        self.snapshots: list[PerformanceSnapshot] = []
        self.retention_hours = retention_hours
        self.is_monitoring = False
        self.monitor_thread: threading.Thread | None = None
        self._lock = threading.Lock()

        # Configure logging
        self.logger = logging.getLogger(__name__)

        # Performance counters
        self.request_count = 0
        self.error_count = 0
        self.db_query_count = 0
        self.db_query_time_total = 0.0
        self.memory_cache_hits = 0
        self.memory_cache_misses = 0

    def start_monitoring(self, interval_seconds: int = 30):
        """Start the performance monitoring system"""
        if self.is_monitoring:
            return

        self.is_monitoring = True
        self.monitor_thread = threading.Thread(
            target=self._monitoring_loop,
            args=(interval_seconds,),
            daemon=True
        )
        self.monitor_thread.start()
        self.logger.info("Performance monitoring started")

    def stop_monitoring(self):
        """Stop the performance monitoring system"""
        self.is_monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        self.logger.info("Performance monitoring stopped")

    def record_metric(self, name: str, value: Any, tags: dict[str, str] = None, metric_type: str = 'gauge'):
        """Record a performance metric"""
        if tags is None:
            tags = {}

        metric = PerformanceMetric(
            name=name,
            value=value,
            timestamp=datetime.now(),
            tags=tags,
            metric_type=metric_type
        )

        with self._lock:
            self.metrics.append(metric)

            # Cleanup old metrics
            cutoff_time = datetime.now() - timedelta(hours=self.retention_hours)
            self.metrics = [m for m in self.metrics if m.timestamp > cutoff_time]

    def record_request(self, endpoint: str, method: str, response_time: float, status_code: int):
        """Record an API request"""
        self.record_metric(
            'http_request_duration',
            response_time,
            {'endpoint': endpoint, 'method': method, 'status': str(status_code)},
            'histogram'
        )
        self.request_count += 1

        if status_code >= 400:
            self.error_count += 1

    def record_db_query(self, query_type: str, execution_time: float, table: str = None):
        """Record a database query"""
        tags = {'query_type': query_type}
        if table:
            tags['table'] = table

        self.record_metric('db_query_duration', execution_time, tags, 'histogram')
        self.db_query_count += 1
        self.db_query_time_total += execution_time

    def record_memory_operation(self, operation: str, hit: bool = None):
        """Record memory/cache operations"""
        if operation == 'cache_access' and hit is not None:
            if hit:
                self.memory_cache_hits += 1
            else:
                self.memory_cache_misses += 1

        self.record_metric(f'memory_{operation}', 1, {}, 'counter')

    def _monitoring_loop(self, interval_seconds: int):
        """Main monitoring loop"""
        while self.is_monitoring:
            try:
                snapshot = self._capture_system_snapshot()
                with self._lock:
                    self.snapshots.append(snapshot)

                    # Keep only recent snapshots
                    cutoff_time = datetime.now() - timedelta(hours=self.retention_hours)
                    self.snapshots = [s for s in self.snapshots if s.timestamp > cutoff_time]

                # Record system metrics
                self.record_metric('cpu_percent', snapshot.cpu_percent)
                self.record_metric('memory_percent', snapshot.memory_percent)
                self.record_metric('memory_used_mb', snapshot.memory_used_mb)
                self.record_metric('disk_usage_percent', snapshot.disk_usage_percent)
                self.record_metric('network_connections', snapshot.network_connections)
                self.record_metric('active_threads', snapshot.active_threads)

                time.sleep(interval_seconds)

            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                time.sleep(interval_seconds)

    def _capture_system_snapshot(self) -> PerformanceSnapshot:
        """Capture current system performance snapshot"""
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)  # Reduced interval
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')

            # Get process-specific metrics with error handling
            try:
                process = psutil.Process()
                connections = len(process.connections())
                threads = process.num_threads()
                open_files = len(process.open_files())
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                connections = 0
                threads = 0
                open_files = 0

            return PerformanceSnapshot(
                timestamp=datetime.utcnow(),
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                memory_used_mb=memory.used / 1024 / 1024,
                disk_usage_percent=disk.percent,
                network_connections=connections,
                active_threads=threads,
                open_files=open_files
            )
        except Exception:
            # Silently return default snapshot to avoid startup issues
            return PerformanceSnapshot(
                timestamp=datetime.utcnow(),
                cpu_percent=0.0,
                memory_percent=0.0,
                memory_used_mb=0.0,
                disk_usage_percent=0.0,
                network_connections=0,
                active_threads=0,
                open_files=0
            )

    def get_metrics_summary(self) -> dict[str, Any]:
        """Get a summary of current performance metrics"""
        with self._lock:
            now = datetime.now()
            last_hour = now - timedelta(hours=1)

            # Calculate averages for last hour
            recent_snapshots = [s for s in self.snapshots if s.timestamp > last_hour]

            summary = {
                'timestamp': now.isoformat(),
                'uptime_seconds': (now - self.snapshots[0].timestamp).total_seconds() if self.snapshots else 0,
                'total_requests': self.request_count,
                'total_errors': self.error_count,
                'error_rate': self.error_count / max(self.request_count, 1),
                'db_queries_total': self.db_query_count,
                'db_avg_query_time': self.db_query_time_total / max(self.db_query_count, 1),
                'memory_cache_hit_rate': self.memory_cache_hits / max(self.memory_cache_hits + self.memory_cache_misses, 1),
                'system_metrics': {}
            }

            if recent_snapshots:
                summary['system_metrics'] = {
                    'avg_cpu_percent': sum(s.cpu_percent for s in recent_snapshots) / len(recent_snapshots),
                    'avg_memory_percent': sum(s.memory_percent for s in recent_snapshots) / len(recent_snapshots),
                    'max_memory_used_mb': max(s.memory_used_mb for s in recent_snapshots),
                    'avg_threads': sum(s.active_threads for s in recent_snapshots) / len(recent_snapshots),
                    'avg_network_connections': sum(s.network_connections for s in recent_snapshots) / len(recent_snapshots)
                }

            return summary

    def get_detailed_metrics(self, metric_name: str = None, hours: int = 1) -> list[dict[str, Any]]:
        """Get detailed metrics for analysis"""
        with self._lock:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            filtered_metrics = [m for m in self.metrics if m.timestamp > cutoff_time]

            if metric_name:
                filtered_metrics = [m for m in filtered_metrics if m.name == metric_name]

            return [asdict(m) for m in filtered_metrics]

    def export_metrics(self, filepath: str):
        """Export metrics to JSON file"""
        data = {
            'summary': self.get_metrics_summary(),
            'detailed_metrics': self.get_detailed_metrics(),
            'snapshots': [asdict(s) for s in self.snapshots[-100:]]  # Last 100 snapshots
        }

        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2, default=str)

    def get_health_status(self) -> dict[str, Any]:
        """Get system health status based on metrics"""
        summary = self.get_metrics_summary()

        health_status = {
            'status': 'healthy',
            'issues': [],
            'recommendations': []
        }

        # Check error rate
        if summary.get('error_rate', 0) > 0.05:  # More than 5% errors
            health_status['issues'].append('High error rate detected')
            health_status['recommendations'].append('Check server logs for error patterns')

        # Check memory usage
        memory_percent = summary.get('system_metrics', {}).get('avg_memory_percent', 0)
        if memory_percent > 85:
            health_status['issues'].append('High memory usage')
            health_status['recommendations'].append('Consider increasing server memory or optimizing memory usage')

        # Check CPU usage
        cpu_percent = summary.get('system_metrics', {}).get('avg_cpu_percent', 0)
        if cpu_percent > 90:
            health_status['issues'].append('High CPU usage')
            health_status['recommendations'].append('Check for performance bottlenecks or consider scaling')

        # Check database performance
        db_avg_time = summary.get('db_avg_query_time', 0)
        if db_avg_time > 1.0:  # More than 1 second average
            health_status['issues'].append('Slow database queries')
            health_status['recommendations'].append('Consider database optimization or indexing')

        # Set overall status
        if health_status['issues']:
            health_status['status'] = 'warning' if len(health_status['issues']) == 1 else 'critical'

        return health_status

# Global performance monitor instance
performance_monitor = PerformanceMonitor()

def get_performance_monitor() -> PerformanceMonitor:
    """Get the global performance monitor instance"""
    return performance_monitor

# Convenience functions for easy integration
def record_request(endpoint: str, method: str, response_time: float, status_code: int):
    """Convenience function to record HTTP requests"""
    performance_monitor.record_request(endpoint, method, response_time, status_code)

def record_db_query(query_type: str, execution_time: float, table: str = None):
    """Convenience function to record database queries"""
    performance_monitor.record_db_query(query_type, execution_time, table)

def record_memory_operation(operation: str, hit: bool = None):
    """Convenience function to record memory operations"""
    performance_monitor.record_memory_operation(operation, hit)

def start_performance_monitoring(interval_seconds: int = 30):
    """Convenience function to start monitoring"""
    performance_monitor.start_monitoring(interval_seconds)

def stop_performance_monitoring():
    """Convenience function to stop monitoring"""
    performance_monitor.stop_monitoring()

def get_performance_summary() -> dict[str, Any]:
    """Convenience function to get performance summary"""
    return performance_monitor.get_metrics_summary()

def get_health_status() -> dict[str, Any]:
    """Convenience function to get health status"""
    return performance_monitor.get_health_status()
