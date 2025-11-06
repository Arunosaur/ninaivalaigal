#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# SPEC-147: Celery Tasks for Billing System
# Developer D - January 2025
#
# BILL-007: Celery Worker Architecture

"""
Celery tasks for SPEC-147 billing system.

Provides async task processing for billing operations.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
from uuid import UUID

from celery import Task
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from .celery_app import celery_app
from .invoice_generation import InvoiceGenerationService
from .models import AccountStatus, BillingAccount, BillingPeriod
from .payment_transfer import PaymentTransferService
from .quota_enforcement import QuotaEnforcementService
from .quota_notifications import QuotaNotificationService
from .stripe_service import StripeService
from .usage_metering import UsageMeteringService

logger = logging.getLogger(__name__)

# Database session factory
DATABASE_URL = None
engine = None
SessionLocal = None


def get_database_url():
    """Get database URL from environment"""
    global DATABASE_URL
    if DATABASE_URL is None:
        import os

        DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/ninaivalaigal")
    return DATABASE_URL


def get_db_session():
    """Get database session"""
    global engine, SessionLocal
    if engine is None:
        db_url = get_database_url()
        engine = create_engine(db_url, pool_pre_ping=True)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()


class DatabaseTask(Task):
    """Base task class with database session management"""

    _db = None

    @property
    def db(self):
        if self._db is None:
            self._db = get_db_session()
        return self._db

    def after_return(self, *args, **kwargs):
        """Close database session after task completion"""
        if self._db:
            try:
                self._db.close()
            except Exception:
                pass
            finally:
                self._db = None


@celery_app.task(
    bind=True,
    base=DatabaseTask,
    name="server.billing.celery_tasks.aggregate_usage_metrics",
    max_retries=3,
    default_retry_delay=60,
)
def aggregate_usage_metrics(self, billing_account_id: Optional[str] = None):
    """
    Aggregate usage metrics for billing accounts.

    Args:
        billing_account_id: Optional billing account ID to process specific account
    """
    try:
        db = self.db
        usage_service = UsageMeteringService(db)

        if billing_account_id:
            # Process specific account
            account_id = UUID(billing_account_id)
            account = db.query(BillingAccount).filter(BillingAccount.id == account_id).first()

            if account:
                # Get current billing period and aggregate
                now = datetime.now(timezone.utc)
                period = (
                    db.query(BillingPeriod)
                    .filter(
                        BillingPeriod.billing_account_id == account.id,
                        BillingPeriod.period_start <= now,
                        BillingPeriod.period_end >= now,
                        BillingPeriod.status == "active",
                    )
                    .first()
                )

                if period:
                    # Aggregate usage for all resource types
                    for resource_type in ["storage", "retrieval", "token"]:
                        usage_service.get_current_usage(
                            billing_account_id=account.id, billing_period_id=period.id, resource_type=resource_type
                        )

                db.commit()
                logger.info(f"Aggregated usage metrics for account {billing_account_id}")
        else:
            # Process all active accounts
            accounts = (
                db.query(BillingAccount)
                .filter(BillingAccount.status == AccountStatus.ACTIVE.value, BillingAccount.deleted_at.is_(None))
                .all()
            )

            processed = 0
            for account in accounts:
                try:
                    now = datetime.now(timezone.utc)
                    period = (
                        db.query(BillingPeriod)
                        .filter(
                            BillingPeriod.billing_account_id == account.id,
                            BillingPeriod.period_start <= now,
                            BillingPeriod.period_end >= now,
                            BillingPeriod.status == "active",
                        )
                        .first()
                    )

                    if period:
                        for resource_type in ["storage", "retrieval", "token"]:
                            usage_service.get_current_usage(
                                billing_account_id=account.id, billing_period_id=period.id, resource_type=resource_type
                            )
                        processed += 1
                except Exception as e:
                    logger.error(f"Error processing account {account.id}: {e}")
                    db.rollback()

            db.commit()
            logger.info(f"Aggregated usage metrics for {processed} accounts")

        return {"success": True, "processed": 1 if billing_account_id else processed}

    except Exception as exc:
        logger.error(f"Error aggregating usage metrics: {exc}", exc_info=True)
        db.rollback()
        raise self.retry(exc=exc)


@celery_app.task(
    bind=True,
    base=DatabaseTask,
    name="server.billing.celery_tasks.sync_stripe_subscriptions",
    max_retries=3,
    default_retry_delay=60,
)
def sync_stripe_subscriptions(self, billing_account_id: Optional[str] = None):
    """
    Sync Stripe subscription status with local billing accounts.

    Args:
        billing_account_id: Optional billing account ID to sync specific account
    """
    try:
        db = self.db
        stripe_service = StripeService(db)

        if billing_account_id:
            account_id = UUID(billing_account_id)
            account = db.query(BillingAccount).filter(BillingAccount.id == account_id).first()

            if account:
                stripe_service.sync_subscription_status(account.id)
                db.commit()
                logger.info(f"Synced Stripe subscription for account {billing_account_id}")
        else:
            # Sync all accounts with Stripe customers
            from .models import StripeCustomer

            customers = db.query(StripeCustomer).all()

            synced = 0
            for customer in customers:
                try:
                    stripe_service.sync_subscription_status(customer.billing_account_id)
                    synced += 1
                except Exception as e:
                    logger.error(f"Error syncing account {customer.billing_account_id}: {e}")
                    db.rollback()

            db.commit()
            logger.info(f"Synced {synced} Stripe subscriptions")

        return {"success": True, "synced": 1 if billing_account_id else synced}

    except Exception as exc:
        logger.error(f"Error syncing Stripe subscriptions: {exc}", exc_info=True)
        db.rollback()
        raise self.retry(exc=exc)


@celery_app.task(
    bind=True,
    base=DatabaseTask,
    name="server.billing.celery_tasks.generate_monthly_invoices",
    max_retries=3,
    default_retry_delay=300,  # 5 minutes for invoice generation
)
def generate_monthly_invoices(self, billing_period_id: Optional[str] = None):
    """
    Generate monthly invoices for billing accounts.

    Args:
        billing_period_id: Optional billing period ID to generate invoices for
    """
    try:
        db = self.db
        invoice_service = InvoiceGenerationService(db)

        if billing_period_id:
            period_id = UUID(billing_period_id)
            results = invoice_service.generate_monthly_invoices(billing_period_id=period_id)
        else:
            # Generate for last month's billing period
            from .models import BillingPeriodStatus

            now = datetime.now(timezone.utc)
            last_month = now.replace(day=1) - timedelta(days=1)

            period = (
                db.query(BillingPeriod)
                .filter(
                    BillingPeriod.period_end >= last_month, BillingPeriod.status == BillingPeriodStatus.INVOICED.value
                )
                .order_by(BillingPeriod.period_end.desc())
                .first()
            )

            if period:
                results = invoice_service.generate_monthly_invoices(billing_period_id=period.id)
            else:
                results = {"processed": 0, "created": 0, "errors": 0}

        db.commit()
        logger.info(f"Generated monthly invoices: {results}")

        return {"success": True, **results}

    except Exception as exc:
        logger.error(f"Error generating monthly invoices: {exc}", exc_info=True)
        db.rollback()
        raise self.retry(exc=exc)


@celery_app.task(
    bind=True,
    base=DatabaseTask,
    name="server.billing.celery_tasks.send_quota_warnings",
    max_retries=2,
    default_retry_delay=60,
)
def send_quota_warnings(self):
    """
    Send quota warning notifications to accounts approaching limits.
    """
    try:
        db = self.db
        quota_service = QuotaEnforcementService(db, UsageMeteringService(db))
        notification_service = QuotaNotificationService(db)

        # Get all active billing accounts
        accounts = (
            db.query(BillingAccount)
            .filter(BillingAccount.status == AccountStatus.ACTIVE.value, BillingAccount.deleted_at.is_(None))
            .all()
        )

        notified = 0
        for account in accounts:
            try:
                now = datetime.now(timezone.utc)
                period = (
                    db.query(BillingPeriod)
                    .filter(
                        BillingPeriod.billing_account_id == account.id,
                        BillingPeriod.period_start <= now,
                        BillingPeriod.period_end >= now,
                        BillingPeriod.status == "active",
                    )
                    .first()
                )

                if period:
                    # Check quota status for all resources
                    from .models import ResourceType

                    for resource_type in [ResourceType.STORAGE, ResourceType.RETRIEVAL, ResourceType.TOKEN]:
                        status, percentage, block = quota_service.check_quota_status(
                            billing_account_id=account.id, billing_period_id=period.id, resource_type=resource_type
                        )

                        # Send warning if approaching limit (75%+)
                        if percentage >= 75 and not block:
                            notification_service.send_soft_warning(
                                billing_account_id=account.id, resource_type=resource_type, usage_percentage=percentage
                            )
                            notified += 1
            except Exception as e:
                logger.error(f"Error sending warning for account {account.id}: {e}")
                db.rollback()

        db.commit()
        logger.info(f"Sent quota warnings to {notified} accounts")

        return {"success": True, "notified": notified}

    except Exception as exc:
        logger.error(f"Error sending quota warnings: {exc}", exc_info=True)
        db.rollback()
        raise self.retry(exc=exc)


@celery_app.task(
    bind=True,
    base=DatabaseTask,
    name="server.billing.celery_tasks.process_payment_transfers",
    max_retries=2,
    default_retry_delay=60,
)
def process_payment_transfers(self):
    """
    Process payment transfer workflows and check grace periods.
    """
    try:
        db = self.db
        transfer_service = PaymentTransferService(db)

        results = transfer_service.process_all_grace_periods()

        db.commit()
        logger.info(f"Processed payment transfers: {results}")

        return {"success": True, **results}

    except Exception as exc:
        logger.error(f"Error processing payment transfers: {exc}", exc_info=True)
        db.rollback()
        raise self.retry(exc=exc)


@celery_app.task(
    bind=True,
    base=DatabaseTask,
    name="server.billing.celery_tasks.process_grace_periods",
    max_retries=2,
    default_retry_delay=60,
)
def process_grace_periods(self):
    """
    Process all active grace periods (alias for process_payment_transfers).
    """
    return process_payment_transfers.apply()
