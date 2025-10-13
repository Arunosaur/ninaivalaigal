#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""tracing middleware module."""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

try:
    from opentelemetry import trace

    tracer = trace.get_tracer(__name__)
except ImportError:
    tracer = None


class TracingMiddleware(BaseHTTPMiddleware):
    """TracingMiddleware middleware."""

    async def dispatch(self, request: Request, call_next):
        """Dispatch method."""
        if tracer:
            with tracer.start_as_current_span("http_request") as span:
                span.set_attribute("http.method", request.method)
                span.set_attribute("http.url", str(request.url))
                response = await call_next(request)
                span.set_attribute("http.status_code", response.status_code)
                return response
        return await call_next(request)
