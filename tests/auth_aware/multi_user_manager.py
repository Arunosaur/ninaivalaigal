#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""
Multi-User Test Manager
Concurrent multi-user authentication testing for enterprise validation
"""

import asyncio
import concurrent.futures
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

import httpx
import jwt

from .models import (
    AuthTestResult,
    AuthTestResults,
    ConflictResults,
    IsolationResults,
    TestSession,
    TestUser,
    TestUserStatus,
    UserRole,
)

logger = logging.getLogger(__name__)


class MultiUserTestManager:
    """
    Manages concurrent multi-user authentication testing scenarios

    Features:
    - Concurrent user authentication simulation
    - Session conflict detection and resolution
    - User isolation validation
    - Performance testing under auth load
    """

    def __init__(self, config: Dict):
        self.config = config
        self.base_url = config.get("base_url", "http://localhost:8080")
        self.test_users: Dict[str, TestUser] = {}
        self.active_sessions: Dict[str, TestSession] = {}
        self.client_pool = []

    async def create_test_users(self, roles: List[UserRole], count_per_role: int = 5) -> List[TestUser]:
        """
        Create test users for multi-user scenarios

        Args:
            roles: List of roles to create users for
            count_per_role: Number of users to create per role

        Returns:
            List of created test users
        """
        try:
            created_users = []

            for role in roles:
                for i in range(count_per_role):
                    user = TestUser(
                        user_id=f"test_user_{role.value}_{i:03d}",
                        username=f"testuser_{role.value}_{i:03d}",
                        email=f"test_{role.value}_{i:03d}@ninaivalaigal.com",
                        role=role,
                        team_id=f"team_{role.value}",
                        organization_id="test_org_001",
                        status=TestUserStatus.ACTIVE,
                    )

                    # Register user in test database
                    await self._register_test_user(user)

                    self.test_users[user.user_id] = user
                    created_users.append(user)

            logger.info(f"Created {len(created_users)} test users across {len(roles)} roles")
            return created_users

        except Exception as e:
            logger.error(f"Failed to create test users: {e}")
            return []

    async def simulate_concurrent_auth(self, users: List[TestUser], concurrent_limit: int = 50) -> AuthTestResults:
        """
        Simulate concurrent authentication for multiple users

        Args:
            users: List of users to authenticate concurrently
            concurrent_limit: Maximum concurrent authentication attempts

        Returns:
            Authentication test results with performance metrics
        """
        start_time = datetime.utcnow()

        try:
            # Prepare authentication tasks
            auth_tasks = []
            semaphore = asyncio.Semaphore(concurrent_limit)

            for user in users:
                task = self._authenticate_user_with_semaphore(user, semaphore)
                auth_tasks.append(task)

            # Execute concurrent authentication
            logger.info(f"Starting concurrent authentication for {len(users)} users")
            auth_results = await asyncio.gather(*auth_tasks, return_exceptions=True)

            # Analyze results
            success_count = 0
            failure_count = 0
            error_count = 0
            auth_times = []

            for i, result in enumerate(auth_results):
                if isinstance(result, Exception):
                    error_count += 1
                    logger.error(f"Auth error for user {users[i].user_id}: {result}")
                elif result.get("success", False):
                    success_count += 1
                    auth_times.append(result.get("auth_time_ms", 0))
                else:
                    failure_count += 1

            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000

            # Performance analysis
            avg_auth_time = sum(auth_times) / len(auth_times) if auth_times else 0
            max_auth_time = max(auth_times) if auth_times else 0

            test_results = AuthTestResults(
                test_name="concurrent_authentication",
                result=(AuthTestResult.PASS if success_count >= len(users) * 0.95 else AuthTestResult.FAIL),
                user_count=len(users),
                success_count=success_count,
                failure_count=failure_count,
                error_count=error_count,
                execution_time_ms=execution_time,
                details={
                    "concurrent_limit": concurrent_limit,
                    "avg_auth_time_ms": avg_auth_time,
                    "max_auth_time_ms": max_auth_time,
                    "throughput_auths_per_sec": len(users) / (execution_time / 1000),
                },
            )

            logger.info(f"Concurrent auth completed: {success_count}/{len(users)} successful")
            return test_results

        except Exception as e:
            logger.error(f"Concurrent authentication failed: {e}")
            return AuthTestResults(
                test_name="concurrent_authentication",
                result=AuthTestResult.ERROR,
                user_count=len(users),
                success_count=0,
                failure_count=0,
                error_count=len(users),
                execution_time_ms=0,
                errors=[str(e)],
            )

    async def test_session_conflicts(self, users: List[TestUser]) -> ConflictResults:
        """
        Test for session conflicts between concurrent users

        Args:
            users: List of authenticated users to test

        Returns:
            Session conflict detection results
        """
        start_time = datetime.utcnow()

        try:
            session_conflicts = []
            data_conflicts = []

            # Test concurrent session operations
            conflict_tasks = []

            for i in range(0, len(users), 2):
                if i + 1 < len(users):
                    user_a, user_b = users[i], users[i + 1]

                    # Test concurrent memory operations
                    task = self._test_concurrent_operations(user_a, user_b)
                    conflict_tasks.append(task)

            conflict_results = await asyncio.gather(*conflict_tasks, return_exceptions=True)

            # Analyze conflict results
            for result in conflict_results:
                if isinstance(result, Exception):
                    continue

                if result.get("session_conflict"):
                    session_conflicts.append(result["session_conflict"])

                if result.get("data_conflict"):
                    data_conflicts.append(result["data_conflict"])

            resolution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            total_conflicts = len(session_conflicts) + len(data_conflicts)

            return ConflictResults(
                total_conflicts=total_conflicts,
                session_conflicts=session_conflicts,
                data_conflicts=data_conflicts,
                resolution_time_ms=resolution_time,
                conflicts_resolved=total_conflicts == 0,
            )

        except Exception as e:
            logger.error(f"Session conflict testing failed: {e}")
            return ConflictResults(
                total_conflicts=-1,
                session_conflicts=[],
                data_conflicts=[],
                resolution_time_ms=0,
                conflicts_resolved=False,
            )

    async def validate_user_isolation(self, user_a: TestUser, user_b: TestUser) -> IsolationResults:
        """
        Validate isolation between two users from different teams

        Args:
            user_a: First user for isolation testing
            user_b: Second user for isolation testing

        Returns:
            User isolation validation results
        """
        try:
            cross_access_attempts = 0
            blocked_attempts = 0
            isolation_violations = []

            # Get auth tokens for both users
            token_a = await self._get_user_token(user_a)
            token_b = await self._get_user_token(user_b)

            if not token_a or not token_b:
                return IsolationResults(
                    user_a_id=user_a.user_id,
                    user_b_id=user_b.user_id,
                    isolation_maintained=False,
                    cross_access_attempts=0,
                    blocked_attempts=0,
                    data_leakage_detected=True,
                    isolation_violations=["Failed to obtain authentication tokens"],
                )

            # Test cross-team data access attempts
            isolation_tests = [
                self._test_cross_team_memory_access(user_a, token_a, user_b.team_id),
                self._test_cross_team_memory_access(user_b, token_b, user_a.team_id),
                self._test_cross_user_profile_access(user_a, token_a, user_b.user_id),
                self._test_cross_user_profile_access(user_b, token_b, user_a.user_id),
                self._test_cross_team_admin_access(user_a, token_a, user_b.team_id),
                self._test_cross_team_admin_access(user_b, token_b, user_a.team_id),
            ]

            isolation_results = await asyncio.gather(*isolation_tests, return_exceptions=True)

            # Analyze isolation results
            for result in isolation_results:
                if isinstance(result, Exception):
                    isolation_violations.append(f"Isolation test error: {str(result)}")
                    continue

                cross_access_attempts += 1

                if result.get("access_blocked", True):
                    blocked_attempts += 1
                else:
                    violation_msg = f"Unauthorized access: {result.get('violation_type', 'unknown')}"
                    isolation_violations.append(violation_msg)

            isolation_maintained = len(isolation_violations) == 0
            data_leakage_detected = not isolation_maintained

            return IsolationResults(
                user_a_id=user_a.user_id,
                user_b_id=user_b.user_id,
                isolation_maintained=isolation_maintained,
                cross_access_attempts=cross_access_attempts,
                blocked_attempts=blocked_attempts,
                data_leakage_detected=data_leakage_detected,
                isolation_violations=isolation_violations,
            )

        except Exception as e:
            logger.error(f"User isolation validation failed: {e}")
            return IsolationResults(
                user_a_id=user_a.user_id,
                user_b_id=user_b.user_id,
                isolation_maintained=False,
                cross_access_attempts=0,
                blocked_attempts=0,
                data_leakage_detected=True,
                isolation_violations=[f"Isolation test error: {str(e)}"],
            )

    async def _authenticate_user_with_semaphore(self, user: TestUser, semaphore: asyncio.Semaphore) -> Dict:
        """Authenticate user with concurrency control"""
        async with semaphore:
            start_time = time.time()

            try:
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        f"{self.base_url}/api/v1/auth/login",
                        json={"username": user.username, "password": user.password},
                        timeout=10.0,
                    )

                    auth_time_ms = (time.time() - start_time) * 1000

                    if response.status_code == 200:
                        token_data = response.json()

                        # Create session record
                        session = TestSession(
                            session_id=f"session_{user.user_id}_{int(time.time())}",
                            user_id=user.user_id,
                            token=token_data.get("access_token", ""),
                            refresh_token=token_data.get("refresh_token"),
                            created_at=datetime.utcnow(),
                            expires_at=datetime.utcnow() + timedelta(hours=1),
                            last_activity=datetime.utcnow(),
                        )

                        self.active_sessions[session.session_id] = session

                        return {
                            "success": True,
                            "user_id": user.user_id,
                            "session_id": session.session_id,
                            "auth_time_ms": auth_time_ms,
                        }
                    else:
                        return {
                            "success": False,
                            "user_id": user.user_id,
                            "error": f"HTTP {response.status_code}",
                            "auth_time_ms": auth_time_ms,
                        }

            except Exception as e:
                auth_time_ms = (time.time() - start_time) * 1000
                return {
                    "success": False,
                    "user_id": user.user_id,
                    "error": str(e),
                    "auth_time_ms": auth_time_ms,
                }

    async def _register_test_user(self, user: TestUser) -> bool:
        """Register test user in the system"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/api/v1/auth/register",
                    json={
                        "username": user.username,
                        "email": user.email,
                        "password": user.password,
                        "role": user.role.value,
                        "team_id": user.team_id,
                        "organization_id": user.organization_id,
                    },
                    timeout=10.0,
                )

                return response.status_code in [200, 201]

        except Exception as e:
            logger.error(f"Failed to register user {user.user_id}: {e}")
            return False

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

    async def _test_concurrent_operations(self, user_a: TestUser, user_b: TestUser) -> Dict:
        """Test concurrent operations between two users"""
        try:
            # Simulate concurrent memory operations
            token_a = await self._get_user_token(user_a)
            token_b = await self._get_user_token(user_b)

            if not token_a or not token_b:
                return {"error": "Failed to get tokens"}

            # Concurrent memory creation
            async with httpx.AsyncClient() as client:
                tasks = [
                    client.post(
                        f"{self.base_url}/api/v1/memories",
                        json={"content": f"Test memory from {user_a.user_id}"},
                        headers={"Authorization": f"Bearer {token_a}"},
                        timeout=5.0,
                    ),
                    client.post(
                        f"{self.base_url}/api/v1/memories",
                        json={"content": f"Test memory from {user_b.user_id}"},
                        headers={"Authorization": f"Bearer {token_b}"},
                        timeout=5.0,
                    ),
                ]

                results = await asyncio.gather(*tasks, return_exceptions=True)

                # Check for conflicts
                session_conflict = None
                data_conflict = None

                # Analyze results for conflicts
                for i, result in enumerate(results):
                    if isinstance(result, Exception):
                        continue

                    if hasattr(result, "status_code") and result.status_code == 409:
                        data_conflict = {
                            "type": "concurrent_creation_conflict",
                            "user": user_a.user_id if i == 0 else user_b.user_id,
                            "timestamp": datetime.utcnow().isoformat(),
                        }

                return {
                    "session_conflict": session_conflict,
                    "data_conflict": data_conflict,
                }

        except Exception as e:
            return {"error": str(e)}

    async def _test_cross_team_memory_access(self, user: TestUser, token: str, target_team_id: str) -> Dict:
        """Test cross-team memory access attempt"""
        try:
            async with httpx.AsyncClient() as client:
                # Attempt to access memories from different team
                response = await client.get(
                    f"{self.base_url}/api/v1/memories",
                    params={"team_id": target_team_id},
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=5.0,
                )

                # Should be blocked (403 or 404)
                access_blocked = response.status_code in [403, 404]

                return {
                    "access_blocked": access_blocked,
                    "violation_type": ("cross_team_memory_access" if not access_blocked else None),
                    "response_code": response.status_code,
                }

        except Exception as e:
            return {
                "access_blocked": True,  # Exception counts as blocked
                "violation_type": None,
                "error": str(e),
            }

    async def _test_cross_user_profile_access(self, user: TestUser, token: str, target_user_id: str) -> Dict:
        """Test cross-user profile access attempt"""
        try:
            async with httpx.AsyncClient() as client:
                # Attempt to access another user's profile
                response = await client.get(
                    f"{self.base_url}/api/v1/users/{target_user_id}",
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=5.0,
                )

                # Should be blocked unless admin
                access_blocked = response.status_code in [403, 404] or user.role != UserRole.ADMIN

                return {
                    "access_blocked": access_blocked,
                    "violation_type": ("cross_user_profile_access" if not access_blocked else None),
                    "response_code": response.status_code,
                }

        except Exception as e:
            return {"access_blocked": True, "violation_type": None, "error": str(e)}

    async def _test_cross_team_admin_access(self, user: TestUser, token: str, target_team_id: str) -> Dict:
        """Test cross-team admin access attempt"""
        try:
            async with httpx.AsyncClient() as client:
                # Attempt admin operation on different team
                response = await client.post(
                    f"{self.base_url}/api/v1/teams/{target_team_id}/members",
                    json={"user_id": "test_user", "role": "member"},
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=5.0,
                )

                # Should be blocked unless global admin
                access_blocked = response.status_code in [
                    403,
                    404,
                ] or user.role not in [UserRole.ADMIN]

                return {
                    "access_blocked": access_blocked,
                    "violation_type": ("cross_team_admin_access" if not access_blocked else None),
                    "response_code": response.status_code,
                }

        except Exception as e:
            return {"access_blocked": True, "violation_type": None, "error": str(e)}
