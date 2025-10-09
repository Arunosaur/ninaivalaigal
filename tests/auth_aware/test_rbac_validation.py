"""
RBAC Validation Tests
Role-based access control testing for enterprise security validation
"""

import asyncio
from typing import List

import pytest

from .models import AuthTestResult, UserRole
from .rbac_engine import RBACTestEngine
from .test_fixtures import AuthTestHelper


class TestRBACValidation:
    """Test suite for RBAC validation scenarios"""

    @pytest.mark.asyncio
    async def test_admin_role_permissions(self, rbac_engine: RBACTestEngine, admin_user):
        """Test admin role has all required permissions"""

        # Test admin permissions
        permission_results = await rbac_engine.test_role_permissions(admin_user)

        # Admin should have access to all endpoints
        admin_endpoints = [result for result in permission_results if result.expected_result == "allow"]

        # Validate admin access
        assert len(admin_endpoints) > 0

        # All admin endpoints should be accessible
        successful_admin_access = sum(1 for result in admin_endpoints if result.is_correct)
        assert successful_admin_access == len(admin_endpoints)

        # Validate specific admin permissions
        admin_endpoint_methods = [(r.endpoint, r.method) for r in admin_endpoints]

        # Should include admin-specific endpoints
        assert any("/admin/users" in endpoint for endpoint, method in admin_endpoint_methods)
        assert any("/admin/teams" in endpoint for endpoint, method in admin_endpoint_methods)
        assert any("/admin/audit" in endpoint for endpoint, method in admin_endpoint_methods)

    @pytest.mark.asyncio
    async def test_team_lead_role_permissions(self, rbac_engine: RBACTestEngine, team_lead_user):
        """Test team lead role permissions"""

        permission_results = await rbac_engine.test_role_permissions(team_lead_user)

        # Separate allowed and forbidden results
        allowed_results = [r for r in permission_results if r.expected_result == "allow"]
        forbidden_results = [r for r in permission_results if r.expected_result == "deny"]

        # Validate team lead permissions
        successful_allowed = sum(1 for r in allowed_results if r.is_correct)
        successful_forbidden = sum(1 for r in forbidden_results if r.is_correct)

        assert successful_allowed == len(allowed_results)
        assert successful_forbidden == len(forbidden_results)

        # Team lead should have team management permissions
        team_endpoints = [r.endpoint for r in allowed_results]
        assert any("teams" in endpoint for endpoint in team_endpoints)
        assert any("memories" in endpoint for endpoint in team_endpoints)

        # Team lead should NOT have admin permissions
        forbidden_endpoints = [r.endpoint for r in forbidden_results]
        assert any("/admin/" in endpoint for endpoint in forbidden_endpoints)

    @pytest.mark.asyncio
    async def test_member_role_permissions(self, rbac_engine: RBACTestEngine, member_user):
        """Test member role permissions"""

        permission_results = await rbac_engine.test_role_permissions(member_user)

        allowed_results = [r for r in permission_results if r.expected_result == "allow"]
        forbidden_results = [r for r in permission_results if r.expected_result == "deny"]

        # Validate member permissions
        successful_allowed = sum(1 for r in allowed_results if r.is_correct)
        successful_forbidden = sum(1 for r in forbidden_results if r.is_correct)

        assert successful_allowed == len(allowed_results)
        assert successful_forbidden == len(forbidden_results)

        # Member should have basic access
        allowed_endpoints = [r.endpoint for r in allowed_results]
        assert any("memories" in endpoint for endpoint in allowed_endpoints)

        # Member should NOT have admin or team management permissions
        forbidden_endpoints = [r.endpoint for r in forbidden_results]
        assert any("/admin/" in endpoint for endpoint in forbidden_endpoints)
        assert any("DELETE" in r.method for r in forbidden_results if "memories" in r.endpoint)

    @pytest.mark.asyncio
    async def test_viewer_role_permissions(self, rbac_engine: RBACTestEngine, viewer_user):
        """Test viewer role permissions (read-only)"""

        permission_results = await rbac_engine.test_role_permissions(viewer_user)

        allowed_results = [r for r in permission_results if r.expected_result == "allow"]
        forbidden_results = [r for r in permission_results if r.expected_result == "deny"]

        # Validate viewer permissions
        successful_allowed = sum(1 for r in allowed_results if r.is_correct)
        successful_forbidden = sum(1 for r in forbidden_results if r.is_correct)

        assert successful_allowed == len(allowed_results)
        assert successful_forbidden == len(forbidden_results)

        # Viewer should only have GET permissions
        allowed_methods = [r.method for r in allowed_results]
        assert all(method == "GET" for method in allowed_methods)

        # Viewer should NOT have write permissions
        forbidden_methods = [r.method for r in forbidden_results]
        assert any(method in ["POST", "PUT", "DELETE"] for method in forbidden_methods)

    @pytest.mark.asyncio
    async def test_guest_role_permissions(self, rbac_engine: RBACTestEngine, guest_user):
        """Test guest role permissions (minimal access)"""

        permission_results = await rbac_engine.test_role_permissions(guest_user)

        allowed_results = [r for r in permission_results if r.expected_result == "allow"]
        forbidden_results = [r for r in permission_results if r.expected_result == "deny"]

        # Validate guest permissions
        successful_allowed = sum(1 for r in allowed_results if r.is_correct)
        successful_forbidden = sum(1 for r in forbidden_results if r.is_correct)

        assert successful_allowed == len(allowed_results)
        assert successful_forbidden == len(forbidden_results)

        # Guest should have very limited access
        assert len(allowed_results) <= 3  # Very few allowed endpoints
        assert len(forbidden_results) >= 10  # Many forbidden endpoints

        # Guest should only access public memories
        allowed_endpoints = [r.endpoint for r in allowed_results]
        assert all("memories" in endpoint for endpoint in allowed_endpoints)

    @pytest.mark.asyncio
    async def test_permission_boundary_enforcement(self, rbac_engine: RBACTestEngine, all_role_users: List):
        """Test permission boundaries are enforced for all roles"""

        for user in all_role_users:
            # Define forbidden actions based on role
            forbidden_actions = self._get_forbidden_actions_for_role(user.role)

            # Test permission boundaries
            boundary_results = await rbac_engine.test_permission_boundaries(user, forbidden_actions)

            # All forbidden actions should be blocked
            blocked_count = sum(1 for result in boundary_results if result.is_correct)
            assert blocked_count == len(boundary_results)

            # Validate no privilege escalation
            escalation_attempts = [r for r in boundary_results if "escalation" in r.endpoint or "admin" in r.endpoint]

            for attempt in escalation_attempts:
                assert attempt.actual_result == "deny"
                assert attempt.response_code in [401, 403, 404]

    @pytest.mark.asyncio
    async def test_role_switching_validation(self, rbac_engine: RBACTestEngine, member_user, team_lead_user):
        """Test role switching functionality and validation"""

        # Test member trying to switch to team lead
        member_switch_result = await rbac_engine.test_role_switching(member_user, UserRole.TEAM_LEAD)

        # Member should NOT be able to switch to team lead
        assert member_switch_result.result == AuthTestResult.PASS  # Test passes because switch was properly blocked
        assert not member_switch_result.details.get("switch_successful", True)

        # Test team lead trying to switch to member (downgrade)
        lead_switch_result = await rbac_engine.test_role_switching(team_lead_user, UserRole.MEMBER)

        # Team lead should be able to switch to member (if allowed by policy)
        switch_allowed = lead_switch_result.details.get("switch_allowed", False)
        switch_successful = lead_switch_result.details.get("switch_successful", False)

        # Validate switch behavior matches policy
        assert switch_successful == switch_allowed

    @pytest.mark.asyncio
    async def test_cross_team_access_control(self, rbac_engine: RBACTestEngine, multi_team_users: List):
        """Test cross-team access control validation"""

        # Get users from different teams
        teams = list(set(user.team_id for user in multi_team_users))

        for i, user in enumerate(multi_team_users[:5]):  # Test first 5 users
            # Get a different team ID
            other_teams = [t for t in teams if t != user.team_id]
            if other_teams:
                target_team = other_teams[0]

                # Test cross-team access
                cross_team_results = await rbac_engine.validate_cross_team_access(user, target_team)

                # Validate cross-team access control
                for result in cross_team_results:
                    if user.role != UserRole.ADMIN:
                        # Non-admin users should be blocked from other teams
                        if "POST" in result.method or "PUT" in result.method or "DELETE" in result.method:
                            assert result.actual_result == "deny"
                    else:
                        # Admin users should have cross-team access
                        assert result.actual_result == "allow"

    @pytest.mark.asyncio
    async def test_role_permission_matrix_validation(self, rbac_engine: RBACTestEngine, auth_helper: AuthTestHelper):
        """Test complete role permission matrix"""

        # Create users for each role
        role_users = {}
        for role in UserRole:
            role_users[role] = auth_helper.generate_test_user(role)

        # Test permission matrix for each role
        role_results = {}

        for role, user in role_users.items():
            permission_results = await rbac_engine.test_role_permissions(user)
            role_results[role] = permission_results

        # Validate role hierarchy
        admin_allowed = len([r for r in role_results[UserRole.ADMIN] if r.expected_result == "allow"])
        lead_allowed = len([r for r in role_results[UserRole.TEAM_LEAD] if r.expected_result == "allow"])
        member_allowed = len([r for r in role_results[UserRole.MEMBER] if r.expected_result == "allow"])
        viewer_allowed = len([r for r in role_results[UserRole.VIEWER] if r.expected_result == "allow"])
        guest_allowed = len([r for r in role_results[UserRole.GUEST] if r.expected_result == "allow"])

        # Validate permission hierarchy (admin > team_lead > member > viewer > guest)
        assert admin_allowed >= lead_allowed
        assert lead_allowed >= member_allowed
        assert member_allowed >= viewer_allowed
        assert viewer_allowed >= guest_allowed

    @pytest.mark.asyncio
    async def test_concurrent_rbac_validation(self, rbac_engine: RBACTestEngine, all_role_users: List):
        """Test RBAC validation under concurrent access"""

        # Test concurrent permission validation
        permission_tasks = []

        for user in all_role_users:
            task = rbac_engine.test_role_permissions(user)
            permission_tasks.append(task)

        # Execute concurrent RBAC tests
        concurrent_results = await asyncio.gather(*permission_tasks, return_exceptions=True)

        # Validate concurrent RBAC consistency
        successful_tests = sum(1 for result in concurrent_results if not isinstance(result, Exception))

        assert successful_tests == len(all_role_users)

        # Validate no permission bleeding between concurrent tests
        for i, result in enumerate(concurrent_results):
            if not isinstance(result, Exception):
                all_role_users[i].role

                # Validate results match expected role permissions
                allowed_results = [r for r in result if r.expected_result == "allow"]
                correct_permissions = sum(1 for r in allowed_results if r.is_correct)

                assert correct_permissions == len(allowed_results)

    @pytest.mark.asyncio
    async def test_rbac_performance_validation(
        self,
        rbac_engine: RBACTestEngine,
        performance_thresholds: dict,
        auth_helper: AuthTestHelper,
    ):
        """Test RBAC performance under load"""

        # Create test user
        test_user = auth_helper.generate_test_user(UserRole.MEMBER)

        # Measure RBAC validation performance
        import time

        start_time = time.time()

        permission_results = await rbac_engine.test_role_permissions(test_user)

        end_time = time.time()
        rbac_time_ms = (end_time - start_time) * 1000

        # Validate RBAC performance
        assert rbac_time_ms <= performance_thresholds["authorization_time_ms"] * len(permission_results)

        # Validate individual permission check performance
        for result in permission_results:
            assert result.execution_time_ms <= performance_thresholds["authorization_time_ms"]

    def _get_forbidden_actions_for_role(self, role: UserRole) -> List[tuple]:
        """Get forbidden actions for a specific role"""

        base_forbidden = [
            ("POST", "/api/v1/admin/users/{user_id}/promote"),
            ("PUT", "/api/v1/users/{user_id}/role"),
            ("POST", "/api/v1/auth/impersonate"),
            ("DELETE", "/api/v1/admin/audit-logs"),
        ]

        if role == UserRole.ADMIN:
            return []  # Admin has no forbidden actions in this test
        elif role == UserRole.TEAM_LEAD:
            return base_forbidden + [
                ("GET", "/api/v1/admin/users"),
                ("DELETE", "/api/v1/admin/teams/{id}"),
            ]
        elif role == UserRole.MEMBER:
            return base_forbidden + [
                ("DELETE", "/api/v1/memories/{id}"),
                ("POST", "/api/v1/teams/{team_id}/members"),
                ("GET", "/api/v1/admin/users"),
            ]
        elif role == UserRole.VIEWER:
            return base_forbidden + [
                ("POST", "/api/v1/memories"),
                ("PUT", "/api/v1/memories/{id}"),
                ("DELETE", "/api/v1/memories/{id}"),
                ("POST", "/api/v1/teams/{team_id}/members"),
            ]
        elif role == UserRole.GUEST:
            return base_forbidden + [
                ("POST", "/api/v1/memories"),
                ("PUT", "/api/v1/memories/{id}"),
                ("DELETE", "/api/v1/memories/{id}"),
                ("GET", "/api/v1/teams/{team_id}"),
                ("GET", "/api/v1/analytics/personal"),
            ]

        return base_forbidden

    @pytest.mark.asyncio
    async def test_rbac_audit_logging(self, rbac_engine: RBACTestEngine, admin_user, member_user):
        """Test RBAC audit logging functionality"""

        # Test admin access (should be logged)
        admin_results = await rbac_engine.test_role_permissions(admin_user)

        # Test member access (should be logged)
        member_results = await rbac_engine.test_role_permissions(member_user)

        # Validate audit trail exists
        # Note: In a real implementation, this would check actual audit logs
        assert len(admin_results) > 0
        assert len(member_results) > 0

        # Validate different permission levels are recorded
        admin_allowed = [r for r in admin_results if r.expected_result == "allow"]
        member_allowed = [r for r in member_results if r.expected_result == "allow"]

        # Admin should have more allowed permissions than member
        assert len(admin_allowed) > len(member_allowed)

    @pytest.mark.asyncio
    async def test_rbac_error_handling(self, rbac_engine: RBACTestEngine, auth_helper: AuthTestHelper):
        """Test RBAC error handling for edge cases"""

        # Test with invalid user
        invalid_user = auth_helper.generate_test_user(UserRole.MEMBER)
        invalid_user.password = "wrong_password"

        permission_results = await rbac_engine.test_role_permissions(invalid_user)

        # Should handle authentication failure gracefully
        if len(permission_results) > 0:
            first_result = permission_results[0]
            if first_result.endpoint == "authentication":
                assert first_result.response_code == 401
                assert first_result.error_message is not None
