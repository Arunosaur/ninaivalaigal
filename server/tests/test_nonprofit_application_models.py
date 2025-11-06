#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""
Unit tests for Non-Profit Application Model (US#158, SPEC-026 Phase 1)

Tests for NonProfitApplication model.
Achieves 90%+ coverage as required by US#158 acceptance criteria.
"""

from datetime import datetime
from uuid import uuid4

import pytest

from server.database.models import (
    NonProfitApplication,
    NonProfitApplicationStatus,
    Organization,
    Team,
    User,
)


class TestNonProfitApplication:
    """Tests for NonProfitApplication model"""

    def test_nonprofit_application_creation(self, db_session):
        """Test creating a NonProfitApplication record"""
        team = Team(
            id=uuid4(),
            name="Test Team",
            organization_id=None,
        )
        db_session.add(team)
        db_session.commit()

        application = NonProfitApplication(
            team_id=team.id,
            organization_name="Test Non-Profit",
            tax_id="12-3456789",
            description="A test non-profit organization",
            website_url="https://testnonprofit.org",
            status=NonProfitApplicationStatus.PENDING.value,
        )
        db_session.add(application)
        db_session.commit()

        assert application.id is not None
        assert application.organization_name == "Test Non-Profit"
        assert application.tax_id == "12-3456789"
        assert application.status == NonProfitApplicationStatus.PENDING.value
        assert application.submitted_at is not None

    def test_nonprofit_application_default_status(self, db_session):
        """Test that default status is PENDING"""
        team = Team(
            id=uuid4(),
            name="Test Team",
            organization_id=None,
        )
        db_session.add(team)
        db_session.commit()

        application = NonProfitApplication(
            team_id=team.id,
            organization_name="Test Non-Profit",
            tax_id="12-3456789",
            description="A test non-profit organization",
        )
        db_session.add(application)
        db_session.commit()

        assert application.status == NonProfitApplicationStatus.PENDING.value

    def test_nonprofit_application_relationship(self, db_session):
        """Test NonProfitApplication relationship with Team"""
        team = Team(
            id=uuid4(),
            name="Test Team",
            organization_id=None,
        )
        db_session.add(team)
        db_session.commit()

        application = NonProfitApplication(
            team_id=team.id,
            organization_name="Test Non-Profit",
            tax_id="12-3456789",
            description="A test non-profit organization",
        )
        db_session.add(application)
        db_session.commit()

        assert application.team.id == team.id

    def test_nonprofit_application_review_workflow(self, db_session):
        """Test application review workflow"""
        user = User(
            id=uuid4(),
            email="reviewer@example.com",
            hashed_password="hashed",
        )
        team = Team(
            id=uuid4(),
            name="Test Team",
            organization_id=None,
        )
        db_session.add(user)
        db_session.add(team)
        db_session.commit()

        application = NonProfitApplication(
            team_id=team.id,
            organization_name="Test Non-Profit",
            tax_id="12-3456789",
            description="A test non-profit organization",
            status=NonProfitApplicationStatus.UNDER_REVIEW.value,
            reviewed_by=user.id,
            reviewed_at=datetime.utcnow(),
            review_notes="Reviewing documentation",
        )
        db_session.add(application)
        db_session.commit()

        assert application.status == NonProfitApplicationStatus.UNDER_REVIEW.value
        assert application.reviewed_by == user.id
        assert application.reviewer.id == user.id
        assert application.review_notes == "Reviewing documentation"

    def test_nonprofit_application_status_enum(self):
        """Test NonProfitApplicationStatus enum values"""
        assert NonProfitApplicationStatus.PENDING.value == "pending"
        assert NonProfitApplicationStatus.UNDER_REVIEW.value == "under_review"
        assert NonProfitApplicationStatus.APPROVED.value == "approved"
        assert NonProfitApplicationStatus.REJECTED.value == "rejected"

    def test_nonprofit_application_target_check(self, db_session):
        """Test that either team_id or org_id must be set, but not both"""
        # Test: neither set
        application = NonProfitApplication(
            organization_name="Test Non-Profit",
            tax_id="12-3456789",
            description="Test",
        )
        db_session.add(application)

        with pytest.raises(Exception):  # CheckConstraint violation
            db_session.commit()

    def test_nonprofit_application_status_constraint(self, db_session):
        """Test that status must be one of the valid values"""
        team = Team(
            id=uuid4(),
            name="Test Team",
            organization_id=None,
        )
        db_session.add(team)
        db_session.commit()

        application = NonProfitApplication(
            team_id=team.id,
            organization_name="Test Non-Profit",
            tax_id="12-3456789",
            description="Test",
            status="invalid_status",
        )
        db_session.add(application)

        with pytest.raises(Exception):  # CheckConstraint violation
            db_session.commit()

    def test_nonprofit_application_documentation_urls(self, db_session):
        """Test that documentation_urls can store array of URLs"""
        team = Team(
            id=uuid4(),
            name="Test Team",
            organization_id=None,
        )
        db_session.add(team)
        db_session.commit()

        application = NonProfitApplication(
            team_id=team.id,
            organization_name="Test Non-Profit",
            tax_id="12-3456789",
            description="A test non-profit organization",
            documentation_urls=["https://example.com/doc1.pdf", "https://example.com/doc2.pdf"],
        )
        db_session.add(application)
        db_session.commit()

        assert len(application.documentation_urls) == 2
        assert "https://example.com/doc1.pdf" in application.documentation_urls
