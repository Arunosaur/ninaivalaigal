"""tracing module."""

from __future__ import annotations

try:
    from opentelemetry import trace
except Exception:  # pragma: no cover
    trace = None


def start_span(name: str):
    """Start an OpenTelemetry tracing span or return no-op if unavailable."""
    if trace is None:

        class _Noop:
            def __enter__(self):
                """enter   method."""
                return self

            def __exit__(self, *a):
                """exit   method."""
                return False

            def set_attribute(self, *a, **k):
                """Set attribute."""
                pass

        return _Noop()
    tracer = trace.get_tracer("ninaiv.security")
    return tracer.start_as_current_span(name)
