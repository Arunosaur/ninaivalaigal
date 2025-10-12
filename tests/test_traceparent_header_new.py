#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
from fastapi import FastAPI
from fastapi.testclient import TestClient

from server.security.observability.traceparent_middleware import (
    TraceparentHeaderMiddleware,
)


def test_traceparent_header_present():
    app = FastAPI()
    app = TraceparentHeaderMiddleware(app)

    @app.get("/ping")
    def ping():
        return {"ok": True}

    c = TestClient(app)
    r = c.get("/ping")
    assert r.status_code == 200
    tp = r.headers.get("traceparent")
    assert tp is not None and len(tp) > 10
