#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""Prometheus metrics stub for SPEC-118 observability."""

import time

from fastapi import FastAPI
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
from starlette.responses import Response

REQUESTS = Counter("nv_requests_total", "Total API requests", ["route", "method", "status"])
LATENCY = Histogram("nv_request_latency_seconds", "Request latency", buckets=[0.1, 0.2, 0.4, 0.8, 1.6, 3.2])


def instrument(app: FastAPI):
    """Instrument FastAPI app with Prometheus metrics."""

    @app.middleware("http")
    async def _metrics_mw(request, call_next):
        start = time.time()
        resp = await call_next(request)
        LATENCY.observe(time.time() - start)
        REQUESTS.labels(route=str(request.url.path), method=request.method, status=str(resp.status_code)).inc()
        return resp

    @app.get("/metrics")
    async def metrics():
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
