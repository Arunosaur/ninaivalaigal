#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from server.health.config_hash_guard import compute_hash, router

pytestmark = pytest.mark.unit


def test_health_config_hash_endpoint_exposes_hash(monkeypatch):
    monkeypatch.setenv("JWT_SECRET", "s1")
    monkeypatch.setenv("UPLOAD_LIMIT", "10MB")
    monkeypatch.setenv("REDIS_URL", "memory://")

    app = FastAPI()
    app.include_router(router)
    c = TestClient(app)

    r = c.get("/healthz/config")
    assert r.status_code == 200
    h = r.json().get("security_config_hash")
    assert h == compute_hash()
    assert len(h) == 64
