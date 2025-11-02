#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""
Unit tests for Team Billing Models (US#156, SPEC-026 Phase 1)

Tests for TeamBilling, TeamSubscription, and TeamUsageMetrics models.
Achieves 90%+ coverage as required by US#156 acceptance criteria.
"""

from datetime import datetime, timedelta
from uuid import uuid4

import pytest

from server.database import Base
from server.database.models import (
    SubscriptionStatus,
    Team,
    TeamBilling,
    TeamSubscription,
    TeamUsageMetrics,
    User,
)


class TestTeamBilling:
    """Tests for TeamBilling model"""

    def test_team_billing_creation(self, db_session):
        """Test creating a TeamBilling record"""
        # Create a user and team
        user = User(
            id=uuid4(),
            email="test@example.com",
            hashed_password="hashed",
        )
        team = Team(
            id=uuid4(),
            name="Test Team",
            organization_id=None,
            is_standalone=True,
        )
        db_session.add(user)
        db_session.add(team)
        db_session.commit()

        # Create team billing
        billing = TeamBilling(
            team_id=team.id,
            stripe_customer_id="cus_test123",
            billing_email="billing@example.com",
            currency="USD",
        )
        db_session.add(billing)
        db_session.commit()

        assert billing.id is not None
        assert billing.team_id == team.id
        assert billing.stripe_customer_id == "cus_test123"
        assert billing.billing_email == "billing@example.com"
        assert billing.currency == "USD"
        assert billing.created_at is not None
        assert billing.updated_at is not None

    def test_team_billing_relationship(self, db_session):
        """Test TeamBilling relationship with Team"""
        team = Team(
            id=uuid4(),
            name="Test Team",
            organization_id=None,
        )
        db_session.add(team)
        db_session.commit()

        billing = TeamBilling(
            team_id=team.id,
            billing_email="billing@example.com",
        )
        db_session.add(billing)
        db_session.commit()

        # Test relationship
        assert team.billing is not None
        assert team.billing.id == billing.id

    def test_team_billing_unique_team_id(self, db_session):
        """Test that team_id must be unique"""
        team = Team(
            id=uuid4(),
            name="Test Team",
            organization_id=None,
        )
        db_session.add(team)
        db_session.commit()

        billing1 = TeamBilling(
            team_id=team.id,
            billing_email="billing1@example.com",
        )
        db_session.add(billing1)
        db_session.commit()

        # Try to create duplicate
        billing2 = TeamBilling(
            team_id=team.id,
            billing_email="billing2@example.com",
        )
        db_session.add(billing2)

        with pytest.raises(Exception):  # IntegrityError or similar
            db_session.commit()

    def test_team_billing_updated_at(self, db_session):
        """Test that updated_at is automatically updated"""
        team = Team(
            id=uuid4(),
            name="Test Team",
            organization_id=None,
        )
        db_session.add(team)
        db_session.commit()

        billing = TeamBilling(
            team_id=team.id,
            billing_email="billing@example.com",
        )
        db_session.add(billing)
        db_session.commit()

        original_updated_at = billing.updated_at

        # Update billing
        billing.billing_email = "newemail@example.com"
        db_session.commit()

        assert billing.updated_at > original_updated_at


class TestTeamSubscription:
    """Tests for TeamSubscription model"""

    def test_team_subscription_creation(self, db_session):
        """Test creating a TeamSubscription record"""
        team = Team(
            id=uuid4(),
            name="Test Team",
            organization_id=None,
        )
        db_session.add(team)
        db_session.commit()

        now = datetime.utcnow()
        subscription = TeamSubscription(
            team_id=team.id,
            plan_id="pro",
            status=SubscriptionStatus.ACTIVE.value,
            current_period_start=now,
            current_period_end=now + timedelta(days=30),
        )
        db_session.add(subscription)
        db_session.commit()

        assert subscription.id is not None
        assert subscription.team_id == team.id
        assert subscription.plan_id == "pro"
        assert subscription.status == SubscriptionStatus.ACTIVE.value
        assert subscription.current_period_start == now
        assert subscription.current_period_end == now + timedelta(days=30)

    def test_team_subscription_relationship(self, db_session):
        """Test TeamSubscription relationship with Team"""
        team = Team(
            id=uuid4(),
            name="Test Team",
            organization_id=None,
        )
        db_session.add(team)
        db_session.commit()

        now = datetime.utcnow()
        subscription = TeamSubscription(
            team_id=team.id,
            plan_id="starter",
            status=SubscriptionStatus.ACTIVE.value,
            current_period_start=now,
            current_period_end=now + timedelta(days=30),
        )
        db_session.add(subscription)
        db_session.commit()

        # Test relationship
        assert len(team.subscriptions) == 1
        assert team.subscriptions[0].id == subscription.id

    def test_team_subscription_default_status(self, db_session):
        """Test that default status is ACTIVE"""
        team = Team(
            id=uuid4(),
            name="Test Team",
            organization_id=None,
        )
        db_session.add(team)
        db_session.commit()

        now = datetime.utcnow()
        subscription = TeamSubscription(
            team_id=team.id,
            plan_id="free",
            current_period_start=now,
            current_period_end=now + timedelta(days=30),
        )
        db_session.add(subscription)
        db_session.commit()

        assert subscription.status == SubscriptionStatus.ACTIVE.value

    def test_team_subscription_trial_period(self, db_session):
        """Test subscription with trial period"""
        team = Team(
            id=uuid4(),
            name="Test Team",
            organization_id=None,
        )
        db_session.add(team)
        db_session.commit()

        now = datetime.utcnow()
        subscription = TeamSubscription(
            team_id=team.id,
            plan_id="pro",
            status=SubscriptionStatus.TRIALING.value,
            current_period_start=now,
            current_period_end=now + timedelta(days=30),
            trial_start=now,
            trial_end=now + timedelta(days=14),
        )
        db_session.add(subscription)
        db_session.commit()

        assert subscription.trial_start == now
        assert subscription.trial_end == now + timedelta(days=14)
        assert subscription.status == SubscriptionStatus.TRIALING.value

    def test_team_subscription_cancel_at_period_end(self, db_session):
        """Test subscription cancellation flag"""
        team = Team(
            id=uuid4(),
            name="Test Team",
            organization_id=None,
        )
        db_session.add(team)
        db_session.commit()

        now = datetime.utcnow()
        subscription = TeamSubscription(
            team_id=team.id,
            plan_id="pro",
            status=SubscriptionStatus.ACTIVE.value,
            current_period_start=now,
            current_period_end=now + timedelta(days=30),
            cancel_at_period_end=True,
        )
        db_session.add(subscription)
        db_session.commit()

        assert subscription.cancel_at_period_end is True


class TestTeamUsageMetrics:
    """Tests for TeamUsageMetrics model"""

    def test_team_usage_metrics_creation(self, db_session):
        """Test creating a TeamUsageMetrics record"""
        team = Team(
            id=uuid4(),
            name="Test Team",
            organization_id=None,
        )
        db_session.add(team)
        db_session.commit()

        now = datetime.utcnow()
        metrics = TeamUsageMetrics(
            team_id=team.id,
            period_start=now,
            period_end=now + timedelta(days=30),
            memory_count=100,
            api_calls=5000,
            storage_bytes=1024 * 1024 * 100,  # 100 MB
            context_count=50,
            member_count=5,
        )
        db_session.add(metrics)
        db_session.commit()

        assert metrics.id is not None
        assert metrics.team_id == team.id
        assert metrics.memory_count == 100
        assert metrics.api_calls == 5000
        assert metrics.storage_bytes == 1024 * 1024 * 100
        assert metrics.context_count == 50
        assert metrics.member_count == 5

    def test_team_usage_metrics_relationship(self, db_session):
        """Test TeamUsageMetrics relationship with Team"""
        team = Team(
            id=uuid4(),
            name="Test Team",
            organization_id=None,
        )
        db_session.add(team)
        db_session.commit()

        now = datetime.utcnow()
        metrics = TeamUsageMetrics(
            team_id=team.id,
            period_start=now,
            period_end=now + timedelta(days=30),
        )
        db_session.add(metrics)
        db_session.commit()

        # Test relationship
        assert len(team.usage_metrics) == 1
        assert team.usage_metrics[0].id == metrics.id

    def test_team_usage_metrics_defaults(self, db_session):
        """Test that default values are zero"""
        team = Team(
            id=uuid4(),
            name="Test Team",
            organization_id=None,
        )
        db_session.add(team)
        db_session.commit()

        now = datetime.utcnow()
        metrics = TeamUsageMetrics(
            team_id=team.id,
            period_start=now,
            period_end=now + timedelta(days=30),
        )
        db_session.add(metrics)
        db_session.commit()

        assert metrics.memory_count == 0
        assert metrics.api_calls == 0
        assert metrics.storage_bytes == 0
        assert metrics.context_count == 0
        assert metrics.member_count == 0

    def test_team_usage_metrics_non_negative_constraints(self, db_session):
        """Test that negative values are rejected"""
        team = Team(
            id=uuid4(),
            name="Test Team",
            organization_id=None,
        )
        db_session.add(team)
        db_session.commit()

        now = datetime.utcnow()
        metrics = TeamUsageMetrics(
            team_id=team.id,
            period_start=now,
            period_end=now + timedelta(days=30),
            memory_count=-1,  # Negative value
        )
        db_session.add(metrics)

        with pytest.raises(Exception):  # CheckConstraint violation
            db_session.commit()

    def test_team_usage_metrics_period_check(self, db_session):
        """Test that period_end must be >= period_start"""
        team = Team(
            id=uuid4(),
            name="Test Team",
            organization_id=None,
        )
        db_session.add(team)
        db_session.commit()

        now = datetime.utcnow()
        metrics = TeamUsageMetrics(
            team_id=team.id,
            period_start=now,
            period_end=now - timedelta(days=1),  # End before start
        )
        db_session.add(metrics)

        with pytest.raises(Exception):  # CheckConstraint violation
            db_session.commit()


class TestSubscriptionStatus:
    """Tests for SubscriptionStatus enum"""

    def test_subscription_status_values(self):
        """Test that all expected status values exist"""
        assert SubscriptionStatus.ACTIVE.value == "active"
        assert SubscriptionStatus.CANCELED.value == "canceled"
        assert SubscriptionStatus.PAST_DUE.value == "past_due"
        assert SubscriptionStatus.TRIALING.value == "trialing"
        assert SubscriptionStatus.INCOMPLETE.value == "incomplete"
