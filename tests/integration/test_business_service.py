import pytest
import requests
from tests.config import CORE_API_BASE_URL
import os
import subprocess
import json

def get_pgbouncer_ip():
    """Get PgBouncer container IP dynamically"""
    try:
        result = subprocess.run(
            ["container", "inspect", "ninaivalaigal-dev-pgbouncer"],
            capture_output=True,
            text=True,
            check=True
        )
        data = json.loads(result.stdout)
        return data[0]['networks'][0]['address'].split('/')[0]
    except:
        return os.getenv('PGBOUNCER_IP', 'localhost')

# Use in your database URL
PGB_IP = get_pgbouncer_ip()
DATABASE_URL = f"postgresql://nina:dev_password_change_in_production@{PGB_IP}:6432/ninaivalaigal_dev"

@pytest.mark.integration
class TestBillingAndInvoices:
    """Test billing and invoice endpoints"""

    @pytest.fixture
    def auth_token(self):
        """Get auth token for authenticated requests"""
        # Signup
        requests.post(f"{CORE_API_BASE_URL}/auth/signup", json={
            "email": "billinguser@test.com",
            "password": "BillingPass123!",  # pragma: allowlist secret
            "name": "Billing User"
        })

        # Login
        response = requests.post(f"{CORE_API_BASE_URL}/auth/login", json={
            "email": "billinguser@test.com",
            "password": "BillingPass123!"  # pragma: allowlist secret
        })

        return response.json()["access_token"]

    def test_create_subscription(self, auth_token):
        """User can create a subscription"""
        response = requests.post(
            f"{CORE_API_BASE_URL}/billing/subscriptions",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"plan": "pro"}
        )
        assert response.status_code == 201
        data = response.json()
        assert data["plan"] == "pro"
        assert data["status"] == "active"

    def test_get_subscription(self, auth_token):
        """User can get their subscription"""
        # Create a subscription first
        requests.post(
            f"{CORE_API_BASE_URL}/billing/subscriptions",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"plan": "pro"}
        )

        response = requests.get(
            f"{CORE_API_BASE_URL}/billing/subscriptions",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data[0]["plan"] == "pro"

    def test_add_payment_method(self, auth_token):
        """User can add a payment method"""
        response = requests.post(
            f"{CORE_API_BASE_URL}/billing/payment-methods",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"token": "tok_visa"}
        )
        assert response.status_code == 201
        data = response.json()
        assert data["message"] == "Payment method added successfully"

    def test_get_invoices(self, auth_token):
        """User can get their invoices"""
        response = requests.get(
            f"{CORE_API_BASE_URL}/invoices",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        assert isinstance(response.json(), list)
