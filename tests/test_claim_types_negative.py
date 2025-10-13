#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
def test_invalid_claims(client, make_jwt):
    token = make_jwt(claims={"org_id": 123, "roles": "viewer"})
    resp = client.get("/secure-endpoint", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 401
