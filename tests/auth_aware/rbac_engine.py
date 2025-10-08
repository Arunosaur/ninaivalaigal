"""
RBAC Test Engine
Role-based access control validation for enterprise security testing
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple

import httpx

from .models import (AuthTestResult, AuthTestResults, PermissionTestResult,
                     TestUser, TestUserStatus, UserRole)

logger = logging.getLogger(__name__)


class RBACTestEngine:
    """
    Comprehensive RBAC testing engine for enterprise validation

    Features:
    - Role permission matrix validation
    - Permission boundary testing
    - Role switching validation
    - Cross-team access control testing
    """

    def __init__(self, config: Dict):
        self.config = config
        self.base_url = config.get("base_url", "http://localhost:8080")

        # Define role permission matrix based on your execution plan
        self.role_permissions = {
            UserRole.ADMIN: {
                "endpoints": [
                    ("GET", "/api/v1/admin/users"),
                    ("POST", "/api/v1/admin/users"),
                    ("PUT", "/api/v1/admin/users/{id}"),
                    ("DELETE", "/api/v1/admin/users/{id}"),
                    ("GET", "/api/v1/admin/teams"),
                    ("POST", "/api/v1/admin/teams"),
                    ("DELETE", "/api/v1/admin/teams/{id}"),
                    ("GET", "/api/v1/memories"),
                    ("POST", "/api/v1/memories"),
                    ("PUT", "/api/v1/memories/{id}"),
                    ("DELETE", "/api/v1/memories/{id}"),
                    ("GET", "/api/v1/analytics/admin"),
                    ("GET", "/api/v1/billing/admin"),
                ],
                "expected_codes": [200, 201, 204],
            },
            UserRole.TEAM_LEAD: {
                "endpoints": [
                    ("GET", "/api/v1/teams/{team_id}/members"),
                    ("POST", "/api/v1/teams/{team_id}/members"),
                    ("PUT", "/api/v1/teams/{team_id}/members/{id}"),
                    ("DELETE", "/api/v1/teams/{team_id}/members/{id}"),
                    ("GET", "/api/v1/memories"),
                    ("POST", "/api/v1/memories"),
                    ("PUT", "/api/v1/memories/{id}"),
                    ("DELETE", "/api/v1/memories/{id}"),
                    ("GET", "/api/v1/analytics/team"),
                ],
                "expected_codes": [200, 201, 204],
                "forbidden_endpoints": [
                    ("GET", "/api/v1/admin/users"),
                    ("DELETE", "/api/v1/admin/teams/{id}"),
                    ("GET", "/api/v1/billing/admin"),
                ],
            },
            UserRole.MEMBER: {
                "endpoints": [
                    ("GET", "/api/v1/teams/{team_id}"),
                    ("GET", "/api/v1/memories"),
                    ("POST", "/api/v1/memories"),
                    ("PUT", "/api/v1/memories/{id}"),
                    ("GET", "/api/v1/analytics/personal"),
                ],
                "expected_codes": [200, 201],
                "forbidden_endpoints": [
                    ("DELETE", "/api/v1/memories/{id}"),
                    ("POST", "/api/v1/teams/{team_id}/members"),
                    ("GET", "/api/v1/admin/users"),
                    ("GET", "/api/v1/billing/admin"),
                ],
            },
            UserRole.VIEWER: {
                "endpoints": [
                    ("GET", "/api/v1/teams/{team_id}"),
                    ("GET", "/api/v1/memories"),
                    ("GET", "/api/v1/analytics/personal"),
                ],
                "expected_codes": [200],
                "forbidden_endpoints": [
                    ("POST", "/api/v1/memories"),
                    ("PUT", "/api/v1/memories/{id}"),
                    ("DELETE", "/api/v1/memories/{id}"),
                    ("POST", "/api/v1/teams/{team_id}/members"),
                    ("GET", "/api/v1/admin/users"),
                ],
            },
            UserRole.GUEST: {
                "endpoints": [("GET", "/api/v1/memories")],
                "expected_codes": [200],
                "forbidden_endpoints": [
                    ("POST", "/api/v1/memories"),
                    ("PUT", "/api/v1/memories/{id}"),
                    ("DELETE", "/api/v1/memories/{id}"),
                    ("GET", "/api/v1/teams/{team_id}"),
                    ("GET", "/api/v1/admin/users"),
                    ("GET", "/api/v1/analytics/personal"),
                ],
            },
        }

    async def test_role_permissions(
        self, user: TestUser, endpoints: Optional[List[Tuple[str, str]]] = None
    ) -> List[PermissionTestResult]:
        """
        Test role permissions against defined endpoint matrix

        Args:
            user: Test user with specific role
            endpoints: Optional specific endpoints to test (uses role matrix if None)

        Returns:
            List of permission test results for each endpoint
        """
        try:
            # Get user token
            token = await self._get_user_token(user)
            if not token:
                return [
                    PermissionTestResult(
                        endpoint="authentication",
                        method="POST",
                        user_role=user.role,
                        expected_result="allow",
                        actual_result="deny",
                        response_code=401,
                        execution_time_ms=0,
                        error_message="Failed to obtain authentication token",
                    )
                ]

            # Get endpoints to test
            if endpoints is None:
                role_config = self.role_permissions.get(user.role, {})
                endpoints = role_config.get("endpoints", [])

            # Test each endpoint
            permission_results = []

            for method, endpoint_template in endpoints:
                # Replace template variables
                endpoint = self._resolve_endpoint_template(endpoint_template, user)

                result = await self._test_endpoint_permission(
                    user, token, method, endpoint, expected_result="allow"
                )
                permission_results.append(result)

            # Test forbidden endpoints
            role_config = self.role_permissions.get(user.role, {})
            forbidden_endpoints = role_config.get("forbidden_endpoints", [])

            for method, endpoint_template in forbidden_endpoints:
                endpoint = self._resolve_endpoint_template(endpoint_template, user)

                result = await self._test_endpoint_permission(
                    user, token, method, endpoint, expected_result="deny"
                )
                permission_results.append(result)

            logger.info(
                f"Tested {len(permission_results)} permissions for role {user.role.value}"
            )
            return permission_results

        except Exception as e:
            logger.error(f"Role permission testing failed: {e}")
            return [
                PermissionTestResult(
                    endpoint="error",
                    method="ERROR",
                    user_role=user.role,
                    expected_result="allow",
                    actual_result="error",
                    response_code=500,
                    execution_time_ms=0,
                    error_message=str(e),
                )
            ]

    async def test_permission_boundaries(
        self, user: TestUser, forbidden_actions: List[Tuple[str, str]]
    ) -> List[PermissionTestResult]:
        """
        Test permission boundaries by attempting forbidden actions

        Args:
            user: Test user to test boundaries for
            forbidden_actions: List of (method, endpoint) tuples that should be forbidden

        Returns:
            List of boundary test results
        """
        try:
            token = await self._get_user_token(user)
            if not token:
                return []

            boundary_results = []

            for method, endpoint_template in forbidden_actions:
                endpoint = self._resolve_endpoint_template(endpoint_template, user)

                result = await self._test_endpoint_permission(
                    user, token, method, endpoint, expected_result="deny"
                )
                boundary_results.append(result)

            # Test privilege escalation attempts
            escalation_attempts = [
                ("POST", "/api/v1/admin/users/{user_id}/promote"),
                ("PUT", "/api/v1/users/{user_id}/role"),
                ("POST", "/api/v1/auth/impersonate"),
                ("DELETE", "/api/v1/admin/audit-logs"),
            ]

            for method, endpoint_template in escalation_attempts:
                endpoint = self._resolve_endpoint_template(endpoint_template, user)

                result = await self._test_privilege_escalation_attempt(
                    user, token, method, endpoint
                )
                boundary_results.append(result)

            logger.info(
                f"Tested {len(boundary_results)} permission boundaries for {user.role.value}"
            )
            return boundary_results

        except Exception as e:
            logger.error(f"Permission boundary testing failed: {e}")
            return []

    async def test_role_switching(
        self, user: TestUser, target_role: UserRole
    ) -> AuthTestResults:
        """
        Test role switching functionality and validation

        Args:
            user: User attempting role switch
            target_role: Target role to switch to

        Returns:
            Role switching test results
        """
        start_time = datetime.utcnow()

        try:
            # Get initial token
            initial_token = await self._get_user_token(user)
            if not initial_token:
                return AuthTestResults(
                    test_name="role_switching",
                    result=AuthTestResult.ERROR,
                    user_count=1,
                    success_count=0,
                    failure_count=1,
                    error_count=0,
                    execution_time_ms=0,
                    errors=["Failed to obtain initial token"],
                )

            # Attempt role switch
            switch_success = await self._attempt_role_switch(
                user, initial_token, target_role
            )

            # Validate new permissions if switch was successful
            validation_results = []
            if switch_success:
                # Test that new role permissions are active
                new_token = await self._get_user_token(user)
                if new_token:
                    validation_results = await self._validate_role_permissions(
                        user, new_token, target_role
                    )

            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000

            # Determine if role switching should be allowed
            switch_allowed = self._is_role_switch_allowed(user.role, target_role)

            success = switch_success == switch_allowed

            return AuthTestResults(
                test_name="role_switching",
                result=AuthTestResult.PASS if success else AuthTestResult.FAIL,
                user_count=1,
                success_count=1 if success else 0,
                failure_count=0 if success else 1,
                error_count=0,
                execution_time_ms=execution_time,
                details={
                    "initial_role": user.role.value,
                    "target_role": target_role.value,
                    "switch_allowed": switch_allowed,
                    "switch_successful": switch_success,
                    "permissions_validated": len(validation_results),
                    "validation_results": validation_results,
                },
            )

        except Exception as e:
            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            logger.error(f"Role switching test failed: {e}")

            return AuthTestResults(
                test_name="role_switching",
                result=AuthTestResult.ERROR,
                user_count=1,
                success_count=0,
                failure_count=0,
                error_count=1,
                execution_time_ms=execution_time,
                errors=[str(e)],
            )

    async def validate_cross_team_access(
        self, user: TestUser, target_team_id: str
    ) -> List[PermissionTestResult]:
        """
        Validate cross-team access controls

        Args:
            user: User attempting cross-team access
            target_team_id: Target team ID to access

        Returns:
            List of cross-team access test results
        """
        try:
            token = await self._get_user_token(user)
            if not token:
                return []

            cross_team_results = []

            # Test cross-team data access
            cross_team_endpoints = [
                ("GET", f"/api/v1/teams/{target_team_id}/memories"),
                ("POST", f"/api/v1/teams/{target_team_id}/memories"),
                ("GET", f"/api/v1/teams/{target_team_id}/analytics"),
                ("GET", f"/api/v1/teams/{target_team_id}/members"),
                ("POST", f"/api/v1/teams/{target_team_id}/members"),
                ("DELETE", f"/api/v1/teams/{target_team_id}/members/{{user_id}}"),
            ]

            for method, endpoint in cross_team_endpoints:
                # Determine expected result based on user role and team relationship
                expected_result = self._determine_cross_team_access_expectation(
                    user, target_team_id, method, endpoint
                )

                result = await self._test_endpoint_permission(
                    user, token, method, endpoint, expected_result
                )
                cross_team_results.append(result)

            logger.info(f"Tested {len(cross_team_results)} cross-team access scenarios")
            return cross_team_results

        except Exception as e:
            logger.error(f"Cross-team access validation failed: {e}")
            return []

    async def _get_user_token(self, user: TestUser) -> Optional[str]:
        """Get authentication token for user"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/api/v1/auth/login",
                    json={"username": user.username, "password": user.password},
                    timeout=10.0,
                )

                if response.status_code == 200:
                    token_data = response.json()
                    return token_data.get("access_token")

                return None

        except Exception as e:
            logger.error(f"Failed to get token for user {user.user_id}: {e}")
            return None

    async def _test_endpoint_permission(
        self,
        user: TestUser,
        token: str,
        method: str,
        endpoint: str,
        expected_result: str,
    ) -> PermissionTestResult:
        """Test permission for a specific endpoint"""
        start_time = datetime.utcnow()

        try:
            async with httpx.AsyncClient() as client:
                headers = {"Authorization": f"Bearer {token}"}

                # Prepare request based on method
                if method == "GET":
                    response = await client.get(
                        f"{self.base_url}{endpoint}", headers=headers, timeout=5.0
                    )
                elif method == "POST":
                    response = await client.post(
                        f"{self.base_url}{endpoint}",
                        json={"test": "data"},
                        headers=headers,
                        timeout=5.0,
                    )
                elif method == "PUT":
                    response = await client.put(
                        f"{self.base_url}{endpoint}",
                        json={"test": "data"},
                        headers=headers,
                        timeout=5.0,
                    )
                elif method == "DELETE":
                    response = await client.delete(
                        f"{self.base_url}{endpoint}", headers=headers, timeout=5.0
                    )
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")

                execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000

                # Determine actual result
                if response.status_code in [200, 201, 204]:
                    actual_result = "allow"
                elif response.status_code in [401, 403, 404]:
                    actual_result = "deny"
                else:
                    actual_result = "error"

                return PermissionTestResult(
                    endpoint=endpoint,
                    method=method,
                    user_role=user.role,
                    expected_result=expected_result,
                    actual_result=actual_result,
                    response_code=response.status_code,
                    execution_time_ms=execution_time,
                )

        except Exception as e:
            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000

            return PermissionTestResult(
                endpoint=endpoint,
                method=method,
                user_role=user.role,
                expected_result=expected_result,
                actual_result="error",
                response_code=500,
                execution_time_ms=execution_time,
                error_message=str(e),
            )

    async def _test_privilege_escalation_attempt(
        self, user: TestUser, token: str, method: str, endpoint: str
    ) -> PermissionTestResult:
        """Test privilege escalation attempt"""
        return await self._test_endpoint_permission(
            user, token, method, endpoint, expected_result="deny"
        )

    async def _attempt_role_switch(
        self, user: TestUser, token: str, target_role: UserRole
    ) -> bool:
        """Attempt to switch user role"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.put(
                    f"{self.base_url}/api/v1/users/{user.user_id}/role",
                    json={"role": target_role.value},
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=5.0,
                )

                return response.status_code in [200, 204]

        except Exception as e:
            logger.error(f"Role switch attempt failed: {e}")
            return False

    async def _validate_role_permissions(
        self, user: TestUser, token: str, role: UserRole
    ) -> List[Dict]:
        """Validate permissions for a specific role"""
        try:
            role_config = self.role_permissions.get(role, {})
            test_endpoints = role_config.get("endpoints", [])[
                :3
            ]  # Test first 3 for validation

            validation_results = []

            for method, endpoint_template in test_endpoints:
                endpoint = self._resolve_endpoint_template(endpoint_template, user)

                result = await self._test_endpoint_permission(
                    user, token, method, endpoint, expected_result="allow"
                )

                validation_results.append(
                    {
                        "endpoint": endpoint,
                        "method": method,
                        "correct": result.is_correct,
                    }
                )

            return validation_results

        except Exception as e:
            logger.error(f"Role permission validation failed: {e}")
            return []

    def _resolve_endpoint_template(self, template: str, user: TestUser) -> str:
        """Resolve endpoint template variables"""
        return template.format(
            id=user.user_id, user_id=user.user_id, team_id=user.team_id
        )

    def _is_role_switch_allowed(
        self, current_role: UserRole, target_role: UserRole
    ) -> bool:
        """Determine if role switching should be allowed"""
        # Define role switching rules
        allowed_switches = {
            UserRole.ADMIN: [UserRole.TEAM_LEAD, UserRole.MEMBER, UserRole.VIEWER],
            UserRole.TEAM_LEAD: [UserRole.MEMBER, UserRole.VIEWER],
            UserRole.MEMBER: [UserRole.VIEWER],
            UserRole.VIEWER: [],
            UserRole.GUEST: [],
        }

        return target_role in allowed_switches.get(current_role, [])

    def _determine_cross_team_access_expectation(
        self, user: TestUser, target_team_id: str, method: str, endpoint: str
    ) -> str:
        """Determine expected result for cross-team access"""
        # Admin can access all teams
        if user.role == UserRole.ADMIN:
            return "allow"

        # Users cannot access other teams (except read-only for some roles)
        if user.team_id != target_team_id:
            if method == "GET" and user.role in [UserRole.TEAM_LEAD, UserRole.MEMBER]:
                # Limited read access might be allowed
                return "allow" if "memories" in endpoint else "deny"
            else:
                return "deny"

        # Same team access follows normal role permissions
        return "allow"
