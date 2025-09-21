# Spec 010 Kickoff Bundle

This package includes:
- Tracing middleware for OpenTelemetry spans
- RED metrics (Requests, Errors, Duration)
- Grafana dashboard JSON (importable)
- Prometheus alerts YAML
- Negative/chaos test cases

## Usage
1. Wire TracingMiddleware in ASGI stack.
2. Import Grafana JSON dashboard.
3. Load Prometheus alerts.
4. Run tests with pytest.
