"""
End-to-End Billing Flow Testing
Comprehensive testing for subscription creation, payment processing, and invoice generation
"""

import asyncio
import json
import pytest
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from unittest.mock import Mock, patch, MagicMock
import stripe
from fastapi.testclient import TestClient

# Import our application components
from server.main import app
from server.billing_console_api import router as billing_router
from server.invoice_management_api import router as invoice_router
from tests.auth_aware_testing import AuthTestFramework


class BillingTestFramework:
    """Comprehensive billing flow testing framework"""
    
    def __init__(self):
        self.client = TestClient(app)
        self.auth_framework = AuthTestFramework()
        self.mock_stripe_data = {}
        self.test_scenarios = []
        
    def setup_mock_stripe_data(self):
        """Setup mock Stripe data for testing"""
        self.mock_stripe_data = {
            "customers": {
                "cus_test_001": {
                    "id": "cus_test_001",
                    "email": "owner@company.com",
                    "name": "Team Owner",
                    "created": int(datetime.utcnow().timestamp()),
                    "metadata": {"team_id": "team-enterprise-001"}
                }
            },
            "subscriptions": {
                "sub_test_001": {
                    "id": "sub_test_001",
                    "customer": "cus_test_001",
                    "status": "active",
                    "current_period_start": int(datetime.utcnow().timestamp()),
                    "current_period_end": int((datetime.utcnow() + timedelta(days=30)).timestamp()),
                    "items": {
                        "data": [{
                            "id": "si_test_001",
                            "price": {
                                "id": "price_test_pro",
                                "unit_amount": 2900,  # $29.00
                                "currency": "usd",
                                "recurring": {"interval": "month"}
                            },
                            "quantity": 1
                        }]
                    }
                }
            },
            "payment_methods": {
                "pm_test_001": {
                    "id": "pm_test_001",
                    "customer": "cus_test_001",
                    "type": "card",
                    "card": {
                        "brand": "visa",
                        "last4": "4242",
                        "exp_month": 12,
                        "exp_year": 2025
                    }
                }
            },
            "invoices": {
                "in_test_001": {
                    "id": "in_test_001",
                    "customer": "cus_test_001",
                    "subscription": "sub_test_001",
                    "status": "paid",
                    "amount_paid": 2900,
                    "currency": "usd",
                    "created": int(datetime.utcnow().timestamp()),
                    "lines": {
                        "data": [{
                            "description": "Pro Plan",
                            "amount": 2900,
                            "currency": "usd"
                        }]
                    }
                }
            },
            "payment_intents": {
                "pi_test_001": {
                    "id": "pi_test_001",
                    "customer": "cus_test_001",
                    "amount": 2900,
                    "currency": "usd",
                    "status": "succeeded",
                    "payment_method": "pm_test_001"
                }
            }
        }


class BillingFlowScenarios:
    """End-to-end billing flow test scenarios"""
    
    def __init__(self, framework: BillingTestFramework):
        self.framework = framework
        
    def test_subscription_creation_flow(self):
        """Test complete subscription creation workflow"""
        test_results = []
        
        # Mock Stripe API calls
        with patch('stripe.Customer.create') as mock_customer_create, \
             patch('stripe.Subscription.create') as mock_subscription_create, \
             patch('stripe.PaymentMethod.attach') as mock_pm_attach:
            
            # Setup mock responses
            mock_customer_create.return_value = Mock(
                id="cus_test_001",
                email="owner@company.com"
            )
            
            mock_subscription_create.return_value = Mock(
                id="sub_test_001",
                status="active",
                current_period_start=int(datetime.utcnow().timestamp()),
                current_period_end=int((datetime.utcnow() + timedelta(days=30)).timestamp())
            )
            
            mock_pm_attach.return_value = Mock(id="pm_test_001")
            
            try:
                # Test subscription creation
                headers = self.framework.auth_framework.get_auth_headers("team_owner")
                
                subscription_data = {
                    "team_id": "team-enterprise-001",
                    "plan": "pro",
                    "payment_method_id": "pm_test_001",
                    "billing_email": "owner@company.com"
                }
                
                response = self.framework.client.post(
                    "/billing-console/create-subscription",
                    json=subscription_data,
                    headers=headers
                )
                
                test_results.append({
                    "test": "subscription_creation_success",
                    "status": "PASS" if response.status_code == 200 else "FAIL",
                    "status_code": response.status_code,
                    "response_data": response.json() if response.status_code == 200 else None,
                    "description": "Successful subscription creation"
                })
                
                # Verify Stripe API calls were made
                assert mock_customer_create.called, "Customer creation should be called"
                assert mock_subscription_create.called, "Subscription creation should be called"
                
                test_results.append({
                    "test": "stripe_api_integration",
                    "status": "PASS",
                    "description": "Stripe API calls executed correctly"
                })
                
            except Exception as e:
                test_results.append({
                    "test": "subscription_creation_flow",
                    "status": "ERROR",
                    "error": str(e)
                })
                
        return test_results
        
    def test_payment_processing_flow(self):
        """Test payment processing and webhook handling"""
        test_results = []
        
        # Test successful payment webhook
        try:
            webhook_payload = {
                "type": "payment_intent.succeeded",
                "data": {
                    "object": {
                        "id": "pi_test_001",
                        "customer": "cus_test_001",
                        "amount": 2900,
                        "currency": "usd",
                        "status": "succeeded",
                        "metadata": {
                            "team_id": "team-enterprise-001",
                            "subscription_id": "sub_test_001"
                        }
                    }
                }
            }
            
            response = self.framework.client.post(
                "/billing-console/stripe-webhook",
                json=webhook_payload,
                headers={"stripe-signature": "test_signature"}
            )
            
            test_results.append({
                "test": "payment_success_webhook",
                "status": "PASS" if response.status_code == 200 else "FAIL",
                "status_code": response.status_code,
                "description": "Payment success webhook processing"
            })
            
        except Exception as e:
            test_results.append({
                "test": "payment_success_webhook",
                "status": "ERROR",
                "error": str(e)
            })
            
        # Test failed payment webhook
        try:
            webhook_payload = {
                "type": "payment_intent.payment_failed",
                "data": {
                    "object": {
                        "id": "pi_test_002",
                        "customer": "cus_test_001",
                        "amount": 2900,
                        "currency": "usd",
                        "status": "requires_payment_method",
                        "last_payment_error": {
                            "code": "card_declined",
                            "message": "Your card was declined."
                        },
                        "metadata": {
                            "team_id": "team-enterprise-001",
                            "subscription_id": "sub_test_001"
                        }
                    }
                }
            }
            
            response = self.framework.client.post(
                "/billing-console/stripe-webhook",
                json=webhook_payload,
                headers={"stripe-signature": "test_signature"}
            )
            
            test_results.append({
                "test": "payment_failure_webhook",
                "status": "PASS" if response.status_code == 200 else "FAIL",
                "status_code": response.status_code,
                "description": "Payment failure webhook processing"
            })
            
        except Exception as e:
            test_results.append({
                "test": "payment_failure_webhook",
                "status": "ERROR",
                "error": str(e)
            })
            
        return test_results
        
    def test_invoice_generation_flow(self):
        """Test automated invoice generation and PDF creation"""
        test_results = []
        
        # Mock ReportLab PDF generation
        with patch('server.invoice_management_api.REPORTLAB_AVAILABLE', True), \
             patch('server.invoice_management_api.SimpleDocTemplate') as mock_doc:
            
            mock_doc.return_value.build = Mock()
            
            try:
                headers = self.framework.auth_framework.get_auth_headers("team_owner")
                
                # Test invoice generation
                invoice_data = {
                    "team_id": "team-enterprise-001",
                    "billing_period_start": datetime.utcnow().strftime("%Y-%m-%d"),
                    "billing_period_end": (datetime.utcnow() + timedelta(days=30)).strftime("%Y-%m-%d"),
                    "line_items": [
                        {
                            "description": "Pro Plan Subscription",
                            "quantity": 1,
                            "unit_price": 29.00,
                            "total": 29.00
                        }
                    ]
                }
                
                response = self.framework.client.post(
                    "/invoicing/generate",
                    json=invoice_data,
                    headers=headers
                )
                
                test_results.append({
                    "test": "invoice_generation",
                    "status": "PASS" if response.status_code == 200 else "FAIL",
                    "status_code": response.status_code,
                    "description": "Invoice generation from billing data"
                })
                
                if response.status_code == 200:
                    invoice_response = response.json()
                    invoice_id = invoice_response.get("invoice_id")
                    
                    # Test PDF generation
                    pdf_response = self.framework.client.get(
                        f"/invoicing/{invoice_id}/pdf",
                        headers=headers
                    )
                    
                    test_results.append({
                        "test": "pdf_generation",
                        "status": "PASS" if pdf_response.status_code == 200 else "FAIL",
                        "status_code": pdf_response.status_code,
                        "description": "PDF invoice generation"
                    })
                    
                    # Test invoice email sending
                    email_response = self.framework.client.post(
                        f"/invoicing/{invoice_id}/send",
                        json={"recipient_email": "owner@company.com"},
                        headers=headers
                    )
                    
                    test_results.append({
                        "test": "invoice_email_sending",
                        "status": "PASS" if email_response.status_code == 200 else "FAIL",
                        "status_code": email_response.status_code,
                        "description": "Invoice email delivery"
                    })
                    
            except Exception as e:
                test_results.append({
                    "test": "invoice_generation_flow",
                    "status": "ERROR",
                    "error": str(e)
                })
                
        return test_results
        
    def test_billing_cycle_automation(self):
        """Test automated billing cycle processing"""
        test_results = []
        
        try:
            headers = self.framework.auth_framework.get_auth_headers("admin")
            
            # Setup billing cycle
            cycle_data = {
                "team_id": "team-enterprise-001",
                "billing_frequency": "monthly",
                "next_billing_date": (datetime.utcnow() + timedelta(days=1)).strftime("%Y-%m-%d"),
                "auto_charge": True
            }
            
            response = self.framework.client.post(
                "/invoicing/billing-cycle/team-enterprise-001",
                json=cycle_data,
                headers=headers
            )
            
            test_results.append({
                "test": "billing_cycle_setup",
                "status": "PASS" if response.status_code == 200 else "FAIL",
                "status_code": response.status_code,
                "description": "Billing cycle configuration"
            })
            
            # Test billing cycle processing
            process_response = self.framework.client.post(
                "/invoicing/process-billing-cycles",
                headers=headers
            )
            
            test_results.append({
                "test": "billing_cycle_processing",
                "status": "PASS" if process_response.status_code == 200 else "FAIL",
                "status_code": process_response.status_code,
                "description": "Automated billing cycle execution"
            })
            
        except Exception as e:
            test_results.append({
                "test": "billing_cycle_automation",
                "status": "ERROR",
                "error": str(e)
            })
            
        return test_results
        
    def test_payment_failure_handling(self):
        """Test payment failure detection and retry logic"""
        test_results = []
        
        try:
            headers = self.framework.auth_framework.get_auth_headers("admin")
            
            # Simulate payment failure
            failure_data = {
                "payment_intent_id": "pi_test_failed_001",
                "customer_id": "cus_test_001",
                "team_id": "team-enterprise-001",
                "amount": 2900,
                "currency": "usd",
                "failure_reason": "card_declined",
                "failure_message": "Your card was declined.",
                "retry_count": 0
            }
            
            # Test failure recording
            response = self.framework.client.post(
                "/invoicing/payment-failures",
                json=failure_data,
                headers=headers
            )
            
            test_results.append({
                "test": "payment_failure_recording",
                "status": "PASS" if response.status_code == 200 else "FAIL",
                "status_code": response.status_code,
                "description": "Payment failure tracking"
            })
            
            # Test retry logic
            if response.status_code == 200:
                failure_response = response.json()
                failure_id = failure_response.get("failure_id")
                
                retry_response = self.framework.client.post(
                    f"/invoicing/retry-payment/{failure_id}",
                    headers=headers
                )
                
                test_results.append({
                    "test": "payment_retry_logic",
                    "status": "PASS" if retry_response.status_code == 200 else "FAIL",
                    "status_code": retry_response.status_code,
                    "description": "Payment retry mechanism"
                })
                
        except Exception as e:
            test_results.append({
                "test": "payment_failure_handling",
                "status": "ERROR",
                "error": str(e)
            })
            
        return test_results


class BillingTestRunner:
    """Test runner for comprehensive billing flow testing"""
    
    def __init__(self):
        self.framework = BillingTestFramework()
        self.scenarios = BillingFlowScenarios(self.framework)
        
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all billing flow tests and return comprehensive results"""
        print("💳 Starting End-to-End Billing Flow Testing...")
        
        # Setup test environment
        self.framework.auth_framework.setup_test_database()
        self.framework.auth_framework.generate_test_tokens()
        self.framework.setup_mock_stripe_data()
        
        # Run all test scenarios
        results = {
            "test_run_id": f"billing_test_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            "timestamp": datetime.utcnow().isoformat(),
            "test_categories": {}
        }
        
        # Subscription creation tests
        print("  📝 Running subscription creation tests...")
        results["test_categories"]["subscription_creation"] = self.scenarios.test_subscription_creation_flow()
        
        # Payment processing tests
        print("  💰 Running payment processing tests...")
        results["test_categories"]["payment_processing"] = self.scenarios.test_payment_processing_flow()
        
        # Invoice generation tests
        print("  📄 Running invoice generation tests...")
        results["test_categories"]["invoice_generation"] = self.scenarios.test_invoice_generation_flow()
        
        # Billing cycle automation tests
        print("  🔄 Running billing cycle tests...")
        results["test_categories"]["billing_automation"] = self.scenarios.test_billing_cycle_automation()
        
        # Payment failure handling tests
        print("  ⚠️ Running payment failure tests...")
        results["test_categories"]["failure_handling"] = self.scenarios.test_payment_failure_handling()
        
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
        
        print(f"✅ Billing testing complete: {passed_tests}/{total_tests} tests passed ({results['summary']['pass_rate']}%)")
        
        return results


# Test execution functions
def run_billing_tests():
    """Main function to run billing flow tests"""
    runner = BillingTestRunner()
    results = runner.run_all_tests()
    
    # Save results
    with open("billing_test_results.json", "w") as f:
        json.dump(results, f, indent=2)
        
    return results


if __name__ == "__main__":
    # Run tests when script is executed directly
    test_results = run_billing_tests()
    print(f"\n📊 Test results saved to billing_test_results.json")
    print(f"🎯 Overall pass rate: {test_results['summary']['pass_rate']}%")
