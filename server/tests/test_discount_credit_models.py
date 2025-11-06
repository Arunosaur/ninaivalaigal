#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""
Unit tests for Discount & Credit Models (US#157, SPEC-026 Phase 1)

⚠️  DEPRECATED: These tests are for old SPEC-026 models.
SPEC-147 has replaced these models with a unified billing architecture.

New models:
- DiscountCode → server.billing.models.DiscountCode (SPEC-147)
- DiscountCodeUsage → server.billing.models.DiscountApplication (SPEC-147)
- TeamCredit → server.billing.models.CreditBalance (SPEC-147)

TODO: Update tests to use SPEC-147 models or mark as deprecated.
"""

from datetime import datetime, timedelta
from uuid import uuid4

import pytest

# New SPEC-147 imports
from server.billing.models import DiscountApplication, DiscountCode

# Old SPEC-026 imports - models removed
from server.database.models import (
    CreditTransaction,
    CreditTransactionType,
    Organization,
    Team,
    TeamCredit,
    User,
)


class TestDiscountCode:
    """Tests for DiscountCode model"""

    def test_discount_code_creation_percent(self, db_session):
        """Test creating a percentage discount code"""
        user = User(
            id=uuid4(),
            email="admin@example.com",
            hashed_password="hashed",
        )
        db_session.add(user)
        db_session.commit()

        discount = DiscountCode(
            code="SAVE10",
            percent_off=10,
            expires_at=datetime.utcnow() + timedelta(days=30),
            usage_limit=100,
            created_by=user.id,
        )
        db_session.add(discount)
        db_session.commit()

        assert discount.id is not None
        assert discount.code == "SAVE10"
        assert discount.percent_off == 10
        assert discount.amount_off is None
        assert discount.usage_limit == 100
        assert discount.used_count == 0
        assert discount.is_active is True

    def test_discount_code_creation_amount(self, db_session):
        """Test creating a fixed amount discount code"""
        discount = DiscountCode(
            code="FIXED50",
            amount_off=5000,  # $50.00 in cents
            expires_at=datetime.utcnow() + timedelta(days=30),
        )
        db_session.add(discount)
        db_session.commit()

        assert discount.percent_off is None
        assert discount.amount_off == 5000

    def test_discount_code_unique_constraint(self, db_session):
        """Test that discount codes must be unique"""
        discount1 = DiscountCode(
            code="UNIQUE10",
            percent_off=10,
        )
        db_session.add(discount1)
        db_session.commit()

        discount2 = DiscountCode(
            code="UNIQUE10",  # Duplicate code
            percent_off=20,
        )
        db_session.add(discount2)

        with pytest.raises(Exception):  # IntegrityError
            db_session.commit()

    def test_discount_code_type_check(self, db_session):
        """Test that either percent_off or amount_off must be set, but not both"""
        # Test: neither set
        discount = DiscountCode(code="INVALID")
        db_session.add(discount)

        with pytest.raises(Exception):  # CheckConstraint violation
            db_session.commit()

    def test_discount_code_relationship(self, db_session):
        """Test DiscountCode relationship with User and DiscountCodeUsage"""
        user = User(
            id=uuid4(),
            email="admin@example.com",
            hashed_password="hashed",
        )
        db_session.add(user)
        db_session.commit()

        discount = DiscountCode(
            code="TEST10",
            percent_off=10,
            created_by=user.id,
        )
        db_session.add(discount)
        db_session.commit()

        assert discount.creator.id == user.id


class TestTeamCredit:
    """Tests for TeamCredit model"""

    def test_team_credit_creation(self, db_session):
        """Test creating a TeamCredit record"""
        user = User(
            id=uuid4(),
            email="admin@example.com",
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

        credit = TeamCredit(
            team_id=team.id,
            amount=100.00,
            reason="Welcome bonus",
            granted_by=user.id,
        )
        db_session.add(credit)
        db_session.commit()

        assert credit.id is not None
        assert credit.team_id == team.id
        assert credit.amount == 100.00
        assert credit.used_amount == 0
        assert credit.reason == "Welcome bonus"

    def test_team_credit_relationship(self, db_session):
        """Test TeamCredit relationship with Team"""
        team = Team(
            id=uuid4(),
            name="Test Team",
            organization_id=None,
        )
        db_session.add(team)
        db_session.commit()

        credit = TeamCredit(
            team_id=team.id,
            amount=50.00,
            reason="Test credit",
        )
        db_session.add(credit)
        db_session.commit()

        assert credit.team.id == team.id

    def test_team_credit_target_check(self, db_session):
        """Test that either team_id or org_id must be set, but not both"""
        # Test: neither set
        credit = TeamCredit(amount=100.00, reason="Test")
        db_session.add(credit)

        with pytest.raises(Exception):  # CheckConstraint violation
            db_session.commit()

    def test_team_credit_amount_constraints(self, db_session):
        """Test that amount must be positive and used_amount <= amount"""
        team = Team(
            id=uuid4(),
            name="Test Team",
            organization_id=None,
        )
        db_session.add(team)
        db_session.commit()

        # Test: negative amount
        credit = TeamCredit(team_id=team.id, amount=-10.00, reason="Test")
        db_session.add(credit)

        with pytest.raises(Exception):  # CheckConstraint violation
            db_session.commit()

    def test_team_credit_used_amount_constraint(self, db_session):
        """Test that used_amount cannot exceed amount"""
        team = Team(
            id=uuid4(),
            name="Test Team",
            organization_id=None,
        )
        db_session.add(team)
        db_session.commit()

        credit = TeamCredit(
            team_id=team.id,
            amount=100.00,
            used_amount=150.00,  # Exceeds amount
            reason="Test",
        )
        db_session.add(credit)

        with pytest.raises(Exception):  # CheckConstraint violation
            db_session.commit()


class TestCreditTransaction:
    """Tests for CreditTransaction model"""

    def test_credit_transaction_creation(self, db_session):
        """Test creating a CreditTransaction record"""
        user = User(
            id=uuid4(),
            email="admin@example.com",
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

        credit = TeamCredit(
            team_id=team.id,
            amount=100.00,
            reason="Test credit",
            granted_by=user.id,
        )
        db_session.add(credit)
        db_session.commit()

        transaction = CreditTransaction(
            team_credit_id=credit.id,
            transaction_type=CreditTransactionType.DEDUCT.value,
            amount=25.00,
            balance_before=100.00,
            balance_after=75.00,
            reason="Invoice payment",
            performed_by=user.id,
        )
        db_session.add(transaction)
        db_session.commit()

        assert transaction.id is not None
        assert transaction.transaction_type == CreditTransactionType.DEDUCT.value
        assert transaction.balance_before == 100.00
        assert transaction.balance_after == 75.00

    def test_credit_transaction_relationship(self, db_session):
        """Test CreditTransaction relationship with TeamCredit"""
        team = Team(
            id=uuid4(),
            name="Test Team",
            organization_id=None,
        )
        db_session.add(team)
        db_session.commit()

        credit = TeamCredit(
            team_id=team.id,
            amount=100.00,
            reason="Test credit",
        )
        db_session.add(credit)
        db_session.commit()

        transaction = CreditTransaction(
            team_credit_id=credit.id,
            transaction_type=CreditTransactionType.GRANT.value,
            amount=50.00,
            balance_before=0.00,
            balance_after=50.00,
            reason="Granted credit",
        )
        db_session.add(transaction)
        db_session.commit()

        assert credit.transactions[0].id == transaction.id

    def test_credit_transaction_balance_consistency(self, db_session):
        """Test that balance_after is calculated correctly"""
        team = Team(
            id=uuid4(),
            name="Test Team",
            organization_id=None,
        )
        db_session.add(team)
        db_session.commit()

        credit = TeamCredit(
            team_id=team.id,
            amount=100.00,
            reason="Test credit",
        )
        db_session.add(credit)
        db_session.commit()

        # Test: incorrect balance calculation
        transaction = CreditTransaction(
            team_credit_id=credit.id,
            transaction_type=CreditTransactionType.DEDUCT.value,
            amount=25.00,
            balance_before=100.00,
            balance_after=80.00,  # Should be 75.00
            reason="Invalid balance",
        )
        db_session.add(transaction)

        with pytest.raises(Exception):  # CheckConstraint violation
            db_session.commit()

    def test_credit_transaction_type_enum(self):
        """Test CreditTransactionType enum values"""
        assert CreditTransactionType.GRANT.value == "grant"
        assert CreditTransactionType.DEDUCT.value == "deduct"
        assert CreditTransactionType.EXPIRE.value == "expire"
        assert CreditTransactionType.REFUND.value == "refund"


class TestDiscountCodeUsage:
    """Tests for DiscountCodeUsage model

    ⚠️  DEPRECATED: DiscountCodeUsage model removed in SPEC-147.
    Use DiscountApplication from server.billing.models instead.
    """

    @pytest.mark.skip(reason="DiscountCodeUsage model removed - use SPEC-147 DiscountApplication")
    def test_discount_code_usage_creation(self, db_session):
        """Test creating a DiscountCodeUsage record"""
        team = Team(
            id=uuid4(),
            name="Test Team",
            organization_id=None,
        )
        db_session.add(team)
        db_session.commit()

        discount = DiscountCode(
            code="SAVE10",
            percent_off=10,
        )
        db_session.add(discount)
        db_session.commit()

        usage = DiscountCodeUsage(
            discount_code_id=discount.id,
            team_id=team.id,
            amount_discounted=10.00,
        )
        db_session.add(usage)
        db_session.commit()

        assert usage.id is not None
        assert usage.discount_code_id == discount.id
        assert usage.team_id == team.id
        assert usage.amount_discounted == 10.00

    @pytest.mark.skip(reason="DiscountCodeUsage model removed - use SPEC-147 DiscountApplication")
    def test_discount_code_usage_relationship(self, db_session):
        """Test DiscountCodeUsage relationship with DiscountCode"""
        discount = DiscountCode(
            code="TEST10",
            percent_off=10,
        )
        db_session.add(discount)
        db_session.commit()

        team = Team(
            id=uuid4(),
            name="Test Team",
            organization_id=None,
        )
        db_session.add(team)
        db_session.commit()

        usage = DiscountCodeUsage(
            discount_code_id=discount.id,
            team_id=team.id,
            amount_discounted=10.00,
        )
        db_session.add(usage)
        db_session.commit()

        assert discount.usages[0].id == usage.id

    @pytest.mark.skip(reason="DiscountCodeUsage model removed - use SPEC-147 DiscountApplication")
    def test_discount_code_usage_target_check(self, db_session):
        """Test that either team_id or org_id must be set, but not both"""
        discount = DiscountCode(
            code="TEST10",
            percent_off=10,
        )
        db_session.add(discount)
        db_session.commit()

        # Test: neither set
        usage = DiscountCodeUsage(
            discount_code_id=discount.id,
            amount_discounted=10.00,
        )
        db_session.add(usage)

        with pytest.raises(Exception):  # CheckConstraint violation
            db_session.commit()
