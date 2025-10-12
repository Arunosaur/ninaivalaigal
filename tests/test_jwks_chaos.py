#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
def test_jwks_failure(monkeypatch, client):
    # Simulate JWKS offline by monkeypatching fetch
    from server.security import jwks_utils

    monkeypatch.setattr(
        jwks_utils,
        "fetch_keys",
        lambda: (_ for _ in ()).throw(Exception("JWKS offline")),
    )
    resp = client.get("/secure-endpoint")
    assert resp.status_code == 401
