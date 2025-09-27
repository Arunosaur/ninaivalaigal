"""
Foundation SPEC Tests Configuration

Shared fixtures and configuration for all Foundation SPEC tests.
"""

import asyncio
import os
from datetime import datetime, timezone
from typing import Any, Dict, List
from unittest.mock import AsyncMock, Mock

import pytest

# Configure pytest-asyncio
pytest_plugins = ("pytest_asyncio",)


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def foundation_test_config():
    """Foundation test configuration"""
    return {
        "test_database_url": "postgresql://postgres:foundation_test@localhost:5432/foundation_test",  # pragma: allowlist secret
        "test_redis_url": "redis://localhost:6379/15",
        "test_timeout": 30,
        "coverage_threshold": 85.0,
        "performance_threshold_ms": 100,
        "max_concurrent_operations": 50,
    }


@pytest.fixture
async def mock_database_session():
    """Mock database session for testing"""
    session = AsyncMock()
    session.execute.return_value = Mock()
    session.commit.return_value = None
    session.rollback.return_value = None
    session.close.return_value = None
    return session


@pytest.fixture
async def mock_redis_client():
    """Mock Redis client for testing"""
    client = AsyncMock()
    client.get.return_value = None
    client.set.return_value = True
    client.delete.return_value = 1
    client.exists.return_value = False
    client.expire.return_value = True
    return client


@pytest.fixture
async def sample_test_users():
    """Sample test users for foundation tests"""
    return [
        {
            "id": 1,
            "username": "test_user_1",
            "email": "user1@foundation.test",
            "scope": "user",
            "created_at": datetime.now(timezone.utc),
        },
        {
            "id": 2,
            "username": "test_team_1",
            "email": "team1@foundation.test",
            "scope": "team",
            "created_at": datetime.now(timezone.utc),
        },
        {
            "id": 3,
            "username": "test_org_1",
            "email": "org1@foundation.test",
            "scope": "organization",
            "created_at": datetime.now(timezone.utc),
        },
    ]


@pytest.fixture
async def sample_test_memories():
    """Sample test memories for foundation tests"""
    return [
        {
            "id": "mem_1",
            "content": "Test memory content 1",
            "context": "test/context/1",
            "owner_id": 1,
            "scope": "user",
            "created_at": datetime.now(timezone.utc),
        },
        {
            "id": "mem_2",
            "content": "Test memory content 2",
            "context": "test/context/2",
            "owner_id": 2,
            "scope": "team",
            "created_at": datetime.now(timezone.utc),
        },
        {
            "id": "mem_3",
            "content": "Test memory content 3",
            "context": "test/context/3",
            "owner_id": 3,
            "scope": "organization",
            "created_at": datetime.now(timezone.utc),
        },
    ]


@pytest.fixture
async def performance_timer():
    """Performance timing utility for tests"""
    import time

    class PerformanceTimer:
        def __init__(self):
            self.start_time = None
            self.end_time = None

        def start(self):
            self.start_time = time.time()

        def stop(self):
            self.end_time = time.time()
            return self.duration_ms

        @property
        def duration_ms(self):
            if self.start_time and self.end_time:
                return (self.end_time - self.start_time) * 1000
            return None

    return PerformanceTimer()


@pytest.fixture
async def chaos_simulator():
    """Chaos testing simulator for foundation tests"""

    class ChaosSimulator:
        def __init__(self):
            self.active_chaos = []

        async def simulate_database_failure(self, duration_seconds=30):
            """Simulate database connection failure"""
            chaos_event = {
                "type": "database_failure",
                "duration": duration_seconds,
                "started_at": datetime.now(timezone.utc),
            }
            self.active_chaos.append(chaos_event)
            return chaos_event

        async def simulate_redis_failure(self, duration_seconds=15):
            """Simulate Redis connection failure"""
            chaos_event = {
                "type": "redis_failure",
                "duration": duration_seconds,
                "started_at": datetime.now(timezone.utc),
            }
            self.active_chaos.append(chaos_event)
            return chaos_event

        async def simulate_provider_flapping(self, provider_name, flap_count=5):
            """Simulate provider flapping"""
            chaos_event = {
                "type": "provider_flapping",
                "provider": provider_name,
                "flap_count": flap_count,
                "started_at": datetime.now(timezone.utc),
            }
            self.active_chaos.append(chaos_event)
            return chaos_event

        def clear_chaos(self):
            """Clear all active chaos events"""
            self.active_chaos.clear()

    return ChaosSimulator()


@pytest.fixture
async def coverage_validator():
    """Coverage validation utility for tests"""

    class CoverageValidator:
        def __init__(self):
            self.coverage_data = {}

        def validate_spec_coverage(self, spec_id, target_coverage=85.0):
            """Validate coverage for a specific SPEC"""
            actual_coverage = self.coverage_data.get(spec_id, 0.0)
            return {
                "spec_id": spec_id,
                "target_coverage": target_coverage,
                "actual_coverage": actual_coverage,
                "meets_threshold": actual_coverage >= target_coverage,
                "deficit": max(0, target_coverage - actual_coverage),
            }

        def set_coverage(self, spec_id, coverage_percent):
            """Set coverage data for testing"""
            self.coverage_data[spec_id] = coverage_percent

        def generate_coverage_report(self):
            """Generate coverage report"""
            return {
                "total_specs": len(self.coverage_data),
                "average_coverage": (
                    sum(self.coverage_data.values()) / len(self.coverage_data)
                    if self.coverage_data
                    else 0
                ),
                "specs_meeting_threshold": sum(
                    1 for c in self.coverage_data.values() if c >= 85.0
                ),
                "coverage_by_spec": self.coverage_data.copy(),
            }

    return CoverageValidator()


# Pytest markers
def pytest_configure(config):
    """Configure pytest markers"""
    config.addinivalue_line("markers", "foundation: Foundation SPEC tests")
    config.addinivalue_line("markers", "scope: Context scope system tests")
    config.addinivalue_line("markers", "substrate: Memory substrate tests")
    config.addinivalue_line("markers", "cicd: CI/CD pipeline tests")
    config.addinivalue_line("markers", "provider: Memory provider tests")
    config.addinivalue_line("markers", "sharing: Memory sharing tests")
    config.addinivalue_line("markers", "coverage: Test coverage validation")
    config.addinivalue_line("markers", "documentation: Documentation tests")
    config.addinivalue_line("markers", "performance: Performance benchmark tests")
    config.addinivalue_line("markers", "chaos: Chaos/failure scenario tests")


# Test collection hooks
def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on file paths"""
    for item in items:
        # Add markers based on test file location
        if "spec_007" in str(item.fspath):
            item.add_marker(pytest.mark.scope)
        elif "spec_012" in str(item.fspath):
            item.add_marker(pytest.mark.substrate)
        elif "spec_016" in str(item.fspath):
            item.add_marker(pytest.mark.cicd)
        elif "spec_020" in str(item.fspath):
            item.add_marker(pytest.mark.provider)
        elif "spec_049" in str(item.fspath):
            item.add_marker(pytest.mark.sharing)
        elif "spec_052" in str(item.fspath):
            item.add_marker(pytest.mark.coverage)
        elif "spec_058" in str(item.fspath):
            item.add_marker(pytest.mark.documentation)

        # Add foundation marker to all tests in this directory
        if "foundation" in str(item.fspath):
            item.add_marker(pytest.mark.foundation)
