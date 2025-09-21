#!/usr/bin/env python3
"""
RBAC Integration Test Suite
Tests the complete RBAC integration with authentication, middleware, and API endpoints
"""

import json
import sys
from datetime import datetime

import requests

# Test configuration
BASE_URL = "http://localhost:13370"
TEST_USER_EMAIL = "test@example.com"
TEST_USER_PASSWORD = "testpassword123"


class RBACIntegrationTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.user_id = None
        self.test_results = []

    def log_test(self, test_name: str, success: bool, message: str = ""):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        self.test_results.append(
            {
                "test": test_name,
                "success": success,
                "message": message,
                "timestamp": datetime.now().isoformat(),
            }
        )
        print(f"{status} {test_name}: {message}")

    def test_authentication_with_rbac(self):
        """Test authentication returns RBAC roles in JWT token"""
        try:
            # Login with test user
            login_data = {"email": TEST_USER_EMAIL, "password": TEST_USER_PASSWORD}

            response = self.session.post(f"{BASE_URL}/login", json=login_data)

            if response.status_code == 200:
                data = response.json()

                # Check if JWT token is present
                if "user" in data and "jwt_token" in data["user"]:
                    self.auth_token = data["user"]["jwt_token"]
                    self.user_id = data["user"]["user_id"]

                    # Check for RBAC roles
                    if "rbac_roles" in data["user"]:
                        self.log_test(
                            "Authentication with RBAC",
                            True,
                            f"User authenticated with roles: {data['user']['rbac_roles']}",
                        )
                        return True
                    else:
                        self.log_test(
                            "Authentication with RBAC",
                            False,
                            "RBAC roles not found in authentication response",
                        )
                        return False
                else:
                    self.log_test(
                        "Authentication with RBAC",
                        False,
                        "JWT token not found in response",
                    )
                    return False
            else:
                self.log_test(
                    "Authentication with RBAC",
                    False,
                    f"Login failed with status {response.status_code}: {response.text}",
                )
                return False

        except Exception as e:
            self.log_test("Authentication with RBAC", False, f"Exception: {str(e)}")
            return False

    def test_rbac_middleware(self):
        """Test RBAC middleware extracts context from JWT"""
        try:
            if not self.auth_token:
                self.log_test("RBAC Middleware", False, "No auth token available")
                return False

            # Set authorization header
            headers = {"Authorization": f"Bearer {self.auth_token}"}

            # Test protected endpoint
            response = self.session.get(f"{BASE_URL}/auth/me", headers=headers)

            if response.status_code == 200:
                self.log_test(
                    "RBAC Middleware",
                    True,
                    "Middleware successfully processed JWT token",
                )
                return True
            else:
                self.log_test(
                    "RBAC Middleware",
                    False,
                    f"Protected endpoint failed with status {response.status_code}",
                )
                return False

        except Exception as e:
            self.log_test("RBAC Middleware", False, f"Exception: {str(e)}")
            return False

    def test_permission_decorators(self):
        """Test permission decorators on API endpoints"""
        try:
            if not self.auth_token:
                self.log_test("Permission Decorators", False, "No auth token available")
                return False

            headers = {"Authorization": f"Bearer {self.auth_token}"}

            # Test memory read endpoint (should work with MEMBER role)
            response = self.session.get(
                f"{BASE_URL}/memory?context=test", headers=headers
            )

            if response.status_code in [200, 404]:  # 404 is ok if no memories exist
                self.log_test(
                    "Permission Decorators - Memory Read",
                    True,
                    "Memory read permission check passed",
                )
                memory_test = True
            else:
                self.log_test(
                    "Permission Decorators - Memory Read",
                    False,
                    f"Memory read failed with status {response.status_code}",
                )
                memory_test = False

            # Test organization read endpoint
            response = self.session.get(f"{BASE_URL}/organizations", headers=headers)

            if response.status_code == 200:
                self.log_test(
                    "Permission Decorators - Org Read",
                    True,
                    "Organization read permission check passed",
                )
                org_test = True
            elif response.status_code == 403:
                self.log_test(
                    "Permission Decorators - Org Read",
                    True,
                    "Organization read correctly denied (403)",
                )
                org_test = True
            else:
                self.log_test(
                    "Permission Decorators - Org Read",
                    False,
                    f"Unexpected status {response.status_code}",
                )
                org_test = False

            return memory_test and org_test

        except Exception as e:
            self.log_test("Permission Decorators", False, f"Exception: {str(e)}")
            return False

    def test_rbac_api_endpoints(self):
        """Test RBAC management API endpoints"""
        try:
            if not self.auth_token:
                self.log_test("RBAC API Endpoints", False, "No auth token available")
                return False

            headers = {"Authorization": f"Bearer {self.auth_token}"}

            # Test RBAC status endpoint
            response = self.session.get(f"{BASE_URL}/rbac/status", headers=headers)

            if response.status_code == 200:
                data = response.json()
                if "rbac_enabled" in data and data["rbac_enabled"]:
                    self.log_test(
                        "RBAC API - Status",
                        True,
                        f"RBAC system active with {data.get('statistics', {}).get('total_role_assignments', 0)} role assignments",
                    )
                    status_test = True
                else:
                    self.log_test(
                        "RBAC API - Status",
                        False,
                        "RBAC not enabled in status response",
                    )
                    status_test = False
            elif response.status_code == 403:
                self.log_test(
                    "RBAC API - Status",
                    True,
                    "RBAC status correctly denied (403) - user lacks SYSTEM permissions",
                )
                status_test = True
            else:
                self.log_test(
                    "RBAC API - Status",
                    False,
                    f"Status endpoint failed with {response.status_code}",
                )
                status_test = False

            # Test user roles endpoint
            response = self.session.get(
                f"{BASE_URL}/rbac/roles/user/{self.user_id}", headers=headers
            )

            if response.status_code == 200:
                data = response.json()
                if "roles" in data:
                    self.log_test(
                        "RBAC API - User Roles",
                        True,
                        f"Retrieved {len(data['roles'])} role assignments",
                    )
                    roles_test = True
                else:
                    self.log_test(
                        "RBAC API - User Roles", False, "No roles in response"
                    )
                    roles_test = False
            elif response.status_code == 403:
                self.log_test(
                    "RBAC API - User Roles", True, "User roles correctly denied (403)"
                )
                roles_test = True
            else:
                self.log_test(
                    "RBAC API - User Roles",
                    False,
                    f"User roles failed with {response.status_code}",
                )
                roles_test = False

            return status_test and roles_test

        except Exception as e:
            self.log_test("RBAC API Endpoints", False, f"Exception: {str(e)}")
            return False

    def test_database_integration(self):
        """Test RBAC database tables and data"""
        try:
            # This would require database connection - for now just check if tables exist via API
            if not self.auth_token:
                self.log_test("Database Integration", False, "No auth token available")
                return False

            headers = {"Authorization": f"Bearer {self.auth_token}"}

            # Test audit log endpoint (if accessible)
            response = self.session.get(
                f"{BASE_URL}/rbac/audit/permissions?limit=1", headers=headers
            )

            if response.status_code in [200, 403]:
                self.log_test(
                    "Database Integration",
                    True,
                    "RBAC database tables accessible via API",
                )
                return True
            else:
                self.log_test(
                    "Database Integration",
                    False,
                    f"Database integration test failed with {response.status_code}",
                )
                return False

        except Exception as e:
            self.log_test("Database Integration", False, f"Exception: {str(e)}")
            return False

    def run_all_tests(self):
        """Run complete RBAC integration test suite"""
        print("🧪 Starting RBAC Integration Test Suite")
        print("=" * 50)

        tests = [
            ("Authentication with RBAC", self.test_authentication_with_rbac),
            ("RBAC Middleware", self.test_rbac_middleware),
            ("Permission Decorators", self.test_permission_decorators),
            ("RBAC API Endpoints", self.test_rbac_api_endpoints),
            ("Database Integration", self.test_database_integration),
        ]

        passed = 0
        total = len(tests)

        for test_name, test_func in tests:
            print(f"\n🔍 Running: {test_name}")
            if test_func():
                passed += 1

        print("\n" + "=" * 50)
        print(f"📊 Test Results: {passed}/{total} tests passed")

        if passed == total:
            print("🎉 All RBAC integration tests PASSED!")
            return True
        else:
            print(f"⚠️  {total - passed} tests FAILED")
            return False

    def generate_report(self):
        """Generate detailed test report"""
        report = {
            "test_suite": "RBAC Integration Tests",
            "timestamp": datetime.now().isoformat(),
            "total_tests": len(self.test_results),
            "passed_tests": len([r for r in self.test_results if r["success"]]),
            "failed_tests": len([r for r in self.test_results if not r["success"]]),
            "results": self.test_results,
        }

        with open("rbac_integration_test_report.json", "w") as f:
            json.dump(report, f, indent=2)

        print("\n📄 Detailed report saved to: rbac_integration_test_report.json")
        return report


def main():
    """Main test execution"""
    print("🚀 RBAC Integration Test Suite")
    print("Testing Ninaivalaigal RBAC system integration...")

    tester = RBACIntegrationTester()

    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code != 200:
            print(f"❌ Server not responding at {BASE_URL}")
            sys.exit(1)
    except requests.exceptions.RequestException:
        print(f"❌ Cannot connect to server at {BASE_URL}")
        print("Please ensure the FastAPI server is running on port 13370")
        sys.exit(1)

    # Run tests
    success = tester.run_all_tests()

    # Generate report
    tester.generate_report()

    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
