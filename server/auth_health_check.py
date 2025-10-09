"""
Auth Health Check and Debug Tools
Comprehensive testing and validation for auth system
"""

import asyncio
import logging
import time
from typing import Any, Dict

from auth_async import authenticate_user_async, authenticate_user_sync

logger = logging.getLogger(__name__)


class AuthHealthChecker:
    """Comprehensive auth system health checker"""

    def __init__(self):
        """Initialize instance."""
        self.test_results = []

    async def run_full_health_check(self) -> Dict[str, Any]:
        """Run complete auth system health check"""
        print("🏥 Starting Auth Health Check...")

        results = {"timestamp": time.time(), "overall_status": "unknown", "tests": {}}

        # Test 1: Sync Auth Function
        print("\n📋 Test 1: Sync Authentication Function")
        sync_result = await self._test_sync_auth()
        results["tests"]["sync_auth"] = sync_result

        # Test 2: Async Auth Function
        print("\n📋 Test 2: Async Authentication Function")
        async_result = await self._test_async_auth()
        results["tests"]["async_auth"] = async_result

        # Test 3: Database Connection
        print("\n📋 Test 3: Database Connection")
        db_result = await self._test_database_connection()
        results["tests"]["database"] = db_result

        # Test 4: JWT Generation
        print("\n📋 Test 4: JWT Token Generation")
        jwt_result = await self._test_jwt_generation()
        results["tests"]["jwt"] = jwt_result

        # Test 5: Performance Test
        print("\n📋 Test 5: Performance Test")
        perf_result = await self._test_performance()
        results["tests"]["performance"] = perf_result

        # Determine overall status
        all_passed = all(test.get("status") == "pass" for test in results["tests"].values())
        results["overall_status"] = "healthy" if all_passed else "issues_detected"

        print(f"\n🎯 Overall Status: {results['overall_status']}")
        return results

    async def _test_sync_auth(self) -> Dict[str, Any]:
        """Test synchronous authentication"""
        try:
            start_time = time.time()

            # Test with valid credentials
            result = authenticate_user_sync("test@ninaivalaigal.com", "test")

            duration = time.time() - start_time

            if result and result.get("jwt_token"):
                print(f"✅ Sync auth passed ({duration:.3f}s)")
                return {
                    "status": "pass",
                    "duration": duration,
                    "result": "Authentication successful",
                    "jwt_token_present": True,
                }
            else:
                print("❌ Sync auth failed - no result")
                return {
                    "status": "fail",
                    "duration": duration,
                    "result": "No authentication result",
                    "jwt_token_present": False,
                }

        except Exception as e:
            print(f"❌ Sync auth failed with exception: {e}")
            return {
                "status": "fail",
                "duration": 0,
                "result": f"Exception: {str(e)}",
                "jwt_token_present": False,
            }

    async def _test_async_auth(self) -> Dict[str, Any]:
        """Test asynchronous authentication"""
        try:
            start_time = time.time()

            # Test with timeout
            result = await asyncio.wait_for(authenticate_user_async("test@ninaivalaigal.com", "test"), timeout=10.0)

            duration = time.time() - start_time

            if result and result.get("jwt_token"):
                print(f"✅ Async auth passed ({duration:.3f}s)")
                return {
                    "status": "pass",
                    "duration": duration,
                    "result": "Authentication successful",
                    "jwt_token_present": True,
                }
            else:
                print("❌ Async auth failed - no result")
                return {
                    "status": "fail",
                    "duration": duration,
                    "result": "No authentication result",
                    "jwt_token_present": False,
                }

        except asyncio.TimeoutError:
            print("❌ Async auth timed out")
            return {
                "status": "fail",
                "duration": 10.0,
                "result": "Timeout after 10 seconds",
                "jwt_token_present": False,
            }
        except Exception as e:
            print(f"❌ Async auth failed with exception: {e}")
            return {
                "status": "fail",
                "duration": 0,
                "result": f"Exception: {str(e)}",
                "jwt_token_present": False,
            }

    async def _test_database_connection(self) -> Dict[str, Any]:
        """Test database connection"""
        try:
            from database.simple_operations import SimpleDatabaseOperations

            from config import load_config

            start_time = time.time()

            database_url = load_config()
            db = SimpleDatabaseOperations(database_url)

            # Try to get a user
            user = db.get_user_by_email("test@ninaivalaigal.com")

            duration = time.time() - start_time

            if user:
                print(f"✅ Database connection passed ({duration:.3f}s)")
                return {
                    "status": "pass",
                    "duration": duration,
                    "result": f"User found: {user.email}",
                    "user_exists": True,
                }
            else:
                print("❌ Database connection failed - no user found")
                return {
                    "status": "fail",
                    "duration": duration,
                    "result": "Test user not found",
                    "user_exists": False,
                }

        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            return {
                "status": "fail",
                "duration": 0,
                "result": f"Exception: {str(e)}",
                "user_exists": False,
            }

    async def _test_jwt_generation(self) -> Dict[str, Any]:
        """Test JWT token generation"""
        try:
            from datetime import datetime, timedelta

            import jwt

            start_time = time.time()

            # Test JWT creation
            test_payload = {
                "user_id": "test-user-id",
                "email": "test@example.com",
                "exp": datetime.utcnow() + timedelta(hours=1),
            }

            token = jwt.encode(test_payload, "test-secret", algorithm="HS256")

            # Test JWT decoding
            decoded = jwt.decode(token, "test-secret", algorithms=["HS256"])

            duration = time.time() - start_time

            if decoded.get("user_id") == "test-user-id":
                print(f"✅ JWT generation passed ({duration:.3f}s)")
                return {
                    "status": "pass",
                    "duration": duration,
                    "result": "JWT encode/decode successful",
                    "token_valid": True,
                }
            else:
                print("❌ JWT generation failed - invalid decode")
                return {
                    "status": "fail",
                    "duration": duration,
                    "result": "JWT decode mismatch",
                    "token_valid": False,
                }

        except Exception as e:
            print(f"❌ JWT generation failed: {e}")
            return {
                "status": "fail",
                "duration": 0,
                "result": f"Exception: {str(e)}",
                "token_valid": False,
            }

    async def _test_performance(self) -> Dict[str, Any]:
        """Test auth performance"""
        try:
            print("🚀 Running performance test (5 auth attempts)...")

            times = []
            successes = 0

            for i in range(5):
                start_time = time.time()
                result = await authenticate_user_async("test@ninaivalaigal.com", "test")
                duration = time.time() - start_time

                times.append(duration)
                if result:
                    successes += 1

                print(f"  Attempt {i+1}: {duration:.3f}s {'✅' if result else '❌'}")

            avg_time = sum(times) / len(times)
            max_time = max(times)
            min_time = min(times)

            if successes == 5 and avg_time < 2.0:
                print(f"✅ Performance test passed (avg: {avg_time:.3f}s)")
                return {
                    "status": "pass",
                    "avg_duration": avg_time,
                    "max_duration": max_time,
                    "min_duration": min_time,
                    "success_rate": successes / 5,
                    "result": "Performance acceptable",
                }
            else:
                print(f"❌ Performance test failed (avg: {avg_time:.3f}s, successes: {successes}/5)")
                return {
                    "status": "fail",
                    "avg_duration": avg_time,
                    "max_duration": max_time,
                    "min_duration": min_time,
                    "success_rate": successes / 5,
                    "result": "Performance issues detected",
                }

        except Exception as e:
            print(f"❌ Performance test failed: {e}")
            return {
                "status": "fail",
                "avg_duration": 0,
                "result": f"Exception: {str(e)}",
            }


async def quick_auth_test():
    """Quick auth test for debugging"""
    print("🔍 Quick Auth Test")

    try:
        print("Testing sync auth...")
        sync_result = authenticate_user_sync("test@ninaivalaigal.com", "test")
        print(f"Sync result: {'✅ Success' if sync_result else '❌ Failed'}")

        print("Testing async auth...")
        async_result = await authenticate_user_async("test@ninaivalaigal.com", "test")
        print(f"Async result: {'✅ Success' if async_result else '❌ Failed'}")

        return sync_result and async_result

    except Exception as e:
        print(f"❌ Quick test failed: {e}")
        return False


if __name__ == "__main__":
    # Run health check
    async def main():
        checker = AuthHealthChecker()
        results = await checker.run_full_health_check()

        print("\n📊 HEALTH CHECK SUMMARY:")
        print(f"Overall Status: {results['overall_status']}")

        for test_name, test_result in results["tests"].items():
            status_icon = "✅" if test_result["status"] == "pass" else "❌"
            print(f"{status_icon} {test_name}: {test_result['result']}")

    asyncio.run(main())
