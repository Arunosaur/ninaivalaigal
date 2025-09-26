"""
Complete Authentication Flow E2E Tests
Tests the entire auth flow from login to protected resource access
Critical for Phase 1 production readiness
"""

import pytest
import httpx
import asyncio
from typing import Dict, Any
import json
import time


class TestCompleteAuthFlow:
    """Test complete authentication flow end-to-end"""
    
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.test_user = {
            "email": "test@example.com",
            "password": "testpassword123",
            "role": "user",
            "team_id": 1
        }
        self.admin_user = {
            "email": "admin@example.com", 
            "password": "adminpassword123",
            "role": "team_admin",
            "team_id": 1
        }
        self.jwt_token = None
        self.admin_jwt_token = None

    @pytest.fixture(autouse=True)
    async def setup_and_teardown(self):
        """Setup test environment before each test"""
        # Setup
        await self.ensure_test_users_exist()
        yield
        # Teardown - cleanup if needed
        pass

    async def ensure_test_users_exist(self):
        """Ensure test users exist in the system"""
        async with httpx.AsyncClient() as client:
            # Try to register test users (may fail if they already exist)
            try:
                await client.get(
                    f"{self.base_url}/auth-working/register",
                    params={
                        "email": self.test_user["email"],
                        "password": self.test_user["password"],
                        "role": self.test_user["role"]
                    }
                )
            except:
                pass  # User might already exist
                
            try:
                await client.get(
                    f"{self.base_url}/auth-working/register", 
                    params={
                        "email": self.admin_user["email"],
                        "password": self.admin_user["password"],
                        "role": self.admin_user["role"]
                    }
                )
            except:
                pass  # User might already exist

    async def test_01_user_login_success(self):
        """Test successful user login and JWT token generation"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/auth-working/login",
                params={
                    "email": self.test_user["email"],
                    "password": self.test_user["password"]
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            
            # Validate response structure
            assert "jwt_token" in data
            assert "user_id" in data
            assert "email" in data
            assert data["email"] == self.test_user["email"]
            
            # Store token for subsequent tests
            self.jwt_token = data["jwt_token"]
            
            # Validate JWT token format
            assert len(self.jwt_token.split('.')) == 3  # JWT has 3 parts
            
    async def test_02_admin_login_success(self):
        """Test admin user login"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/auth-working/login",
                params={
                    "email": self.admin_user["email"],
                    "password": self.admin_user["password"]
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            
            assert "jwt_token" in data
            assert data["email"] == self.admin_user["email"]
            
            self.admin_jwt_token = data["jwt_token"]

    async def test_03_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/auth-working/login",
                params={
                    "email": "invalid@example.com",
                    "password": "wrongpassword"
                }
            )
            
            assert response.status_code == 401
            data = response.json()
            assert "detail" in data

    async def test_04_protected_route_with_valid_token(self):
        """Test accessing protected route with valid JWT token"""
        if not self.jwt_token:
            await self.test_01_user_login_success()
            
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/protected-routes/profile",
                headers={"Authorization": f"Bearer {self.jwt_token}"}
            )
            
            assert response.status_code == 200
            data = response.json()
            
            # Validate user profile data
            assert "user_id" in data
            assert "email" in data
            assert data["email"] == self.test_user["email"]

    async def test_05_protected_route_without_token(self):
        """Test accessing protected route without token"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/protected-routes/profile"
            )
            
            assert response.status_code == 401
            data = response.json()
            assert "detail" in data

    async def test_06_protected_route_with_invalid_token(self):
        """Test accessing protected route with invalid token"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/protected-routes/profile",
                headers={"Authorization": "Bearer invalid.jwt.token"}
            )
            
            assert response.status_code == 401
            data = response.json()
            assert "detail" in data

    async def test_07_memory_creation_with_auth(self):
        """Test memory creation requires authentication"""
        if not self.jwt_token:
            await self.test_01_user_login_success()
            
        async with httpx.AsyncClient() as client:
            # Test with authentication
            response = await client.get(
                f"{self.base_url}/memory-system/add",
                headers={"Authorization": f"Bearer {self.jwt_token}"},
                params={
                    "content": "Test memory for auth validation",
                    "tags": "test,auth",
                    "context_id": 1
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "memory_id" in data or "success" in data

    async def test_08_memory_creation_without_auth(self):
        """Test memory creation fails without authentication"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/memory-system/add",
                params={
                    "content": "Unauthorized memory creation attempt",
                    "tags": "test"
                }
            )
            
            assert response.status_code == 401
            data = response.json()
            assert "detail" in data

    async def test_09_approval_workflow_with_auth(self):
        """Test approval workflow requires authentication"""
        if not self.jwt_token:
            await self.test_01_user_login_success()
            
        async with httpx.AsyncClient() as client:
            # First create a memory to approve
            memory_response = await client.get(
                f"{self.base_url}/memory-system/add",
                headers={"Authorization": f"Bearer {self.jwt_token}"},
                params={
                    "content": "Memory for approval test",
                    "tags": "test,approval"
                }
            )
            
            assert memory_response.status_code == 200
            
            # Then submit for approval
            response = await client.get(
                f"{self.base_url}/approval-workflows/submit",
                headers={"Authorization": f"Bearer {self.jwt_token}"},
                params={
                    "memory_id": 1,
                    "submission_note": "Please review this memory"
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "approval_id" in data or "success" in data

    async def test_10_approval_workflow_without_auth(self):
        """Test approval workflow fails without authentication"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/approval-workflows/submit",
                params={
                    "memory_id": 1,
                    "submission_note": "Unauthorized approval attempt"
                }
            )
            
            assert response.status_code == 401

    async def test_11_discussion_comments_with_auth(self):
        """Test discussion comments require authentication"""
        if not self.jwt_token:
            await self.test_01_user_login_success()
            
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/comments/add",
                headers={"Authorization": f"Bearer {self.jwt_token}"},
                params={
                    "mem_id": 1,
                    "text": "Great insight! Very helpful.",
                    "comment_type": "feedback"
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "success" in data or "comment_id" in data

    async def test_12_discussion_comments_without_auth(self):
        """Test discussion comments fail without authentication"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/comments/add",
                params={
                    "mem_id": 1,
                    "text": "Unauthorized comment attempt"
                }
            )
            
            assert response.status_code == 401

    async def test_13_ai_intelligence_with_auth(self):
        """Test AI intelligence endpoints require authentication"""
        if not self.jwt_token:
            await self.test_01_user_login_success()
            
        async with httpx.AsyncClient() as client:
            # Test PageRank memories
            response = await client.get(
                f"{self.base_url}/graph-rank/memories",
                headers={"Authorization": f"Bearer {self.jwt_token}"},
                params={"limit": 5}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "ranked_memories" in data or "success" in data

    async def test_14_ai_intelligence_without_auth(self):
        """Test AI intelligence fails without authentication"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/graph-rank/memories",
                params={"limit": 5}
            )
            
            assert response.status_code == 401

    async def test_15_team_management_with_auth(self):
        """Test team management requires authentication"""
        if not self.jwt_token:
            await self.test_01_user_login_success()
            
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/teams-working/team/1",
                headers={"Authorization": f"Bearer {self.jwt_token}"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "team" in data or "success" in data

    async def test_16_team_management_without_auth(self):
        """Test team management fails without authentication"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/teams-working/team/1"
            )
            
            assert response.status_code == 401

    async def test_17_rbac_admin_only_operations(self):
        """Test RBAC - admin-only operations"""
        if not self.admin_jwt_token:
            await self.test_02_admin_login_success()
            
        async with httpx.AsyncClient() as client:
            # Test admin operation with admin token
            response = await client.get(
                f"{self.base_url}/teams-working/create",
                headers={"Authorization": f"Bearer {self.admin_jwt_token}"},
                params={
                    "name": "Test Team",
                    "description": "RBAC test team"
                }
            )
            
            # Should succeed for admin (or return appropriate response)
            assert response.status_code in [200, 201, 409]  # 409 if team exists

    async def test_18_rbac_regular_user_admin_operation(self):
        """Test RBAC - regular user cannot perform admin operations"""
        if not self.jwt_token:
            await self.test_01_user_login_success()
            
        async with httpx.AsyncClient() as client:
            # Test admin operation with regular user token
            response = await client.get(
                f"{self.base_url}/teams-working/create",
                headers={"Authorization": f"Bearer {self.jwt_token}"},
                params={
                    "name": "Unauthorized Team",
                    "description": "Should fail"
                }
            )
            
            # Should fail for regular user
            assert response.status_code in [403, 401]

    async def test_19_token_expiration_handling(self):
        """Test handling of expired tokens"""
        # This would require a short-lived token or time manipulation
        # For now, test with a malformed token that simulates expiration
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/protected-routes/profile",
                headers={"Authorization": "Bearer expired.token.here"}
            )
            
            assert response.status_code == 401
            data = response.json()
            assert "detail" in data

    async def test_20_concurrent_auth_requests(self):
        """Test concurrent authentication requests"""
        if not self.jwt_token:
            await self.test_01_user_login_success()
            
        async with httpx.AsyncClient() as client:
            # Make multiple concurrent requests with the same token
            tasks = []
            for i in range(5):
                task = client.get(
                    f"{self.base_url}/protected-routes/profile",
                    headers={"Authorization": f"Bearer {self.jwt_token}"}
                )
                tasks.append(task)
            
            responses = await asyncio.gather(*tasks)
            
            # All should succeed
            for response in responses:
                assert response.status_code == 200

    async def test_21_malformed_auth_headers(self):
        """Test various malformed authorization headers"""
        test_cases = [
            "",  # Empty
            "Bearer",  # Missing token
            "Basic dGVzdA==",  # Wrong auth type
            "Bearer ",  # Empty token
            "bearer token",  # Wrong case
            "Bearer token with spaces",  # Invalid token format
        ]
        
        async with httpx.AsyncClient() as client:
            for auth_header in test_cases:
                headers = {"Authorization": auth_header} if auth_header else {}
                
                response = await client.get(
                    f"{self.base_url}/protected-routes/profile",
                    headers=headers
                )
                
                assert response.status_code == 401, f"Failed for header: {auth_header}"

    async def test_22_cross_team_access_control(self):
        """Test that users can only access their team's data"""
        if not self.jwt_token:
            await self.test_01_user_login_success()
            
        async with httpx.AsyncClient() as client:
            # Try to access data from a different team
            response = await client.get(
                f"{self.base_url}/memory-system/memories",
                headers={"Authorization": f"Bearer {self.jwt_token}"},
                params={"team_filter": 999}  # Non-existent team
            )
            
            # Should return empty results or access denied
            assert response.status_code in [200, 403]
            
            if response.status_code == 200:
                data = response.json()
                # Should have no memories or filtered results
                assert len(data.get("memories", [])) == 0

    async def test_23_sql_injection_protection(self):
        """Test protection against SQL injection in auth parameters"""
        if not self.jwt_token:
            await self.test_01_user_login_success()
            
        async with httpx.AsyncClient() as client:
            # Try SQL injection in team filter
            response = await client.get(
                f"{self.base_url}/memory-system/memories",
                headers={"Authorization": f"Bearer {self.jwt_token}"},
                params={"team_filter": "1'; DROP TABLE users; --"}
            )
            
            # Should handle safely without server error
            assert response.status_code in [200, 400, 422]

    async def test_24_auth_performance_benchmark(self):
        """Benchmark authentication performance"""
        if not self.jwt_token:
            await self.test_01_user_login_success()
            
        async with httpx.AsyncClient() as client:
            # Measure auth overhead
            start_time = time.time()
            
            for _ in range(10):
                response = await client.get(
                    f"{self.base_url}/protected-routes/profile",
                    headers={"Authorization": f"Bearer {self.jwt_token}"}
                )
                assert response.status_code == 200
            
            end_time = time.time()
            avg_time = (end_time - start_time) / 10
            
            # Auth should be fast (< 100ms per request)
            assert avg_time < 0.1, f"Auth too slow: {avg_time:.3f}s per request"

    async def test_25_complete_workflow_integration(self):
        """Test complete workflow: login -> create -> approve -> discuss -> analyze"""
        if not self.jwt_token:
            await self.test_01_user_login_success()
            
        async with httpx.AsyncClient() as client:
            # 1. Create memory
            memory_response = await client.get(
                f"{self.base_url}/memory-system/add",
                headers={"Authorization": f"Bearer {self.jwt_token}"},
                params={
                    "content": "Complete workflow test memory",
                    "tags": "test,workflow,integration"
                }
            )
            assert memory_response.status_code == 200
            
            # 2. Submit for approval
            approval_response = await client.get(
                f"{self.base_url}/approval-workflows/submit",
                headers={"Authorization": f"Bearer {self.jwt_token}"},
                params={
                    "memory_id": 1,
                    "submission_note": "Complete workflow test"
                }
            )
            assert approval_response.status_code == 200
            
            # 3. Add discussion comment
            comment_response = await client.get(
                f"{self.base_url}/comments/add",
                headers={"Authorization": f"Bearer {self.jwt_token}"},
                params={
                    "mem_id": 1,
                    "text": "This workflow test is working perfectly!",
                    "comment_type": "feedback"
                }
            )
            assert comment_response.status_code == 200
            
            # 4. Get AI analysis
            ai_response = await client.get(
                f"{self.base_url}/graph-rank/memories",
                headers={"Authorization": f"Bearer {self.jwt_token}"},
                params={"limit": 5, "include_scores": True}
            )
            assert ai_response.status_code == 200
            
            # 5. Get tag suggestions
            tag_response = await client.get(
                f"{self.base_url}/tag-suggester/suggest",
                headers={"Authorization": f"Bearer {self.jwt_token}"},
                params={"content": "Complete workflow test memory"}
            )
            assert tag_response.status_code == 200


# Run the tests
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
