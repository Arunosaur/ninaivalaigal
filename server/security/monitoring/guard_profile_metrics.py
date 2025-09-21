"""
Guard Profile Metrics

Exposes security_guard_profile metric for monitoring edge-decompress and other
security guard modes to track operational behavior and performance.
"""

import time
from dataclasses import dataclass
from enum import Enum
from typing import Any


class GuardMode(Enum):
    """Security guard operational modes."""
    EDGE_DECOMPRESS = "edge-decompress"
    REJECT_ENCODING = "reject-encoding"
    CONTENT_TYPE_STRICT = "content-type-strict"
    MULTIPART_STRICT = "multipart-strict"
    BINARY_MASQUERADE = "binary-masquerade"
    IDEMPOTENCY_REPLAY = "idempotency-replay"
    TIER_FAIL_CLOSED = "tier-fail-closed"


@dataclass
class GuardProfileEvent:
    """Security guard profile event."""
    mode: GuardMode
    action: str  # "allowed", "blocked", "error"
    duration_ms: float
    metadata: dict[str, Any] = None
    timestamp: float = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()


class GuardProfileCollector:
    """Collects and aggregates guard profile metrics."""

    def __init__(self):
        self.events: dict[str, list] = {}
        self.counters: dict[str, int] = {}
        self.durations: dict[str, list] = {}

    def record_event(self, event: GuardProfileEvent):
        """Record a guard profile event."""
        key = f"{event.mode.value}:{event.action}"

        # Store event
        if key not in self.events:
            self.events[key] = []
        self.events[key].append(event)

        # Update counters
        if key not in self.counters:
            self.counters[key] = 0
        self.counters[key] += 1

        # Track durations
        if key not in self.durations:
            self.durations[key] = []
        self.durations[key].append(event.duration_ms)

    def get_prometheus_metrics(self) -> str:
        """Export metrics in Prometheus format."""
        lines = []

        # Counter metrics
        lines.append("# HELP security_guard_profile_total Total security guard operations by mode and action")
        lines.append("# TYPE security_guard_profile_total counter")

        for key, count in self.counters.items():
            mode, action = key.split(":", 1)
            lines.append(f'security_guard_profile_total{{mode="{mode}",action="{action}"}} {count}')

        # Duration metrics
        lines.append("# HELP security_guard_profile_duration_ms Security guard operation duration in milliseconds")
        lines.append("# TYPE security_guard_profile_duration_ms histogram")

        for key, durations in self.durations.items():
            if durations:
                mode, action = key.split(":", 1)
                avg_duration = sum(durations) / len(durations)
                max_duration = max(durations)
                min_duration = min(durations)

                lines.append(f'security_guard_profile_duration_ms_avg{{mode="{mode}",action="{action}"}} {avg_duration:.2f}')
                lines.append(f'security_guard_profile_duration_ms_max{{mode="{mode}",action="{action}"}} {max_duration:.2f}')
                lines.append(f'security_guard_profile_duration_ms_min{{mode="{mode}",action="{action}"}} {min_duration:.2f}')

        return "\n".join(lines)

    def get_summary_stats(self) -> dict[str, Any]:
        """Get summary statistics for all guard profiles."""
        stats = {}

        for mode in GuardMode:
            mode_stats = {
                "total_events": 0,
                "allowed": 0,
                "blocked": 0,
                "errors": 0,
                "avg_duration_ms": 0.0,
                "max_duration_ms": 0.0
            }

            mode_durations = []

            for action in ["allowed", "blocked", "error"]:
                key = f"{mode.value}:{action}"
                count = self.counters.get(key, 0)
                mode_stats[action] = count
                mode_stats["total_events"] += count

                if key in self.durations:
                    mode_durations.extend(self.durations[key])

            if mode_durations:
                mode_stats["avg_duration_ms"] = sum(mode_durations) / len(mode_durations)
                mode_stats["max_duration_ms"] = max(mode_durations)

            if mode_stats["total_events"] > 0:
                stats[mode.value] = mode_stats

        return stats


# Global collector instance
_guard_profile_collector = GuardProfileCollector()


def record_guard_profile(mode: GuardMode, action: str, duration_ms: float, **metadata):
    """Record a guard profile event."""
    event = GuardProfileEvent(
        mode=mode,
        action=action,
        duration_ms=duration_ms,
        metadata=metadata
    )
    _guard_profile_collector.record_event(event)


def get_guard_profile_metrics() -> str:
    """Get Prometheus format metrics."""
    return _guard_profile_collector.get_prometheus_metrics()


def get_guard_profile_stats() -> dict[str, Any]:
    """Get summary statistics."""
    return _guard_profile_collector.get_summary_stats()


# Context manager for timing guard operations
class GuardProfileTimer:
    """Context manager for timing guard profile operations."""

    def __init__(self, mode: GuardMode, **metadata):
        self.mode = mode
        self.metadata = metadata
        self.start_time = None
        self.action = "allowed"  # Default, can be changed

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        duration_ms = (time.time() - self.start_time) * 1000

        # Determine action based on exception
        if exc_type is not None:
            self.action = "error"

        record_guard_profile(self.mode, self.action, duration_ms, **self.metadata)

    def block(self):
        """Mark this operation as blocked."""
        self.action = "blocked"

    def allow(self):
        """Mark this operation as allowed."""
        self.action = "allowed"


def test_guard_profile_metrics():
    """Test guard profile metrics collection."""

    # Simulate various guard operations
    test_cases = [
        (GuardMode.EDGE_DECOMPRESS, "allowed", 1.5, {"content_encoding": "gzip"}),
        (GuardMode.EDGE_DECOMPRESS, "blocked", 0.8, {"content_encoding": "deflate"}),
        (GuardMode.CONTENT_TYPE_STRICT, "allowed", 0.3, {"content_type": "application/json"}),
        (GuardMode.CONTENT_TYPE_STRICT, "blocked", 0.5, {"content_type": "application/octet-stream"}),
        (GuardMode.MULTIPART_STRICT, "blocked", 2.1, {"violation": "binary_masquerade"}),
        (GuardMode.TIER_FAIL_CLOSED, "blocked", 0.1, {"tier": 3, "detector_error": "timeout"}),
    ]

    # Record test events
    for mode, action, duration, metadata in test_cases:
        record_guard_profile(mode, action, duration, **metadata)

    # Test context manager
    with GuardProfileTimer(GuardMode.BINARY_MASQUERADE, file_type="png") as timer:
        time.sleep(0.001)  # Simulate processing
        timer.block()  # Mark as blocked

    # Get metrics and stats
    prometheus_metrics = get_guard_profile_metrics()
    summary_stats = get_guard_profile_stats()

    return {
        "test_events_recorded": len(test_cases) + 1,
        "prometheus_metrics": prometheus_metrics,
        "summary_stats": summary_stats,
        "modes_tracked": list(summary_stats.keys())
    }


if __name__ == "__main__":
    # Run test
    results = test_guard_profile_metrics()

    print("Guard Profile Metrics Test Results:")
    print(f"Events recorded: {results['test_events_recorded']}")
    print(f"Modes tracked: {results['modes_tracked']}")

    print("\nPrometheus Metrics:")
    print(results['prometheus_metrics'])

    print("\nSummary Stats:")
    for mode, stats in results['summary_stats'].items():
        print(f"{mode}: {stats['total_events']} events, {stats['avg_duration_ms']:.2f}ms avg")
