"""
Concurrent Testing Framework
Multi-org/team/user simulation with load testing capabilities
"""

import asyncio
import json
import pytest
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import time
import random
from fastapi.testclient import TestClient

# Import our application components
from server.main import app
from tests.auth_aware_testing import AuthTestFramework


class ConcurrentTestFramework:
    """Framework for concurrent and load testing scenarios"""
    
    def __init__(self, max_workers: int = 10):
        self.client = TestClient(app)
        self.auth_framework = AuthTestFramework()
        self.max_workers = max_workers
        self.test_users = {}
        self.test_teams = {}
        self.concurrent_results = []
        self.performance_metrics = {}
        
    def setup_concurrent_test_data(self):
        """Setup test data for concurrent scenarios"""
        # Create multiple organizations
        self.test_orgs = {
            f"org_{i}": {
                "id": f"org-{i:03d}",
                "name": f"Organization {i}",
                "plan": random.choice(["free", "pro", "enterprise"]),
                "created_at": datetime.utcnow() - timedelta(days=random.randint(1, 365))
            }
            for i in range(1, 6)  # 5 organizations
        }
        
        # Create multiple teams per organization
        self.test_teams = {}
        for org_id, org_data in self.test_orgs.items():
            teams_count = random.randint(2, 5)
            for j in range(teams_count):
                team_id = f"team-{org_data['id']}-{j:02d}"
                self.test_teams[team_id] = {
                    "id": team_id,
                    "name": f"Team {j} - {org_data['name']}",
                    "org_id": org_data["id"],
                    "plan": org_data["plan"],
                    "member_count": random.randint(3, 15),
                    "created_at": datetime.utcnow() - timedelta(days=random.randint(1, 180))
                }
                
        # Create multiple users across teams
        self.test_users = {}
        user_counter = 1
        for team_id, team_data in self.test_teams.items():
            for k in range(team_data["member_count"]):
                user_id = f"user-{user_counter:04d}"
                self.test_users[user_id] = {
                    "id": user_id,
                    "email": f"user{user_counter}@{team_data['org_id']}.com",
                    "name": f"User {user_counter}",
                    "team_id": team_id,
                    "org_id": team_data["org_id"],
                    "role": "owner" if k == 0 else random.choice(["admin", "member", "guest"]),
                    "is_active": random.choice([True, True, True, False]),  # 75% active
                    "created_at": datetime.utcnow() - timedelta(days=random.randint(1, 90))
                }
                user_counter += 1


class ConcurrentUserScenarios:
    """Concurrent user interaction scenarios"""
    
    def __init__(self, framework: ConcurrentTestFramework):
        self.framework = framework
        
    def simulate_user_session(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate a complete user session with multiple actions"""
        session_start = time.time()
        session_results = {
            "user_id": user_data["id"],
            "user_email": user_data["email"],
            "team_id": user_data["team_id"],
            "actions": [],
            "errors": [],
            "total_duration": 0,
            "success_rate": 0
        }
        
        try:
            # Generate token for user
            token_data = {
                "sub": user_data["email"],
                "user_id": user_data["id"],
                "name": user_data["name"],
                "role": user_data["role"],
                "exp": datetime.utcnow() + timedelta(hours=1)
            }
            
            # Simulate typical user actions
            actions = [
                ("login", "GET", "/health"),
                ("view_dashboard", "GET", "/memory/contexts"),
                ("create_memory", "POST", "/memory/create"),
                ("view_team", "GET", f"/teams/{user_data['team_id']}"),
                ("check_billing", "GET", "/billing-console/subscription-status"),
                ("view_analytics", "GET", "/usage-analytics/team-metrics")
            ]
            
            headers = {
                "Authorization": f"Bearer test_token_{user_data['id']}",
                "Content-Type": "application/json"
            }
            
            for action_name, method, endpoint in actions:
                action_start = time.time()
                
                try:
                    if method == "GET":
                        response = self.framework.client.get(endpoint, headers=headers)
                    elif method == "POST":
                        test_data = {"test": True, "user_id": user_data["id"]}
                        response = self.framework.client.post(endpoint, json=test_data, headers=headers)
                        
                    action_duration = time.time() - action_start
                    
                    session_results["actions"].append({
                        "action": action_name,
                        "method": method,
                        "endpoint": endpoint,
                        "status_code": response.status_code,
                        "duration": action_duration,
                        "success": response.status_code < 400
                    })
                    
                except Exception as e:
                    session_results["errors"].append({
                        "action": action_name,
                        "error": str(e),
                        "timestamp": datetime.utcnow().isoformat()
                    })
                    
                # Random delay between actions (0.1 to 2 seconds)
                time.sleep(random.uniform(0.1, 2.0))
                
        except Exception as e:
            session_results["errors"].append({
                "action": "session_setup",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            })
            
        session_results["total_duration"] = time.time() - session_start
        successful_actions = sum(1 for action in session_results["actions"] if action["success"])
        total_actions = len(session_results["actions"])
        session_results["success_rate"] = (successful_actions / total_actions) if total_actions > 0 else 0
        
        return session_results
        
    def test_concurrent_user_sessions(self, num_concurrent_users: int = 20) -> List[Dict[str, Any]]:
        """Test multiple concurrent user sessions"""
        print(f"  👥 Running {num_concurrent_users} concurrent user sessions...")
        
        # Select random users for concurrent testing
        active_users = [user for user in self.framework.test_users.values() if user["is_active"]]
        test_users = random.sample(active_users, min(num_concurrent_users, len(active_users)))
        
        concurrent_results = []
        
        with ThreadPoolExecutor(max_workers=self.framework.max_workers) as executor:
            # Submit all user sessions
            future_to_user = {
                executor.submit(self.simulate_user_session, user): user 
                for user in test_users
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_user):
                user = future_to_user[future]
                try:
                    result = future.result()
                    concurrent_results.append(result)
                except Exception as e:
                    concurrent_results.append({
                        "user_id": user["id"],
                        "error": str(e),
                        "success_rate": 0
                    })
                    
        return concurrent_results


class ConcurrentBillingScenarios:
    """Concurrent billing and payment scenarios"""
    
    def __init__(self, framework: ConcurrentTestFramework):
        self.framework = framework
        
    def simulate_billing_operation(self, team_data: Dict[str, Any], operation: str) -> Dict[str, Any]:
        """Simulate billing operations for a team"""
        operation_start = time.time()
        result = {
            "team_id": team_data["id"],
            "operation": operation,
            "success": False,
            "duration": 0,
            "status_code": None,
            "error": None
        }
        
        try:
            headers = {
                "Authorization": f"Bearer admin_token",
                "Content-Type": "application/json"
            }
            
            if operation == "create_subscription":
                data = {
                    "team_id": team_data["id"],
                    "plan": team_data["plan"],
                    "payment_method_id": f"pm_test_{team_data['id']}"
                }
                response = self.framework.client.post("/billing-console/create-subscription", json=data, headers=headers)
                
            elif operation == "generate_invoice":
                data = {
                    "team_id": team_data["id"],
                    "billing_period_start": datetime.utcnow().strftime("%Y-%m-%d"),
                    "billing_period_end": (datetime.utcnow() + timedelta(days=30)).strftime("%Y-%m-%d")
                }
                response = self.framework.client.post("/invoicing/generate", json=data, headers=headers)
                
            elif operation == "process_payment":
                data = {
                    "team_id": team_data["id"],
                    "amount": 2900,
                    "currency": "usd"
                }
                response = self.framework.client.post("/billing-console/process-payment", json=data, headers=headers)
                
            else:
                raise ValueError(f"Unknown operation: {operation}")
                
            result["success"] = response.status_code < 400
            result["status_code"] = response.status_code
            
        except Exception as e:
            result["error"] = str(e)
            
        result["duration"] = time.time() - operation_start
        return result
        
    def test_concurrent_billing_operations(self, num_operations: int = 15) -> List[Dict[str, Any]]:
        """Test concurrent billing operations across multiple teams"""
        print(f"  💳 Running {num_operations} concurrent billing operations...")
        
        # Select teams for billing operations
        test_teams = list(self.framework.test_teams.values())[:num_operations]
        operations = ["create_subscription", "generate_invoice", "process_payment"]
        
        concurrent_results = []
        
        with ThreadPoolExecutor(max_workers=self.framework.max_workers) as executor:
            # Submit billing operations
            future_to_operation = {}
            
            for i, team in enumerate(test_teams):
                operation = operations[i % len(operations)]
                future = executor.submit(self.simulate_billing_operation, team, operation)
                future_to_operation[future] = (team, operation)
                
            # Collect results
            for future in as_completed(future_to_operation):
                team, operation = future_to_operation[future]
                try:
                    result = future.result()
                    concurrent_results.append(result)
                except Exception as e:
                    concurrent_results.append({
                        "team_id": team["id"],
                        "operation": operation,
                        "success": False,
                        "error": str(e)
                    })
                    
        return concurrent_results


class ConcurrentAnalyticsScenarios:
    """Concurrent analytics and reporting scenarios"""
    
    def __init__(self, framework: ConcurrentTestFramework):
        self.framework = framework
        
    def simulate_analytics_query(self, query_type: str, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate analytics queries"""
        query_start = time.time()
        result = {
            "query_type": query_type,
            "user_id": user_data["id"],
            "team_id": user_data["team_id"],
            "success": False,
            "duration": 0,
            "data_size": 0,
            "error": None
        }
        
        try:
            headers = {
                "Authorization": f"Bearer {user_data['id']}_token",
                "Content-Type": "application/json"
            }
            
            endpoints = {
                "usage_analytics": "/usage-analytics/team-metrics",
                "admin_analytics": "/admin-analytics/platform-overview",
                "billing_analytics": "/billing-console/analytics",
                "memory_analytics": "/memory/analytics",
                "team_analytics": f"/teams/{user_data['team_id']}/analytics"
            }
            
            if query_type in endpoints:
                response = self.framework.client.get(endpoints[query_type], headers=headers)
                result["success"] = response.status_code < 400
                result["status_code"] = response.status_code
                
                if response.status_code == 200:
                    result["data_size"] = len(response.content)
                    
        except Exception as e:
            result["error"] = str(e)
            
        result["duration"] = time.time() - query_start
        return result
        
    def test_concurrent_analytics_queries(self, num_queries: int = 25) -> List[Dict[str, Any]]:
        """Test concurrent analytics queries"""
        print(f"  📊 Running {num_queries} concurrent analytics queries...")
        
        query_types = ["usage_analytics", "admin_analytics", "billing_analytics", "memory_analytics", "team_analytics"]
        active_users = [user for user in self.framework.test_users.values() if user["is_active"]]
        
        concurrent_results = []
        
        with ThreadPoolExecutor(max_workers=self.framework.max_workers) as executor:
            # Submit analytics queries
            future_to_query = {}
            
            for i in range(num_queries):
                query_type = random.choice(query_types)
                user = random.choice(active_users)
                future = executor.submit(self.simulate_analytics_query, query_type, user)
                future_to_query[future] = (query_type, user)
                
            # Collect results
            for future in as_completed(future_to_query):
                query_type, user = future_to_query[future]
                try:
                    result = future.result()
                    concurrent_results.append(result)
                except Exception as e:
                    concurrent_results.append({
                        "query_type": query_type,
                        "user_id": user["id"],
                        "success": False,
                        "error": str(e)
                    })
                    
        return concurrent_results


class LoadTestingScenarios:
    """Load testing scenarios for performance validation"""
    
    def __init__(self, framework: ConcurrentTestFramework):
        self.framework = framework
        
    def run_load_test(self, endpoint: str, method: str = "GET", duration_seconds: int = 30, requests_per_second: int = 10) -> Dict[str, Any]:
        """Run load test against specific endpoint"""
        print(f"  🔥 Load testing {endpoint} for {duration_seconds}s at {requests_per_second} RPS...")
        
        results = {
            "endpoint": endpoint,
            "method": method,
            "duration_seconds": duration_seconds,
            "target_rps": requests_per_second,
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "response_times": [],
            "error_rates": [],
            "throughput": 0
        }
        
        start_time = time.time()
        end_time = start_time + duration_seconds
        request_interval = 1.0 / requests_per_second
        
        def make_request():
            request_start = time.time()
            try:
                headers = {"Authorization": "Bearer load_test_token"}
                
                if method == "GET":
                    response = self.framework.client.get(endpoint, headers=headers)
                elif method == "POST":
                    response = self.framework.client.post(endpoint, json={"test": True}, headers=headers)
                    
                request_duration = time.time() - request_start
                
                return {
                    "success": response.status_code < 400,
                    "status_code": response.status_code,
                    "duration": request_duration
                }
                
            except Exception as e:
                return {
                    "success": False,
                    "error": str(e),
                    "duration": time.time() - request_start
                }
                
        # Execute load test
        with ThreadPoolExecutor(max_workers=self.framework.max_workers * 2) as executor:
            futures = []
            
            while time.time() < end_time:
                future = executor.submit(make_request)
                futures.append(future)
                results["total_requests"] += 1
                
                # Wait for next request interval
                time.sleep(request_interval)
                
            # Collect all results
            for future in as_completed(futures):
                try:
                    result = future.result()
                    results["response_times"].append(result["duration"])
                    
                    if result["success"]:
                        results["successful_requests"] += 1
                    else:
                        results["failed_requests"] += 1
                        
                except Exception as e:
                    results["failed_requests"] += 1
                    
        # Calculate metrics
        actual_duration = time.time() - start_time
        results["actual_duration"] = actual_duration
        results["throughput"] = results["total_requests"] / actual_duration
        results["success_rate"] = (results["successful_requests"] / results["total_requests"]) if results["total_requests"] > 0 else 0
        
        if results["response_times"]:
            results["avg_response_time"] = sum(results["response_times"]) / len(results["response_times"])
            results["min_response_time"] = min(results["response_times"])
            results["max_response_time"] = max(results["response_times"])
            results["p95_response_time"] = sorted(results["response_times"])[int(len(results["response_times"]) * 0.95)]
            
        return results


class ConcurrentTestRunner:
    """Test runner for comprehensive concurrent testing"""
    
    def __init__(self, max_workers: int = 10):
        self.framework = ConcurrentTestFramework(max_workers)
        self.user_scenarios = ConcurrentUserScenarios(self.framework)
        self.billing_scenarios = ConcurrentBillingScenarios(self.framework)
        self.analytics_scenarios = ConcurrentAnalyticsScenarios(self.framework)
        self.load_scenarios = LoadTestingScenarios(self.framework)
        
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all concurrent testing scenarios"""
        print("🚀 Starting Concurrent Testing Framework...")
        
        # Setup test environment
        self.framework.setup_concurrent_test_data()
        
        results = {
            "test_run_id": f"concurrent_test_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            "timestamp": datetime.utcnow().isoformat(),
            "test_environment": {
                "max_workers": self.framework.max_workers,
                "total_orgs": len(self.framework.test_orgs),
                "total_teams": len(self.framework.test_teams),
                "total_users": len(self.framework.test_users)
            },
            "test_results": {}
        }
        
        # Concurrent user sessions
        print("👥 Running concurrent user session tests...")
        results["test_results"]["user_sessions"] = self.user_scenarios.test_concurrent_user_sessions(20)
        
        # Concurrent billing operations
        print("💳 Running concurrent billing tests...")
        results["test_results"]["billing_operations"] = self.billing_scenarios.test_concurrent_billing_operations(15)
        
        # Concurrent analytics queries
        print("📊 Running concurrent analytics tests...")
        results["test_results"]["analytics_queries"] = self.analytics_scenarios.test_concurrent_analytics_queries(25)
        
        # Load testing
        print("🔥 Running load tests...")
        load_test_endpoints = [
            ("/health", "GET"),
            ("/memory/contexts", "GET"),
            ("/usage-analytics/team-metrics", "GET"),
            ("/admin-analytics/platform-overview", "GET")
        ]
        
        results["test_results"]["load_tests"] = []
        for endpoint, method in load_test_endpoints:
            load_result = self.load_scenarios.run_load_test(endpoint, method, duration_seconds=15, requests_per_second=5)
            results["test_results"]["load_tests"].append(load_result)
            
        # Calculate overall performance metrics
        self._calculate_performance_summary(results)
        
        print(f"✅ Concurrent testing complete!")
        
        return results
        
    def _calculate_performance_summary(self, results: Dict[str, Any]):
        """Calculate overall performance summary"""
        summary = {
            "user_sessions": {
                "total_sessions": len(results["test_results"]["user_sessions"]),
                "avg_success_rate": 0,
                "avg_session_duration": 0
            },
            "billing_operations": {
                "total_operations": len(results["test_results"]["billing_operations"]),
                "success_rate": 0,
                "avg_duration": 0
            },
            "analytics_queries": {
                "total_queries": len(results["test_results"]["analytics_queries"]),
                "success_rate": 0,
                "avg_duration": 0
            },
            "load_tests": {
                "total_endpoints": len(results["test_results"]["load_tests"]),
                "avg_throughput": 0,
                "avg_response_time": 0
            }
        }
        
        # User sessions summary
        if results["test_results"]["user_sessions"]:
            sessions = results["test_results"]["user_sessions"]
            summary["user_sessions"]["avg_success_rate"] = sum(s.get("success_rate", 0) for s in sessions) / len(sessions)
            summary["user_sessions"]["avg_session_duration"] = sum(s.get("total_duration", 0) for s in sessions) / len(sessions)
            
        # Billing operations summary
        if results["test_results"]["billing_operations"]:
            operations = results["test_results"]["billing_operations"]
            successful_ops = sum(1 for op in operations if op.get("success", False))
            summary["billing_operations"]["success_rate"] = successful_ops / len(operations)
            summary["billing_operations"]["avg_duration"] = sum(op.get("duration", 0) for op in operations) / len(operations)
            
        # Analytics queries summary
        if results["test_results"]["analytics_queries"]:
            queries = results["test_results"]["analytics_queries"]
            successful_queries = sum(1 for q in queries if q.get("success", False))
            summary["analytics_queries"]["success_rate"] = successful_queries / len(queries)
            summary["analytics_queries"]["avg_duration"] = sum(q.get("duration", 0) for q in queries) / len(queries)
            
        # Load tests summary
        if results["test_results"]["load_tests"]:
            load_tests = results["test_results"]["load_tests"]
            summary["load_tests"]["avg_throughput"] = sum(lt.get("throughput", 0) for lt in load_tests) / len(load_tests)
            summary["load_tests"]["avg_response_time"] = sum(lt.get("avg_response_time", 0) for lt in load_tests) / len(load_tests)
            
        results["performance_summary"] = summary


# Test execution functions
def run_concurrent_tests():
    """Main function to run concurrent tests"""
    runner = ConcurrentTestRunner(max_workers=10)
    results = runner.run_all_tests()
    
    # Save results
    with open("concurrent_test_results.json", "w") as f:
        json.dump(results, f, indent=2)
        
    return results


if __name__ == "__main__":
    test_results = run_concurrent_tests()
    print(f"\n📊 Test results saved to concurrent_test_results.json")
    print(f"🎯 Performance summary available in results")
