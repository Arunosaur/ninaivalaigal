#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""Integration tests for API endpoints."""


class TestAPIEndpoints:
    """Test API endpoint integration."""

    def test_health_endpoint(self, client):
        """Test health endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

    def test_memory_crud_flow(self, client, test_memory_data, auth_headers):
        """Test complete memory CRUD flow."""
        # Create memory
        response = client.post("/api/memories", json=test_memory_data, headers=auth_headers)
        assert response.status_code in [200, 201]

        # Get memories
        response = client.get("/api/memories", headers=auth_headers)
        assert response.status_code == 200
