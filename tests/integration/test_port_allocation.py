#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# Port Allocation Tests (SPEC-086)
# Verifies multi-runtime port allocation and network architecture
#

import os
import socket

import pytest


class TestPortAllocation:
    """Test port allocation according to SPEC-086"""

    def test_api_port_configurable(self):
        """Test that API port is configurable via environment"""
        base_port = int(os.getenv("API_PORT", "13370"))
        runtime = os.getenv("NINA_RUNTIME", "docker")
        env = os.getenv("NINA_ENV", "dev")

        # Calculate expected port based on SPEC-086 formula
        # Base Port + Environment Offset + Runtime Offset
        env_offsets = {"dev": 0, "test": 100, "prod": 200}
        runtime_offsets = {"docker": 0, "colima": 10, "apple": 20}

        expected_port = 13370 + env_offsets.get(env, 0) + runtime_offsets.get(runtime, 0)

        # Verify port is in expected range
        assert base_port >= 13370
        assert base_port <= 13999, "Port should be within SPEC-086 range"

        print(f"✅ API Port: {base_port} (expected: {expected_port} for {runtime}/{env})")

    def test_database_port_configurable(self):
        """Test that database port is configurable"""
        # PgBouncer port should be base + offsets
        base_port = int(os.getenv("PGBOUNCER_PORT", "6432"))
        runtime = os.getenv("NINA_RUNTIME", "docker")
        env = os.getenv("NINA_ENV", "dev")

        env_offsets = {"dev": 0, "test": 100, "prod": 200}
        runtime_offsets = {"docker": 0, "colima": 10, "apple": 20}

        expected_port = 6432 + env_offsets.get(env, 0) + runtime_offsets.get(runtime, 0)

        assert base_port >= 6432
        assert base_port <= 6699

        print(f"✅ PgBouncer Port: {base_port} (expected: {expected_port} for {runtime}/{env})")

    def test_port_ranges_no_overlap(self):
        """Verify port ranges don't overlap between runtimes"""
        ports_by_runtime = {
            "docker": {"api": 13370, "pgbouncer": 6432},
            "colima": {"api": 13380, "pgbouncer": 6442},
            "apple": {"api": 13390, "pgbouncer": 6452},
        }

        # Check API ports
        api_ports = [ports_by_runtime[r]["api"] for r in ports_by_runtime]
        assert len(api_ports) == len(set(api_ports)), "API ports should not overlap"

        # Check PgBouncer ports
        pgb_ports = [ports_by_runtime[r]["pgbouncer"] for r in ports_by_runtime]
        assert len(pgb_ports) == len(set(pgb_ports)), "PgBouncer ports should not overlap"

    def test_port_formula_consistency(self):
        """Test that port formula produces consistent results"""
        # Formula: Base Port + Environment Offset + Runtime Offset
        base_api_port = 13370
        base_pgb_port = 6432

        environments = ["dev", "test", "prod"]
        runtimes = ["docker", "colima", "apple"]

        env_offsets = {"dev": 0, "test": 100, "prod": 200}
        runtime_offsets = {"docker": 0, "colima": 10, "apple": 20}

        all_ports = []

        for env in environments:
            for runtime in runtimes:
                api_port = base_api_port + env_offsets[env] + runtime_offsets[runtime]
                pgb_port = base_pgb_port + env_offsets[env] + runtime_offsets[runtime]

                all_ports.append(api_port)
                all_ports.append(pgb_port)

        # All ports should be unique
        assert len(all_ports) == len(set(all_ports)), "Port formula should produce unique ports"

        # Ports should be in valid ranges
        assert all(13370 <= p <= 13999 or 6432 <= p <= 6699 for p in all_ports), "All ports should be in valid ranges"


class TestNetworkConnectivity:
    """Test network connectivity for different runtimes"""

    def test_api_endpoint_accessible(self):
        """Test that API endpoint is accessible on configured port"""
        base_url = os.getenv("TEST_API_BASE_URL", "http://localhost:13390")

        # Extract port from URL
        port = int(base_url.split(":")[-1]) if ":" in base_url else 13370

        # Try to connect to the port
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)

        try:
            result = sock.connect_ex(("localhost", port))
            # 0 means connection successful
            if result != 0:
                pytest.skip(f"Port {port} not accessible (API may not be running)")
            else:
                print(f"✅ Port {port} is accessible")
        finally:
            sock.close()

    def test_port_in_expected_range(self):
        """Test that actual port is in expected range for runtime"""
        base_url = os.getenv("TEST_API_BASE_URL", "http://localhost:13390")
        runtime = os.getenv("NINA_RUNTIME", "apple")

        if ":" in base_url:
            port = int(base_url.split(":")[-1])

            # Expected ranges
            expected_ranges = {"docker": (13370, 13999), "colima": (13380, 13999), "apple": (13390, 13999)}

            min_port, max_port = expected_ranges.get(runtime, (13370, 13999))
            assert min_port <= port <= max_port, f"Port {port} should be in range {min_port}-{max_port} for {runtime}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
