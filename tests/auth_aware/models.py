"""
Auth-Aware Test Models
Data models for enterprise authentication testing
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional


class UserRole(Enum):
    """User roles for RBAC testing"""

    ADMIN = "admin"
    TEAM_LEAD = "team_lead"
    MEMBER = "member"
    VIEWER = "viewer"
    GUEST = "guest"


class TestUserStatus(Enum):
    """Test user status"""

    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    EXPIRED = "expired"


class AuthTestResult(Enum):
    """Authentication test result status"""

    PASS = "pass"
    FAIL = "fail"
    ERROR = "error"
    SKIP = "skip"


@dataclass
class TestUser:
    """Test user for auth-aware testing"""

    user_id: str
    username: str
    email: str
    role: UserRole
    team_id: str
    organization_id: str
    password: str = "test_password_123"
    status: TestUserStatus = TestUserStatus.ACTIVE
    permissions: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None
    session_data: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Set default permissions based on role"""
        if not self.permissions:
            self.permissions = self._get_default_permissions()

    def _get_default_permissions(self) -> List[str]:
        """Get default permissions for user role"""
        role_permissions = {
            UserRole.ADMIN: [
                "admin:read",
                "admin:write",
                "admin:delete",
                "user:read",
                "user:write",
                "user:delete",
                "team:read",
                "team:write",
                "team:delete",
                "memory:read",
                "memory:write",
                "memory:delete",
                "analytics:read",
                "billing:read",
                "billing:write",
            ],
            UserRole.TEAM_LEAD: [
                "user:read",
                "user:write",
                "team:read",
                "team:write",
                "memory:read",
                "memory:write",
                "memory:delete",
                "analytics:read",
            ],
            UserRole.MEMBER: [
                "user:read",
                "team:read",
                "memory:read",
                "memory:write",
                "analytics:read",
            ],
            UserRole.VIEWER: [
                "user:read",
                "team:read",
                "memory:read",
                "analytics:read",
            ],
            UserRole.GUEST: ["memory:read"],
        }
        return role_permissions.get(self.role, [])


@dataclass
class TestSession:
    """Test session for auth testing"""

    session_id: str
    user_id: str
    token: str
    refresh_token: Optional[str]
    created_at: datetime
    expires_at: datetime
    last_activity: datetime
    ip_address: str = "127.0.0.1"
    user_agent: str = "test-client/1.0"
    is_active: bool = True
    session_data: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_expired(self) -> bool:
        """Check if session is expired"""
        return datetime.utcnow() > self.expires_at

    @property
    def time_remaining(self) -> timedelta:
        """Get remaining session time"""
        if self.is_expired:
            return timedelta(0)
        return self.expires_at - datetime.utcnow()


@dataclass
class AuthTestResults:
    """Results from authentication testing"""

    test_name: str
    result: AuthTestResult
    user_count: int
    success_count: int
    failure_count: int
    error_count: int
    execution_time_ms: float
    details: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage"""
        if self.user_count == 0:
            return 0.0
        return (self.success_count / self.user_count) * 100

    @property
    def is_passing(self) -> bool:
        """Check if test is passing (>95% success rate)"""
        return self.success_rate >= 95.0


@dataclass
class PermissionTestResult:
    """Result from permission testing"""

    endpoint: str
    method: str
    user_role: UserRole
    expected_result: str  # "allow" or "deny"
    actual_result: str
    response_code: int
    execution_time_ms: float
    error_message: Optional[str] = None

    @property
    def is_correct(self) -> bool:
        """Check if permission test result is correct"""
        return self.expected_result == self.actual_result


@dataclass
class SecurityTestResult:
    """Result from security scenario testing"""

    test_scenario: str
    attack_type: str
    user_id: str
    attack_prevented: bool
    response_code: int
    execution_time_ms: float
    attack_details: Dict[str, Any] = field(default_factory=dict)
    security_logs: List[str] = field(default_factory=list)

    @property
    def is_secure(self) -> bool:
        """Check if security test passed (attack was prevented)"""
        return self.attack_prevented


@dataclass
class ConflictResults:
    """Results from session conflict testing"""

    total_conflicts: int
    session_conflicts: List[Dict[str, Any]]
    data_conflicts: List[Dict[str, Any]]
    resolution_time_ms: float
    conflicts_resolved: bool

    @property
    def has_conflicts(self) -> bool:
        """Check if any conflicts were detected"""
        return self.total_conflicts > 0


@dataclass
class IsolationResults:
    """Results from user isolation testing"""

    user_a_id: str
    user_b_id: str
    isolation_maintained: bool
    cross_access_attempts: int
    blocked_attempts: int
    data_leakage_detected: bool
    isolation_violations: List[str] = field(default_factory=list)

    @property
    def isolation_score(self) -> float:
        """Calculate isolation effectiveness score"""
        if self.cross_access_attempts == 0:
            return 100.0
        return (self.blocked_attempts / self.cross_access_attempts) * 100


@dataclass
class ComplianceTestResult:
    """Result from compliance testing"""

    compliance_standard: str  # "SOC2", "GDPR", "ISO27001"
    test_category: str
    requirement_id: str
    test_passed: bool
    evidence_collected: bool
    audit_trail_complete: bool
    compliance_score: float
    findings: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)

    @property
    def is_compliant(self) -> bool:
        """Check if compliance test passed"""
        return (
            self.test_passed
            and self.evidence_collected
            and self.audit_trail_complete
            and self.compliance_score >= 90.0
        )


@dataclass
class LoadTestMetrics:
    """Metrics from auth load testing"""

    concurrent_users: int
    total_requests: int
    successful_requests: int
    failed_requests: int
    avg_response_time_ms: float
    p95_response_time_ms: float
    p99_response_time_ms: float
    throughput_rps: float
    error_rate: float

    @property
    def performance_grade(self) -> str:
        """Get performance grade based on metrics"""
        if self.error_rate > 5.0:
            return "F"
        elif self.p95_response_time_ms > 1000:
            return "D"
        elif self.p95_response_time_ms > 500:
            return "C"
        elif self.p95_response_time_ms > 200:
            return "B"
        else:
            return "A"


@dataclass
class AuthTestSuite:
    """Complete auth test suite results"""

    suite_name: str
    start_time: datetime
    end_time: Optional[datetime]
    total_tests: int
    passed_tests: int
    failed_tests: int
    error_tests: int
    skipped_tests: int
    test_results: List[AuthTestResults] = field(default_factory=list)
    security_results: List[SecurityTestResult] = field(default_factory=list)
    compliance_results: List[ComplianceTestResult] = field(default_factory=list)
    load_metrics: Optional[LoadTestMetrics] = None

    @property
    def duration_seconds(self) -> float:
        """Get test suite duration in seconds"""
        if not self.end_time:
            return 0.0
        return (self.end_time - self.start_time).total_seconds()

    @property
    def success_rate(self) -> float:
        """Calculate overall success rate"""
        if self.total_tests == 0:
            return 0.0
        return (self.passed_tests / self.total_tests) * 100

    @property
    def is_enterprise_ready(self) -> bool:
        """Check if test suite indicates enterprise readiness"""
        return (
            self.success_rate >= 95.0
            and all(sr.is_secure for sr in self.security_results)
            and all(cr.is_compliant for cr in self.compliance_results)
            and (
                not self.load_metrics
                or self.load_metrics.performance_grade in ["A", "B"]
            )
        )
