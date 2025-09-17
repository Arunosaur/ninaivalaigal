from __future__ import annotations
try:
    from opentelemetry import trace
except Exception:  # pragma: no cover
    trace = None

def start_span(name: str):
    if trace is None:
        class _Noop:
            def __enter__(self): return self
            def __exit__(self, *a): return False
            def set_attribute(self, *a, **k): pass
        return _Noop()
    tracer = trace.get_tracer("ninaiv.security")
    return tracer.start_as_current_span(name)
