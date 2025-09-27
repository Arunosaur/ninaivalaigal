# Response Redaction Middleware & ASGI Benchmark

This pack includes:
- `server/security/middleware/response_redaction.py` – ASGI middleware that **redacts response bodies** chunk-by-chunk.
- `tests/test_response_redaction_middleware.py` – unit test using FastAPI `TestClient`.
- `benchmarks/asgi_upload_harness.py` – in-process ASGI benchmark that simulates large uploads (default 8 MiB).

## Usage – Response Middleware
```python
from fastapi import FastAPI
from server.security.middleware.response_redaction import ResponseRedactionASGIMiddleware
from server.security.redaction.detector_glue import detector_fn

app = FastAPI()
app.add_middleware(ResponseRedactionASGIMiddleware, detector_fn=detector_fn, overlap=64)
```

## Benchmark
Run locally (no network sockets required):
```bash
PAYLOAD_MB=32 CHUNK_SIZE=65536 python benchmarks/asgi_upload_harness.py
```
You will see throughput for: no middleware, request-only, response-only, and both.
