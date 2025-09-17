from prometheus_client import Counter, Histogram

# RED metrics (Requests, Errors, Duration)
REQUEST_COUNT = Counter(
    "http_requests_total", "Total HTTP requests",
    ["method", "endpoint", "status"]
)
ERROR_COUNT = Counter(
    "http_errors_total", "Total HTTP errors",
    ["endpoint", "reason"]
)
REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds", "Request latency",
    ["endpoint"]
)

def observe_request(method, endpoint, status, duration, error_reason=None):
    REQUEST_COUNT.labels(method=method, endpoint=endpoint, status=status).inc()
    REQUEST_LATENCY.labels(endpoint=endpoint).observe(duration)
    if error_reason:
        ERROR_COUNT.labels(endpoint=endpoint, reason=error_reason).inc()
