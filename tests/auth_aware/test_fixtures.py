"""
Auth-Aware Test Fixtures
Comprehensive fixtures for enterprise authentication testing
"""

import asyncio
import uuid
from datetime import datetime, timedelta
from typing import Dict, Generator, List, Optional

import pytest

from .models import (AuthTestResults, ComplianceTestResult, SecurityTestResult,
                     TestSession, TestUser, TestUserStatus, UserRole)
from .multi_user_manager import MultiUserTestManager
from .rbac_engine import RBACTestEngine
from .security_scenarios import SecurityScenarioEngine


@pytest.fixture
def auth_test_config() -> Dict:
    """Configuration for auth-aware testing"""
    return {
        "base_url": "http://localhost:8080",
        "concurrent_limit": 50,
        "test_timeout": 30,
        "rate_limit_threshold": 100,
        "session_timeout_minutes": 30,
    }


@pytest.fixture
def multi_user_manager(auth_test_config) -> MultiUserTestManager:
    """Multi-user test manager instance"""
    return MultiUserTestManager(auth_test_config)


@pytest.fixture
def rbac_engine(auth_test_config) -> RBACTestEngine:
    """RBAC test engine instance"""
    return RBACTestEngine(auth_test_config)


@pytest.fixture
def security_engine(auth_test_config) -> SecurityScenarioEngine:
    """Security scenario engine instance"""
    return SecurityScenarioEngine(auth_test_config)


@pytest.fixture
def admin_user() -> TestUser:
    """Admin test user fixture"""
    return TestUser(
        user_id="test_admin_001",
        username="test_admin",
        email="admin@test.ninaivalaigal.com",
        role=UserRole.ADMIN,
        team_id="admin_team",
        organization_id="test_org",
        password="admin_test_password_123",
    )


@pytest.fixture
def team_lead_user() -> TestUser:
    """Team lead test user fixture"""
    return TestUser(
        user_id="test_lead_001",
        username="test_team_lead",
        email="lead@test.ninaivalaigal.com",
        role=UserRole.TEAM_LEAD,
        team_id="engineering_team",
        organization_id="test_org",
        password="lead_test_password_123",
    )


@pytest.fixture
def member_user() -> TestUser:
    """Member test user fixture"""
    return TestUser(
        user_id="test_member_001",
        username="test_member",
        email="member@test.ninaivalaigal.com",
        role=UserRole.MEMBER,
        team_id="engineering_team",
        organization_id="test_org",
        password="member_test_password_123",
    )


@pytest.fixture
def viewer_user() -> TestUser:
    """Viewer test user fixture"""
    return TestUser(
        user_id="test_viewer_001",
        username="test_viewer",
        email="viewer@test.ninaivalaigal.com",
        role=UserRole.VIEWER,
        team_id="support_team",
        organization_id="test_org",
        password="viewer_test_password_123",
    )


@pytest.fixture
def guest_user() -> TestUser:
    """Guest test user fixture"""
    return TestUser(
        user_id="test_guest_001",
        username="test_guest",
        email="guest@test.ninaivalaigal.com",
        role=UserRole.GUEST,
        team_id="guest_team",
        organization_id="test_org",
        password="guest_test_password_123",
    )


@pytest.fixture
def all_role_users(
    admin_user, team_lead_user, member_user, viewer_user, guest_user
) -> List[TestUser]:
    """All role test users"""
    return [admin_user, team_lead_user, member_user, viewer_user, guest_user]


@pytest.fixture
def multi_team_users() -> List[TestUser]:
    """Users from different teams for isolation testing"""
    users = []

    teams = ["engineering", "support", "product", "sales"]
    roles = [UserRole.TEAM_LEAD, UserRole.MEMBER, UserRole.VIEWER]

    for i, team in enumerate(teams):
        for j, role in enumerate(roles):
            user = TestUser(
                user_id=f"test_{team}_{role.value}_{i}_{j}",
                username=f"{team}_{role.value}_{i}_{j}",
                email=f"{team}.{role.value}.{i}.{j}@test.ninaivalaigal.com",
                role=role,
                team_id=f"{team}_team",
                organization_id="test_org",
                password=f"{team}_{role.value}_password_123",
            )
            users.append(user)

    return users


@pytest.fixture
def concurrent_users() -> List[TestUser]:
    """Large set of users for concurrent testing"""
    users = []

    for i in range(100):  # 100 concurrent users
        role = [UserRole.MEMBER, UserRole.VIEWER, UserRole.TEAM_LEAD][i % 3]
        team_id = f"team_{i % 10}"  # 10 different teams

        user = TestUser(
            user_id=f"concurrent_user_{i:03d}",
            username=f"concurrent_{i:03d}",
            email=f"concurrent.{i:03d}@test.ninaivalaigal.com",
            role=role,
            team_id=team_id,
            organization_id="test_org",
            password=f"concurrent_password_{i:03d}",
        )
        users.append(user)

    return users


@pytest.fixture
def test_session(member_user) -> TestSession:
    """Test session fixture"""
    return TestSession(
        session_id=f"session_{member_user.user_id}_{int(datetime.utcnow().timestamp())}",
        user_id=member_user.user_id,
        token="test_jwt_token_placeholder",
        refresh_token="test_refresh_token_placeholder",
        created_at=datetime.utcnow(),
        expires_at=datetime.utcnow() + timedelta(hours=1),
        last_activity=datetime.utcnow(),
        ip_address="192.168.1.100",
        user_agent="test-client/1.0",
    )


@pytest.fixture
def expired_session(member_user) -> TestSession:
    """Expired test session fixture"""
    return TestSession(
        session_id=f"expired_session_{member_user.user_id}",
        user_id=member_user.user_id,
        token="expired_jwt_token_placeholder",
        refresh_token="expired_refresh_token_placeholder",
        created_at=datetime.utcnow() - timedelta(hours=2),
        expires_at=datetime.utcnow() - timedelta(hours=1),  # Expired
        last_activity=datetime.utcnow() - timedelta(hours=1),
        ip_address="192.168.1.100",
        user_agent="test-client/1.0",
    )


@pytest.fixture
def malicious_payloads() -> Dict[str, List[str]]:
    """Common malicious payloads for security testing"""
    return {
        "sql_injection": [
            "'; DROP TABLE users; --",
            "' OR '1'='1",
            "admin'--",
            "' UNION SELECT * FROM users --",
        ],
        "xss_payloads": [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "<img src=x onerror=alert('xss')>",
            "';alert('xss');//",
        ],
        "command_injection": [
            "; ls -la",
            "| cat /etc/passwd",
            "&& rm -rf /",
            "`whoami`",
        ],
        "path_traversal": [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\drivers\\etc\\hosts",
            "....//....//....//etc/passwd",
            "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd",
        ],
    }


@pytest.fixture
def compliance_test_scenarios() -> Dict[str, List[str]]:
    """Compliance test scenarios for different standards"""
    return {
        "SOC2": [
            "access_control_validation",
            "audit_logging_verification",
            "data_encryption_validation",
            "incident_response_testing",
            "vulnerability_management",
        ],
        "GDPR": [
            "data_subject_rights",
            "consent_management",
            "data_portability",
            "right_to_erasure",
            "privacy_by_design",
        ],
        "ISO27001": [
            "information_security_policy",
            "risk_assessment",
            "access_control_management",
            "cryptography_controls",
            "security_incident_management",
        ],
    }


@pytest.fixture
def performance_thresholds() -> Dict[str, float]:
    """Performance thresholds for auth operations"""
    return {
        "authentication_time_ms": 200,
        "authorization_time_ms": 50,
        "session_validation_time_ms": 10,
        "token_generation_time_ms": 100,
        "concurrent_auth_success_rate": 95.0,
        "rate_limit_response_time_ms": 100,
    }


@pytest.fixture
async def authenticated_users(
    multi_user_manager: MultiUserTestManager, all_role_users: List[TestUser]
) -> List[TestUser]:
    """Pre-authenticated users for testing"""
    # Register and authenticate all users
    for user in all_role_users:
        await multi_user_manager._register_test_user(user)

    return all_role_users


@pytest.fixture
def security_test_matrix() -> Dict[str, Dict]:
    """Security test matrix for comprehensive testing"""
    return {
        "privilege_escalation": {
            "test_users": [UserRole.MEMBER, UserRole.VIEWER, UserRole.GUEST],
            "target_roles": [UserRole.ADMIN, UserRole.TEAM_LEAD],
            "expected_result": "blocked",
        },
        "cross_team_access": {
            "test_scenarios": [
                "read_other_team_memories",
                "modify_other_team_data",
                "access_other_team_analytics",
                "manage_other_team_members",
            ],
            "expected_result": "blocked",
        },
        "token_manipulation": {
            "attack_types": [
                "signature_stripping",
                "algorithm_confusion",
                "claims_modification",
                "token_replay",
            ],
            "expected_result": "blocked",
        },
        "session_attacks": {
            "attack_types": [
                "session_fixation",
                "session_hijacking",
                "concurrent_abuse",
                "timeout_bypass",
            ],
            "expected_result": "blocked",
        },
    }


@pytest.fixture
def load_test_scenarios() -> Dict[str, Dict]:
    """Load test scenarios for performance validation"""
    return {
        "concurrent_authentication": {
            "user_count": 100,
            "duration_seconds": 60,
            "expected_success_rate": 95.0,
            "max_response_time_ms": 500,
        },
        "session_validation_load": {
            "requests_per_second": 1000,
            "duration_seconds": 30,
            "expected_success_rate": 99.0,
            "max_response_time_ms": 50,
        },
        "rate_limit_testing": {
            "requests_per_minute": 200,
            "expected_blocks": True,
            "block_threshold": 100,
            "recovery_time_seconds": 60,
        },
    }


@pytest.fixture
def cleanup_test_data():
    """Cleanup fixture for test data"""
    created_users = []
    created_sessions = []

    yield {"users": created_users, "sessions": created_sessions}

    # Cleanup after tests
    # This would integrate with your cleanup procedures
    for user in created_users:
        # Clean up test user data
        pass

    for session in created_sessions:
        # Clean up test session data
        pass


class AuthTestHelper:
    """Helper class for auth testing utilities"""

    @staticmethod
    def generate_test_user(
        role: UserRole, team_id: str = "test_team", org_id: str = "test_org"
    ) -> TestUser:
        """Generate a test user with specified role"""
        user_id = f"test_{role.value}_{uuid.uuid4().hex[:8]}"

        return TestUser(
            user_id=user_id,
            username=f"user_{user_id}",
            email=f"{user_id}@test.ninaivalaigal.com",
            role=role,
            team_id=team_id,
            organization_id=org_id,
            password=f"password_{user_id}",
        )

    @staticmethod
    def generate_test_session(
        user: TestUser, expires_in_minutes: int = 60
    ) -> TestSession:
        """Generate a test session for user"""
        return TestSession(
            session_id=f"session_{user.user_id}_{uuid.uuid4().hex[:8]}",
            user_id=user.user_id,
            token=f"token_{uuid.uuid4().hex}",
            refresh_token=f"refresh_{uuid.uuid4().hex}",
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(minutes=expires_in_minutes),
            last_activity=datetime.utcnow(),
        )

    @staticmethod
    def create_role_matrix_users(count_per_role: int = 5) -> List[TestUser]:
        """Create users for role matrix testing"""
        users = []

        for role in UserRole:
            for i in range(count_per_role):
                user = AuthTestHelper.generate_test_user(
                    role=role,
                    team_id=f"{role.value}_team_{i}",
                    org_id="matrix_test_org",
                )
                users.append(user)

        return users


@pytest.fixture
def auth_helper() -> AuthTestHelper:
    """Auth test helper instance"""
    return AuthTestHelper()
