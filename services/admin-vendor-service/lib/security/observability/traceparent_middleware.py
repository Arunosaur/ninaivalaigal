#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""traceparent middleware module."""

import uuid

from starlette.middleware.base import BaseHTTPMiddleware


class TraceparentHeaderMiddleware(BaseHTTPMiddleware):
    """TraceparentHeaderMiddleware middleware."""

    async def dispatch(self, request, call_next):
        """Dispatch method."""
        trace_id = uuid.uuid4().hex
        request.state.trace_id = trace_id
        response = await call_next(request)
        response.headers["traceparent"] = f"00-{trace_id}-00"
        return response
