"""
End-to-End Testing for Team Workflows and Monetization
Tests complete user journeys from signup through billing
"""

import asyncio
import pytest
import uuid
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Test imports
from server.main import app
from server.database import Base, get_db
from server.models.standalone_teams import (
    StandaloneTeamManager, TeamInvitation, TeamMembership, TeamUpgradeHistory
)
from server.enhanced_signup_api import router as enhanced_signup_router
from server.standalone_teams_api import router as standalone_teams_router


class TestTeamWorkflowsE2E:
    """End-to-end tests for complete team workflows"""
    
    @pytest.fixture
    def client(self):
        """Test client with in-memory database"""
        # Create in-memory SQLite database for testing
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(bind=engine)
        TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
        def override_get_db():
            try:
                db = TestingSessionLocal()
                yield db
            finally:
                db.close()
        
        app.dependency_overrides[get_db] = override_get_db
        return TestClient(app)
    
    @pytest.fixture
    def mock_email_service(self):
        """Mock email service for testing"""
        with patch('server.enhanced_signup_api.send_team_invitation_email') as mock_email:
            mock_email.return_value = None
            yield mock_email
    
    @pytest.fixture
    def mock_stripe_service(self):
        """Mock Stripe service for billing tests"""
        with patch('stripe.Customer.create') as mock_customer, \
             patch('stripe.Subscription.create') as mock_subscription:
            
            mock_customer.return_value = Mock(id='cus_test123')
            mock_subscription.return_value = Mock(
                id='sub_test123',
                status='active',
                current_period_end=int((datetime.now() + timedelta(days=30)).timestamp())
            )
            yield {'customer': mock_customer, 'subscription': mock_subscription}


class TestViralGrowthJourney(TestTeamWorkflowsE2E):
    """Test complete viral growth journey"""
    
    def test_individual_to_team_creation_journey(self, client, mock_email_service):
        """Test: Individual user creates team and invites members"""
        
        # Step 1: User signs up with team creation
        signup_data = {
            "email": "founder@startup.com",
            "password": "securepass123",
            "name": "Jane Founder",
            "team_name": "Awesome Startup",
            "team_max_members": 10
        }
        
        response = client.post("/auth/signup/team-create", json=signup_data)
        assert response.status_code == 200
        
        signup_result = response.json()
        assert signup_result["success"] is True
        assert "team" in signup_result
        assert signup_result["team"]["name"] == "Awesome Startup"
        assert signup_result["team"]["role"] == "admin"
        
        team_id = signup_result["team"]["id"]
        jwt_token = signup_result["user"]["jwt_token"]
        
        # Step 2: Admin invites team members
        invite_data = {
            "email": "developer@startup.com",
            "role": "contributor"
        }
        
        response = client.post(
            f"/teams/{team_id}/invite",
            json=invite_data,
            headers={"Authorization": f"Bearer {jwt_token}"}
        )
        assert response.status_code == 200
        
        invitation_result = response.json()
        assert invitation_result["email"] == "developer@startup.com"
        assert invitation_result["role"] == "contributor"
        assert invitation_result["status"] == "pending"
        
        # Verify email was sent
        mock_email_service.assert_called_once()
        
        # Step 3: Invited user signs up and joins team
        invitation_token = invitation_result["id"]  # In real scenario, this comes from email
        
        join_signup_data = {
            "email": "developer@startup.com",
            "password": "devpass123",
            "name": "John Developer",
            "invitation_token": invitation_token
        }
        
        response = client.post("/auth/signup/team-join", json=join_signup_data)
        assert response.status_code == 200
        
        join_result = response.json()
        assert join_result["success"] is True
        assert join_result["team"]["name"] == "Awesome Startup"
        assert join_result["team"]["role"] == "contributor"
        
        # Step 4: Verify team members can be listed
        response = client.get(
            f"/teams/{team_id}/members",
            headers={"Authorization": f"Bearer {jwt_token}"}
        )
        assert response.status_code == 200
        
        members = response.json()
        assert len(members) == 2
        
        # Verify admin and contributor are both present
        roles = [member["role"] for member in members]
        assert "admin" in roles
        assert "contributor" in roles
    
    def test_team_growth_and_limit_scenarios(self, client, mock_email_service):
        """Test team growth approaching and hitting limits"""
        
        # Create team with 5-member limit
        signup_data = {
            "email": "admin@company.com",
            "password": "adminpass123",
            "name": "Team Admin",
            "team_name": "Growing Company",
            "team_max_members": 5
        }
        
        response = client.post("/auth/signup/team-create", json=signup_data)
        team_data = response.json()
        team_id = team_data["team"]["id"]
        jwt_token = team_data["user"]["jwt_token"]
        
        # Add 4 more members to reach capacity (5 total including admin)
        for i in range(4):
            invite_data = {
                "email": f"member{i+1}@company.com",
                "role": "contributor"
            }
            
            response = client.post(
                f"/teams/{team_id}/invite",
                json=invite_data,
                headers={"Authorization": f"Bearer {jwt_token}"}
            )
            assert response.status_code == 200
            
            # Simulate member joining
            invitation = response.json()
            join_data = {
                "email": f"member{i+1}@company.com",
                "password": f"pass{i+1}",
                "name": f"Member {i+1}",
                "invitation_token": invitation["id"]
            }
            
            response = client.post("/auth/signup/team-join", json=join_data)
            assert response.status_code == 200
        
        # Verify team is at capacity
        response = client.get(
            f"/teams/{team_id}/members",
            headers={"Authorization": f"Bearer {jwt_token}"}
        )
        members = response.json()
        assert len(members) == 5
        
        # Try to invite one more member (should fail or trigger upgrade)
        invite_data = {
            "email": "overflow@company.com",
            "role": "contributor"
        }
        
        response = client.post(
            f"/teams/{team_id}/invite",
            json=invite_data,
            headers={"Authorization": f"Bearer {jwt_token}"}
        )
        
        # Should either fail with capacity error or trigger upgrade flow
        assert response.status_code in [400, 402]  # Bad request or payment required


class TestConversionFunnelJourney(TestTeamWorkflowsE2E):
    """Test conversion from free to paid plans"""
    
    def test_free_to_paid_upgrade_journey(self, client, mock_stripe_service):
        """Test: Team upgrades from free to paid plan"""
        
        # Step 1: Create team on free plan
        signup_data = {
            "email": "ceo@startup.com",
            "password": "ceopass123",
            "name": "CEO Startup",
            "team_name": "Scaling Startup",
            "team_max_members": 5  # Free tier limit
        }
        
        response = client.post("/auth/signup/team-create", json=signup_data)
        team_data = response.json()
        team_id = team_data["team"]["id"]
        jwt_token = team_data["user"]["jwt_token"]
        
        # Step 2: Fill team to capacity (simulate growth)
        for i in range(4):  # Add 4 more to reach 5 total
            invite_data = {
                "email": f"employee{i+1}@startup.com",
                "role": "contributor"
            }
            
            client.post(
                f"/teams/{team_id}/invite",
                json=invite_data,
                headers={"Authorization": f"Bearer {jwt_token}"}
            )
        
        # Step 3: Attempt to add 6th member (trigger upgrade need)
        invite_data = {
            "email": "newbie@startup.com",
            "role": "contributor"
        }
        
        response = client.post(
            f"/teams/{team_id}/invite",
            json=invite_data,
            headers={"Authorization": f"Bearer {jwt_token}"}
        )
        
        # Should get capacity error
        assert response.status_code == 400
        error_data = response.json()
        assert "capacity" in error_data["detail"].lower()
        
        # Step 4: Upgrade team to Pro plan
        upgrade_data = {
            "organization_name": "Scaling Startup Inc",
            "domain": "scalingstartup.com",
            "size": "startup",
            "industry": "technology"
        }
        
        response = client.post(
            f"/teams/{team_id}/upgrade-to-org",
            json=upgrade_data,
            headers={"Authorization": f"Bearer {jwt_token}"}
        )
        assert response.status_code == 200
        
        upgrade_result = response.json()
        assert upgrade_result["success"] is True
        assert "organization" in upgrade_result
        
        # Verify Stripe was called for billing setup
        mock_stripe_service['customer'].assert_called_once()
    
    def test_upgrade_messaging_and_triggers(self, client):
        """Test upgrade prompts and messaging at various trigger points"""
        
        # Create team approaching limits
        signup_data = {
            "email": "manager@company.com",
            "password": "managerpass123",
            "name": "Team Manager",
            "team_name": "Growing Team",
            "team_max_members": 5
        }
        
        response = client.post("/auth/signup/team-create", json=signup_data)
        team_data = response.json()
        team_id = team_data["team"]["id"]
        jwt_token = team_data["user"]["jwt_token"]
        
        # Test 80% capacity trigger (4/5 members)
        for i in range(3):  # Add 3 more to reach 4 total
            invite_data = {
                "email": f"worker{i+1}@company.com",
                "role": "contributor"
            }
            
            client.post(
                f"/teams/{team_id}/invite",
                json=invite_data,
                headers={"Authorization": f"Bearer {jwt_token}"}
            )
        
        # Get team status (should show upgrade eligibility)
        response = client.get(
            "/teams/my",
            headers={"Authorization": f"Bearer {jwt_token}"}
        )
        assert response.status_code == 200
        
        team_status = response.json()
        usage_percentage = (team_status["current_members"] / team_status["max_members"]) * 100
        assert usage_percentage >= 80  # Should trigger upgrade messaging


class TestBillingIntegration(TestTeamWorkflowsE2E):
    """Test billing system integration"""
    
    @patch('stripe.Customer.create')
    @patch('stripe.Subscription.create')
    @patch('stripe.PaymentMethod.attach')
    def test_subscription_lifecycle(self, mock_attach, mock_subscription, mock_customer, client):
        """Test complete subscription lifecycle"""
        
        # Mock Stripe responses
        mock_customer.return_value = Mock(id='cus_test123')
        mock_subscription.return_value = Mock(
            id='sub_test123',
            status='active',
            current_period_end=int((datetime.now() + timedelta(days=30)).timestamp())
        )
        mock_attach.return_value = Mock(id='pm_test123')
        
        # Create team
        signup_data = {
            "email": "billing@company.com",
            "password": "billingpass123",
            "name": "Billing Admin",
            "team_name": "Billing Test Team",
            "team_max_members": 5
        }
        
        response = client.post("/auth/signup/team-create", json=signup_data)
        team_data = response.json()
        team_id = team_data["team"]["id"]
        jwt_token = team_data["user"]["jwt_token"]
        
        # Simulate subscription creation
        billing_data = {
            "plan": "team_pro",
            "payment_method_id": "pm_test123",
            "billing_email": "billing@company.com"
        }
        
        # This would be implemented in SPEC-026 billing API
        # For now, test the upgrade path that leads to billing
        upgrade_data = {
            "organization_name": "Billing Test Inc",
            "domain": "billingtest.com"
        }
        
        response = client.post(
            f"/teams/{team_id}/upgrade-to-org",
            json=upgrade_data,
            headers={"Authorization": f"Bearer {jwt_token}"}
        )
        
        assert response.status_code == 200
        
        # Verify upgrade was recorded
        upgrade_result = response.json()
        assert upgrade_result["success"] is True


class TestSecurityAndValidation(TestTeamWorkflowsE2E):
    """Test security aspects of team workflows"""
    
    def test_team_isolation(self, client):
        """Test that teams cannot access each other's data"""
        
        # Create two separate teams
        team1_data = {
            "email": "admin1@team1.com",
            "password": "team1pass",
            "name": "Team 1 Admin",
            "team_name": "Team One",
            "team_max_members": 5
        }
        
        team2_data = {
            "email": "admin2@team2.com",
            "password": "team2pass",
            "name": "Team 2 Admin",
            "team_name": "Team Two",
            "team_max_members": 5
        }
        
        # Create both teams
        response1 = client.post("/auth/signup/team-create", json=team1_data)
        response2 = client.post("/auth/signup/team-create", json=team2_data)
        
        team1_result = response1.json()
        team2_result = response2.json()
        
        team1_id = team1_result["team"]["id"]
        team2_id = team2_result["team"]["id"]
        team1_token = team1_result["user"]["jwt_token"]
        team2_token = team2_result["user"]["jwt_token"]
        
        # Try to access Team 2's members with Team 1's token
        response = client.get(
            f"/teams/{team2_id}/members",
            headers={"Authorization": f"Bearer {team1_token}"}
        )
        
        # Should be forbidden
        assert response.status_code == 403
        
        # Try to invite to Team 2 with Team 1's token
        invite_data = {
            "email": "hacker@malicious.com",
            "role": "admin"
        }
        
        response = client.post(
            f"/teams/{team2_id}/invite",
            json=invite_data,
            headers={"Authorization": f"Bearer {team1_token}"}
        )
        
        # Should be forbidden
        assert response.status_code == 403
    
    def test_invitation_token_security(self, client):
        """Test invitation token validation and security"""
        
        # Create team
        signup_data = {
            "email": "security@test.com",
            "password": "securitypass123",
            "name": "Security Tester",
            "team_name": "Security Test Team",
            "team_max_members": 5
        }
        
        response = client.post("/auth/signup/team-create", json=signup_data)
        team_data = response.json()
        jwt_token = team_data["user"]["jwt_token"]
        team_id = team_data["team"]["id"]
        
        # Create invitation
        invite_data = {
            "email": "invitee@test.com",
            "role": "contributor"
        }
        
        response = client.post(
            f"/teams/{team_id}/invite",
            json=invite_data,
            headers={"Authorization": f"Bearer {jwt_token}"}
        )
        
        invitation = response.json()
        valid_token = invitation["id"]
        
        # Test with invalid token
        invalid_join_data = {
            "email": "invitee@test.com",
            "password": "inviteepass123",
            "name": "Invitee",
            "invitation_token": "invalid_token_123"
        }
        
        response = client.post("/auth/signup/team-join", json=invalid_join_data)
        assert response.status_code == 400
        
        # Test with wrong email for valid token
        wrong_email_data = {
            "email": "wrong@test.com",
            "password": "wrongpass123",
            "name": "Wrong Person",
            "invitation_token": valid_token
        }
        
        response = client.post("/auth/signup/team-join", json=wrong_email_data)
        assert response.status_code == 400
        
        # Test with correct token and email
        correct_join_data = {
            "email": "invitee@test.com",
            "password": "inviteepass123",
            "name": "Correct Invitee",
            "invitation_token": valid_token
        }
        
        response = client.post("/auth/signup/team-join", json=correct_join_data)
        assert response.status_code == 200


class TestPerformanceAndScaling(TestTeamWorkflowsE2E):
    """Test performance aspects of team workflows"""
    
    def test_large_team_operations(self, client):
        """Test operations with larger teams"""
        
        # Create team with higher member limit
        signup_data = {
            "email": "performance@test.com",
            "password": "perfpass123",
            "name": "Performance Tester",
            "team_name": "Large Team Test",
            "team_max_members": 50
        }
        
        response = client.post("/auth/signup/team-create", json=signup_data)
        team_data = response.json()
        jwt_token = team_data["user"]["jwt_token"]
        team_id = team_data["team"]["id"]
        
        # Add multiple members quickly
        start_time = datetime.now()
        
        for i in range(10):  # Add 10 members
            invite_data = {
                "email": f"member{i}@largeteam.com",
                "role": "contributor"
            }
            
            response = client.post(
                f"/teams/{team_id}/invite",
                json=invite_data,
                headers={"Authorization": f"Bearer {jwt_token}"}
            )
            assert response.status_code == 200
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Should complete within reasonable time (adjust threshold as needed)
        assert duration < 5.0  # 5 seconds for 10 invitations
        
        # Test member list retrieval performance
        start_time = datetime.now()
        
        response = client.get(
            f"/teams/{team_id}/members",
            headers={"Authorization": f"Bearer {jwt_token}"}
        )
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        assert response.status_code == 200
        assert duration < 1.0  # Should load member list quickly


# Pytest configuration and fixtures
@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


if __name__ == "__main__":
    # Run tests with: python -m pytest tests/test_team_workflows_e2e.py -v
    pytest.main([__file__, "-v", "--tb=short"])
