"""
Auth-Aware Testing Infrastructure
Comprehensive testing framework for authentication, authorization, and role-based access control
"""

import asyncio
import json
import pytest
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from unittest.mock import Mock, patch
import jwt
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Import our application components
from server.main import app
from server.auth import create_access_token, verify_token, get_current_user
from server.database import User, Team, get_db
from server.models.standalone_teams import StandaloneTeamManager, TeamMembership


class AuthTestFramework:
    """Comprehensive authentication testing framework"""
    
    def __init__(self, test_db_url: str = "sqlite:///./test_auth.db"):
        self.test_db_url = test_db_url
        self.engine = create_engine(test_db_url, connect_args={"check_same_thread": False})
        self.TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.client = TestClient(app)
        self.test_users = {}
        self.test_teams = {}
        self.test_tokens = {}
        
    def setup_test_database(self):
        """Initialize test database with sample data"""
        # Create test users with different roles
        self.test_users = {
            "admin": {
                "id": "user-admin-001",
                "email": "admin@ninaivalaigal.com",
                "name": "Admin User",
                "role": "admin",
                "is_active": True,
                "created_at": datetime.utcnow()
            },
            "team_owner": {
                "id": "user-owner-001", 
                "email": "owner@company.com",
                "name": "Team Owner",
                "role": "user",
                "is_active": True,
                "created_at": datetime.utcnow()
            },
            "team_member": {
                "id": "user-member-001",
                "email": "member@company.com", 
                "name": "Team Member",
                "role": "user",
                "is_active": True,
                "created_at": datetime.utcnow()
            },
            "guest_user": {
                "id": "user-guest-001",
                "email": "guest@external.com",
                "name": "Guest User", 
                "role": "guest",
                "is_active": True,
                "created_at": datetime.utcnow()
            },
            "inactive_user": {
                "id": "user-inactive-001",
                "email": "inactive@company.com",
                "name": "Inactive User",
                "role": "user", 
                "is_active": False,
                "created_at": datetime.utcnow() - timedelta(days=30)
            }
        }
        
        # Create test teams with different configurations
        self.test_teams = {
            "enterprise_team": {
                "id": "team-enterprise-001",
                "name": "Enterprise Team",
                "plan": "enterprise",
                "owner_id": "user-owner-001",
                "is_standalone": True,
                "created_at": datetime.utcnow(),
                "members": ["user-owner-001", "user-member-001"]
            },
            "pro_team": {
                "id": "team-pro-001", 
                "name": "Pro Team",
                "plan": "pro",
                "owner_id": "user-owner-001",
                "is_standalone": True,
                "created_at": datetime.utcnow(),
                "members": ["user-owner-001"]
            },
            "free_team": {
                "id": "team-free-001",
                "name": "Free Team", 
                "plan": "free",
                "owner_id": "user-member-001",
                "is_standalone": True,
                "created_at": datetime.utcnow(),
                "members": ["user-member-001", "user-guest-001"]
            }
        }
        
    def generate_test_tokens(self) -> Dict[str, str]:
        """Generate JWT tokens for all test users"""
        tokens = {}
        
        for user_type, user_data in self.test_users.items():
            if user_data["is_active"]:
                # Create token with user data
                token_data = {
                    "sub": user_data["email"],
                    "user_id": user_data["id"],
                    "name": user_data["name"],
                    "role": user_data["role"],
                    "exp": datetime.utcnow() + timedelta(hours=24)
                }
                
                token = create_access_token(data=token_data)
                tokens[user_type] = token
                
        self.test_tokens = tokens
        return tokens
        
    def get_auth_headers(self, user_type: str) -> Dict[str, str]:
        """Get authorization headers for a specific user type"""
        if user_type not in self.test_tokens:
            raise ValueError(f"No token available for user type: {user_type}")
            
        return {
            "Authorization": f"Bearer {self.test_tokens[user_type]}",
            "Content-Type": "application/json"
        }


class AuthTestScenarios:
    """Comprehensive authentication test scenarios"""
    
    def __init__(self, framework: AuthTestFramework):
        self.framework = framework
        
    def test_token_validation(self):
        """Test JWT token validation and parsing"""
        test_results = []
        
        for user_type, token in self.framework.test_tokens.items():
            try:
                # Test token validation
                payload = verify_token(token)
                
                test_results.append({
                    "test": f"token_validation_{user_type}",
                    "status": "PASS",
                    "user_type": user_type,
                    "payload": payload
                })
                
            except Exception as e:
                test_results.append({
                    "test": f"token_validation_{user_type}",
                    "status": "FAIL", 
                    "user_type": user_type,
                    "error": str(e)
                })
                
        return test_results
        
    def test_role_based_access(self):
        """Test role-based access control across different endpoints"""
        test_results = []
        
        # Define endpoints with required roles
        protected_endpoints = [
            {
                "endpoint": "/admin-analytics/platform-overview",
                "method": "GET",
                "required_roles": ["admin"],
                "description": "Admin analytics access"
            },
            {
                "endpoint": "/billing-console/subscriptions",
                "method": "GET", 
                "required_roles": ["admin", "user"],
                "description": "Billing console access"
            },
            {
                "endpoint": "/invoicing/team/team-enterprise-001",
                "method": "GET",
                "required_roles": ["admin", "user"],
                "description": "Invoice management access"
            },
            {
                "endpoint": "/memory/contexts",
                "method": "GET",
                "required_roles": ["admin", "user", "guest"],
                "description": "Memory access"
            }
        ]
        
        for endpoint_config in protected_endpoints:
            for user_type in self.framework.test_users.keys():
                if not self.framework.test_users[user_type]["is_active"]:
                    continue
                    
                try:
                    headers = self.framework.get_auth_headers(user_type)
                    user_role = self.framework.test_users[user_type]["role"]
                    
                    # Make request to endpoint
                    if endpoint_config["method"] == "GET":
                        response = self.framework.client.get(
                            endpoint_config["endpoint"],
                            headers=headers
                        )
                    
                    # Determine expected result
                    should_have_access = user_role in endpoint_config["required_roles"]
                    actual_has_access = response.status_code != 403
                    
                    test_status = "PASS" if should_have_access == actual_has_access else "FAIL"
                    
                    test_results.append({
                        "test": f"rbac_{endpoint_config['endpoint'].replace('/', '_')}_{user_type}",
                        "status": test_status,
                        "user_type": user_type,
                        "user_role": user_role,
                        "endpoint": endpoint_config["endpoint"],
                        "expected_access": should_have_access,
                        "actual_access": actual_has_access,
                        "status_code": response.status_code
                    })
                    
                except Exception as e:
                    test_results.append({
                        "test": f"rbac_{endpoint_config['endpoint'].replace('/', '_')}_{user_type}",
                        "status": "ERROR",
                        "user_type": user_type,
                        "endpoint": endpoint_config["endpoint"],
                        "error": str(e)
                    })
                    
        return test_results
        
    def test_team_membership_access(self):
        """Test team-based access control and membership validation"""
        test_results = []
        
        # Test team-specific endpoints
        team_endpoints = [
            {
                "endpoint": "/teams/{team_id}/members",
                "method": "GET",
                "description": "Team member list access"
            },
            {
                "endpoint": "/teams/{team_id}/billing",
                "method": "GET", 
                "description": "Team billing access"
            },
            {
                "endpoint": "/invoicing/team/{team_id}",
                "method": "GET",
                "description": "Team invoice access"
            }
        ]
        
        for team_id, team_data in self.framework.test_teams.items():
            for endpoint_config in team_endpoints:
                endpoint = endpoint_config["endpoint"].format(team_id=team_data["id"])
                
                for user_type in self.framework.test_users.keys():
                    if not self.framework.test_users[user_type]["is_active"]:
                        continue
                        
                    try:
                        headers = self.framework.get_auth_headers(user_type)
                        user_id = self.framework.test_users[user_type]["id"]
                        
                        # Check if user should have access to this team
                        is_team_member = user_id in team_data["members"]
                        is_team_owner = user_id == team_data["owner_id"]
                        is_admin = self.framework.test_users[user_type]["role"] == "admin"
                        
                        should_have_access = is_team_member or is_team_owner or is_admin
                        
                        # Make request
                        response = self.framework.client.get(endpoint, headers=headers)
                        actual_has_access = response.status_code != 403
                        
                        test_status = "PASS" if should_have_access == actual_has_access else "FAIL"
                        
                        test_results.append({
                            "test": f"team_access_{team_id}_{endpoint.replace('/', '_')}_{user_type}",
                            "status": test_status,
                            "user_type": user_type,
                            "team_id": team_data["id"],
                            "endpoint": endpoint,
                            "is_member": is_team_member,
                            "is_owner": is_team_owner,
                            "is_admin": is_admin,
                            "expected_access": should_have_access,
                            "actual_access": actual_has_access,
                            "status_code": response.status_code
                        })
                        
                    except Exception as e:
                        test_results.append({
                            "test": f"team_access_{team_id}_{endpoint.replace('/', '_')}_{user_type}",
                            "status": "ERROR",
                            "user_type": user_type,
                            "team_id": team_data["id"],
                            "endpoint": endpoint,
                            "error": str(e)
                        })
                        
        return test_results
        
    def test_session_invalidation(self):
        """Test session invalidation and token expiry scenarios"""
        test_results = []
        
        # Test expired token
        expired_token_data = {
            "sub": "test@example.com",
            "user_id": "user-test-001",
            "exp": datetime.utcnow() - timedelta(hours=1)  # Expired 1 hour ago
        }
        
        try:
            expired_token = jwt.encode(expired_token_data, "secret_key", algorithm="HS256")
            headers = {"Authorization": f"Bearer {expired_token}"}
            
            response = self.framework.client.get("/memory/contexts", headers=headers)
            
            test_results.append({
                "test": "expired_token_rejection",
                "status": "PASS" if response.status_code == 401 else "FAIL",
                "expected_status": 401,
                "actual_status": response.status_code,
                "description": "Expired token should be rejected"
            })
            
        except Exception as e:
            test_results.append({
                "test": "expired_token_rejection",
                "status": "ERROR",
                "error": str(e)
            })
            
        # Test malformed token
        try:
            malformed_token = "invalid.token.format"
            headers = {"Authorization": f"Bearer {malformed_token}"}
            
            response = self.framework.client.get("/memory/contexts", headers=headers)
            
            test_results.append({
                "test": "malformed_token_rejection",
                "status": "PASS" if response.status_code == 401 else "FAIL",
                "expected_status": 401,
                "actual_status": response.status_code,
                "description": "Malformed token should be rejected"
            })
            
        except Exception as e:
            test_results.append({
                "test": "malformed_token_rejection",
                "status": "ERROR",
                "error": str(e)
            })
            
        # Test missing token
        try:
            response = self.framework.client.get("/memory/contexts")
            
            test_results.append({
                "test": "missing_token_rejection",
                "status": "PASS" if response.status_code == 401 else "FAIL",
                "expected_status": 401,
                "actual_status": response.status_code,
                "description": "Missing token should be rejected"
            })
            
        except Exception as e:
            test_results.append({
                "test": "missing_token_rejection",
                "status": "ERROR",
                "error": str(e)
            })
            
        return test_results


class AuthTestRunner:
    """Test runner for comprehensive authentication testing"""
    
    def __init__(self):
        self.framework = AuthTestFramework()
        self.scenarios = AuthTestScenarios(self.framework)
        
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all authentication tests and return comprehensive results"""
        print("🧪 Starting Auth-Aware Testing Infrastructure...")
        
        # Setup test environment
        self.framework.setup_test_database()
        self.framework.generate_test_tokens()
        
        # Run all test scenarios
        results = {
            "test_run_id": f"auth_test_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            "timestamp": datetime.utcnow().isoformat(),
            "test_categories": {}
        }
        
        # Token validation tests
        print("  🔑 Running token validation tests...")
        results["test_categories"]["token_validation"] = self.scenarios.test_token_validation()
        
        # Role-based access control tests
        print("  👥 Running RBAC tests...")
        results["test_categories"]["role_based_access"] = self.scenarios.test_role_based_access()
        
        # Team membership tests
        print("  🏢 Running team membership tests...")
        results["test_categories"]["team_membership"] = self.scenarios.test_team_membership_access()
        
        # Session invalidation tests
        print("  ⏰ Running session invalidation tests...")
        results["test_categories"]["session_invalidation"] = self.scenarios.test_session_invalidation()
        
        # Calculate summary statistics
        total_tests = 0
        passed_tests = 0
        failed_tests = 0
        error_tests = 0
        
        for category, tests in results["test_categories"].items():
            for test in tests:
                total_tests += 1
                if test["status"] == "PASS":
                    passed_tests += 1
                elif test["status"] == "FAIL":
                    failed_tests += 1
                elif test["status"] == "ERROR":
                    error_tests += 1
                    
        results["summary"] = {
            "total_tests": total_tests,
            "passed": passed_tests,
            "failed": failed_tests,
            "errors": error_tests,
            "pass_rate": round((passed_tests / total_tests) * 100, 2) if total_tests > 0 else 0
        }
        
        print(f"✅ Auth testing complete: {passed_tests}/{total_tests} tests passed ({results['summary']['pass_rate']}%)")
        
        return results
        
    def generate_test_report(self, results: Dict[str, Any]) -> str:
        """Generate comprehensive test report"""
        report = f"""
# Auth-Aware Testing Infrastructure Report

**Test Run ID**: {results['test_run_id']}
**Timestamp**: {results['timestamp']}

## Summary
- **Total Tests**: {results['summary']['total_tests']}
- **Passed**: {results['summary']['passed']} ✅
- **Failed**: {results['summary']['failed']} ❌
- **Errors**: {results['summary']['errors']} ⚠️
- **Pass Rate**: {results['summary']['pass_rate']}%

## Test Categories

"""
        
        for category, tests in results["test_categories"].items():
            report += f"### {category.replace('_', ' ').title()}\n\n"
            
            category_passed = sum(1 for t in tests if t["status"] == "PASS")
            category_total = len(tests)
            category_rate = round((category_passed / category_total) * 100, 2) if category_total > 0 else 0
            
            report += f"**Category Pass Rate**: {category_passed}/{category_total} ({category_rate}%)\n\n"
            
            for test in tests:
                status_emoji = "✅" if test["status"] == "PASS" else "❌" if test["status"] == "FAIL" else "⚠️"
                report += f"- {status_emoji} **{test['test']}**: {test['status']}\n"
                
                if test["status"] == "FAIL" and "error" in test:
                    report += f"  - Error: {test['error']}\n"
                elif "description" in test:
                    report += f"  - {test['description']}\n"
                    
            report += "\n"
            
        return report


# Test execution functions
def run_auth_tests():
    """Main function to run authentication tests"""
    runner = AuthTestRunner()
    results = runner.run_all_tests()
    
    # Generate and save report
    report = runner.generate_test_report(results)
    
    with open("auth_test_report.md", "w") as f:
        f.write(report)
        
    return results


if __name__ == "__main__":
    # Run tests when script is executed directly
    test_results = run_auth_tests()
    print(f"\n📊 Test results saved to auth_test_report.md")
    print(f"🎯 Overall pass rate: {test_results['summary']['pass_rate']}%")
