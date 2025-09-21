from __future__ import annotations

import asyncio
import math
import os
import time

from httpx import AsyncClient
from starlette.applications import Starlette
from starlette.responses import PlainTextResponse
from starlette.routing import Route

from server.security.middleware.fastapi_redaction import (
    RedactionASGIMiddleware,  # reuse request MW if present
)
from server.security.middleware.response_redaction import (
    ResponseRedactionASGIMiddleware,
)

SECRET = "AKIAIOSFODNN7EXAMPLE"
PAYLOAD_MB = float(os.environ.get("PAYLOAD_MB", "8"))  # default 8 MB
CHUNK_SIZE = int(os.environ.get("CHUNK_SIZE", "65536"))  # 64KB

def detector_fn(text: str) -> str:
    # extremely simple for benchmark
    return text.replace(SECRET, "<AWS_KEY>")

async def echo(request):
    body = await request.body()
    return PlainTextResponse(body)

def build_app(with_request_mw: bool, with_response_mw: bool):
    app = Starlette(routes=[Route("/echo", echo, methods=["POST"])])
    if with_request_mw:
        app.add_middleware(RedactionASGIMiddleware, detector_fn=detector_fn, overlap=64)
    if with_response_mw:
        app.add_middleware(ResponseRedactionASGIMiddleware, detector_fn=detector_fn, overlap=64)
    return app

def make_payload(size_bytes: int) -> bytes:
    # Insert secret every ~4KB to exercise detector
    chunk = (("x"*2000) + SECRET + ("y"*2000)).encode()
    reps = math.ceil(size_bytes / len(chunk))
    data = chunk * reps
    return data[:size_bytes]

async def run_case(label: str, app, payload: bytes):
    async with AsyncClient(app=app, base_url="http://test") as client:
        t0 = time.perf_counter()
        r = await client.post("/echo", content=payload, headers={"content-type":"text/plain"})
        dt = time.perf_counter() - t0
        ok = r.status_code == 200 and "<AWS_KEY>" in r.text
        return label, dt, len(payload), ok

async def main():
    size = int(PAYLOAD_MB * 1024 * 1024)
    payload = make_payload(size)

    cases = [
        ("no-mw", build_app(False, False)),
        ("req-only", build_app(True, False)),
        ("resp-only", build_app(False, True)),
        ("both", build_app(True, True)),
    ]

    results = []
    for label, app in cases:
        label, dt, n, ok = await run_case(label, app, payload)
        results.append((label, dt, n, ok))

    print("\n=== ASGI Redaction Benchmark (in-process) ===")
    for label, dt, n, ok in results:
        mbps = (n / (1024*1024)) / dt
        print(f"{label:9s} | {dt:6.3f}s | {mbps:7.2f} MiB/s | ok={ok}")

if __name__ == "__main__":
    asyncio.run(main())
