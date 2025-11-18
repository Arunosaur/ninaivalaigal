#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""
Load Testing for Platform Stability Monitoring (US#407)

This module provides comprehensive load testing scenarios for validating
the platform stability monitoring system under various load conditions.

Usage:
    # Normal load (100 users)
    locust -f tests/load/test_platform_monitoring_load.py --headless --users 100 --spawn-rate 10 --run-time 30m

    # Peak load (500 users)
    locust -f tests/load/test_platform_monitoring_load.py --headless --users 500 --spawn-rate 100 --run-time 15m

    # Stress test (1000 users)
    locust -f tests/load/test_platform_monitoring_load.py --headless --users 1000 --spawn-rate 200 --run-time 10m
"""

import logging
import random

from locust import HttpUser, between, events, task

logger = logging.getLogger(__name__)


class PlatformMonitoringUser(HttpUser):
    """
    Simulates a user making requests to various platform services
    to validate monitoring system performance under load.
    """

    # Wait between 1-3 seconds between tasks (realistic user behavior)
    wait_time = between(1, 3)

    # Service endpoints to test
    services = [
        "core-api",
        "memory-service",
        "graph-service",
        "business-service",
        "upload-api",
        "redis",
        "postgres",
        "pgbouncer",
    ]

    def on_start(self):
        """Called when a user starts - simulate login/setup"""
        logger.info(f"User {self.environment.runner.user_count} started")

    @task(10)
    def check_platform_health_summary(self):
        """
        Most common operation: Check overall platform health
        Weight: 10 (highest frequency)
        """
        with self.client.get(
            "/platform/health/summary", catch_response=True, name="Platform Health Summary"
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if data.get("overall_status") in ["healthy", "degraded", "unhealthy"]:
                    response.success()
                else:
                    response.failure(f"Invalid status: {data.get('overall_status')}")
            else:
                response.failure(f"Status code: {response.status_code}")

    @task(5)
    def check_all_containers(self):
        """
        Check all container health statuses
        Weight: 5 (medium frequency)
        """
        with self.client.get(
            "/platform/health/containers", catch_response=True, name="All Containers Health"
        ) as response:
            if response.status_code == 200:
                data = response.json()
                # API returns "services" key, not "containers"
                if isinstance(data, dict) and "services" in data:
                    response.success()
                else:
                    response.failure("Invalid response format")
            else:
                response.failure(f"Status code: {response.status_code}")

    @task(3)
    def check_specific_service(self):
        """
        Check health of a specific service
        Weight: 3 (medium-low frequency)
        """
        service = random.choice(self.services)
        with self.client.get(
            f"/platform/health/containers/{service}", catch_response=True, name=f"Service Health: {service}"
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if data.get("service") == service:
                    response.success()
                else:
                    response.failure(f"Service mismatch: {data.get('service')}")
            elif response.status_code == 404:
                # Service might not exist, that's ok
                response.success()
            else:
                response.failure(f"Status code: {response.status_code}")

    @task(4)
    def check_dependencies(self):
        """
        Check service dependencies
        Weight: 4 (medium frequency)
        """
        with self.client.get(
            "/platform/health/dependencies", catch_response=True, name="Service Dependencies"
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, dict):
                    response.success()
                else:
                    response.failure("Invalid response format")
            else:
                response.failure(f"Status code: {response.status_code}")

    @task(2)
    def check_performance_metrics(self):
        """
        Check performance metrics and baselines
        Weight: 2 (low frequency)
        """
        with self.client.get(
            "/platform/health/performance", catch_response=True, name="Performance Metrics"
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, dict):
                    response.success()
                else:
                    response.failure("Invalid response format")
            else:
                response.failure(f"Status code: {response.status_code}")

    @task(2)
    def check_uptime(self):
        """
        Check service uptime
        Weight: 2 (low frequency)
        """
        with self.client.get("/platform/health/uptime", catch_response=True, name="Service Uptime") as response:
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, dict):
                    response.success()
                else:
                    response.failure("Invalid response format")
            else:
                response.failure(f"Status code: {response.status_code}")

    @task(1)
    def trigger_manual_check(self):
        """
        Trigger manual health check
        Weight: 1 (lowest frequency)
        """
        with self.client.post("/platform/health/check", catch_response=True, name="Manual Health Check") as response:
            if response.status_code in [200, 202]:
                response.success()
            else:
                response.failure(f"Status code: {response.status_code}")


class BurstTrafficUser(HttpUser):
    """
    Simulates burst traffic patterns for peak load testing.
    Makes rapid requests with minimal wait time.
    """

    wait_time = between(0.1, 0.5)  # Very short wait for burst testing

    @task
    def rapid_health_checks(self):
        """Rapid-fire health checks to simulate burst traffic"""
        endpoints = ["/platform/health/summary", "/platform/health/containers", "/platform/health/dependencies"]

        endpoint = random.choice(endpoints)
        with self.client.get(endpoint, catch_response=True, name="Burst Traffic") as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Status code: {response.status_code}")


class StressTestUser(HttpUser):
    """
    Simulates stress test conditions with aggressive request patterns.
    Used to find breaking points of the monitoring system.
    """

    wait_time = between(0.05, 0.2)  # Minimal wait for stress testing

    @task(5)
    def aggressive_summary_checks(self):
        """Aggressive health summary checks"""
        self.client.get("/platform/health/summary", name="Stress: Summary")

    @task(3)
    def aggressive_container_checks(self):
        """Aggressive container checks"""
        self.client.get("/platform/health/containers", name="Stress: Containers")

    @task(2)
    def aggressive_performance_checks(self):
        """Aggressive performance checks"""
        self.client.get("/platform/health/performance", name="Stress: Performance")


# Event handlers for custom metrics and logging


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Called when the test starts"""
    logger.info("=" * 80)
    logger.info("Platform Monitoring Load Test Starting")
    logger.info(f"Target host: {environment.host}")
    user_count = environment.runner.target_user_count if hasattr(environment.runner, "target_user_count") else "N/A"
    logger.info(f"User count: {user_count}")
    logger.info("=" * 80)


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Called when the test stops"""
    logger.info("=" * 80)
    logger.info("Platform Monitoring Load Test Completed")
    logger.info(f"Total requests: {environment.stats.total.num_requests}")
    logger.info(f"Total failures: {environment.stats.total.num_failures}")
    logger.info(f"Average response time: {environment.stats.total.avg_response_time:.2f}ms")
    logger.info(f"Requests per second: {environment.stats.total.total_rps:.2f}")
    logger.info("=" * 80)


@events.request.add_listener
def on_request(request_type, name, response_time, response_length, exception, **kwargs):
    """
    Called for every request - can be used for custom metrics
    """
    # Log slow requests (>1000ms)
    if response_time > 1000:
        logger.warning(f"Slow request detected: {name} took {response_time:.2f}ms")

    # Log failures
    if exception:
        logger.error(f"Request failed: {name} - {exception}")


# Custom test scenarios


class RealisticTrafficUser(HttpUser):
    """
    Simulates realistic production traffic patterns based on
    expected usage distribution.

    Distribution:
    - 40% health summary checks
    - 20% container health checks
    - 15% dependency checks
    - 10% performance metrics
    - 10% specific service checks
    - 5% other operations
    """

    wait_time = between(2, 5)  # Realistic user think time

    @task(40)
    def health_summary(self):
        self.client.get("/platform/health/summary", name="Realistic: Summary")

    @task(20)
    def container_health(self):
        self.client.get("/platform/health/containers", name="Realistic: Containers")

    @task(15)
    def dependencies(self):
        self.client.get("/platform/health/dependencies", name="Realistic: Dependencies")

    @task(10)
    def performance(self):
        self.client.get("/platform/health/performance", name="Realistic: Performance")

    @task(10)
    def specific_service(self):
        service = random.choice(["core-api", "memory-service", "redis"])
        self.client.get(f"/platform/health/containers/{service}", name="Realistic: Service")

    @task(5)
    def other_operations(self):
        endpoints = ["/platform/health/uptime", "/platform/health/check"]
        endpoint = random.choice(endpoints)
        if endpoint.endswith("/check"):
            self.client.post(endpoint, name="Realistic: Other")
        else:
            self.client.get(endpoint, name="Realistic: Other")


# Configuration for different test scenarios

"""
USAGE EXAMPLES:

1. Normal Load Test (100 concurrent users, 30 minutes):
   locust -f tests/load/test_platform_monitoring_load.py \\
     --headless \\
     --users 100 \\
     --spawn-rate 10 \\
     --run-time 30m \\
     --host http://localhost:8000 \\
     --html load_test_report.html

2. Peak Load Test (500 concurrent users, 15 minutes):
   locust -f tests/load/test_platform_monitoring_load.py \\
     --headless \\
     --users 500 \\
     --spawn-rate 100 \\
     --run-time 15m \\
     --host http://localhost:8000 \\
     --user-classes BurstTrafficUser

3. Stress Test (1000 concurrent users, 10 minutes):
   locust -f tests/load/test_platform_monitoring_load.py \\
     --headless \\
     --users 1000 \\
     --spawn-rate 200 \\
     --run-time 10m \\
     --host http://localhost:8000 \\
     --user-classes StressTestUser

4. Realistic Traffic Pattern (200 concurrent users, 1 hour):
   locust -f tests/load/test_platform_monitoring_load.py \\
     --headless \\
     --users 200 \\
     --spawn-rate 20 \\
     --run-time 1h \\
     --host http://localhost:8000 \\
     --user-classes RealisticTrafficUser

5. Web UI Mode (for interactive testing):
   locust -f tests/load/test_platform_monitoring_load.py \\
     --host http://localhost:8000
   # Then open http://localhost:8089 in browser
"""
