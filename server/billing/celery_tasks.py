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

Note: Database backup tasks (including backup from replicas) are typically
handled via cron jobs rather than Celery. See scripts/database/backup-from-replica.sh
for backup implementation. US#955: DB-REPL-006: Backup from Replicas & Disaster Recovery.
"""

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
from uuid import UUID

from celery import Task
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from .archive_metrics import MetricsArchivalService
from .celery_app import celery_app
from .invoice_generation import InvoiceGenerationService
from .models import AccountStatus, BillingAccount, BillingPeriod
from .payment_transfer import PaymentTransferService
from .quota_enforcement import QuotaEnforcementService
from .quota_notifications import QuotaNotificationService
from .stripe_service import StripeService
from .usage_metering import UsageMeteringService
from .weekly_cost_summary import WeeklyCostSummaryService

logger = logging.getLogger(__name__)

# Event stream integration
try:
    import os
    import sys

    # Add shared directory to path if needed
    shared_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "shared")
    if os.path.exists(shared_path) and shared_path not in sys.path:
        sys.path.insert(0, shared_path)

    from events import EventMetadata, EventPublisher, EventType

    EVENT_STREAM_ENABLED = True
except ImportError:
    logger.warning("Event stream integration not available. Install shared/events module.")
    EventPublisher = None
    EventType = None
    EventMetadata = None
    EVENT_STREAM_ENABLED = False

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


def get_event_publisher():
    """Get event publisher instance"""
    if not EVENT_STREAM_ENABLED or EventPublisher is None:
        return None

    import os

    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    publisher = EventPublisher(redis_url=redis_url)
    return publisher


def publish_event_sync(event_type, source_service, payload, metadata=None):
    """Publish event synchronously (for use in Celery tasks)"""
    if not EVENT_STREAM_ENABLED:
        return None

    try:
        publisher = get_event_publisher()
        if publisher:
            # Run async publish in sync context
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(publisher.connect())
                event_id = loop.run_until_complete(
                    publisher.publish(
                        event_type=event_type,
                        source_service=source_service,
                        payload=payload,
                        metadata=metadata or EventMetadata(),
                    )
                )
                loop.run_until_complete(publisher.disconnect())
                return event_id
            finally:
                loop.close()
    except Exception as e:
        logger.warning(f"Failed to publish event {event_type.value}: {e}")
        return None


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

        # Publish event for usage aggregation
        if EVENT_STREAM_ENABLED:
            publish_event_sync(
                event_type=EventType.USAGE_RECORDED,
                source_service="billing-service",
                payload={
                    "billing_account_id": str(billing_account_id) if billing_account_id else None,
                    "processed_count": processed if not billing_account_id else 1,
                    "aggregation_type": "hourly",
                },
            )

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

        # Publish event for Stripe sync
        if EVENT_STREAM_ENABLED and billing_account_id:
            publish_event_sync(
                event_type=EventType.SUBSCRIPTION_UPDATED,
                source_service="billing-service",
                payload={
                    "billing_account_id": str(billing_account_id),
                    "sync_type": "hourly",
                },
            )

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

        # Publish event for invoice generation
        if EVENT_STREAM_ENABLED:
            publish_event_sync(
                event_type=EventType.INVOICE_GENERATED,
                source_service="billing-service",
                payload={
                    "billing_period_id": str(billing_period_id) if billing_period_id else None,
                    "invoices_created": results.get("created", 0),
                    "invoices_processed": results.get("processed", 0),
                    "errors": results.get("errors", 0),
                },
            )

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


@celery_app.task(
    bind=True,
    base=DatabaseTask,
    name="server.billing.celery_tasks.retry_failed_payment",
    max_retries=1,
    default_retry_delay=300,  # 5 minutes
)
def retry_failed_payment(self, subscription_id: str, invoice_id: str, amount: float, retry_count: int):
    """
    Retry a failed payment (US#165: Celery task for scheduled payment retries).

    This task is scheduled by the webhook handler when a payment fails.
    It will retry the payment and schedule the next retry if needed.

    Args:
        subscription_id: Stripe subscription ID
        invoice_id: Stripe invoice ID
        amount: Invoice amount
        retry_count: Current retry attempt (0-3)
    """
    try:
        db = self.db
        stripe_service = StripeService(db)

        # Call the dunning handler with the retry count
        result = stripe_service._handle_failed_payment_dunning(
            subscription_id=subscription_id,
            invoice_id=invoice_id,
            amount=amount,
            retry_count=retry_count,
        )

        db.commit()
        logger.info(
            f"Payment retry task completed for invoice {invoice_id}, retry {retry_count + 1}",
            extra={"invoice_id": invoice_id, "retry_count": retry_count, "result": result},
        )

        return {"success": True, **result}

    except Exception as exc:
        logger.error(
            f"Error in payment retry task for invoice {invoice_id}: {exc}",
            exc_info=True,
            extra={"invoice_id": invoice_id, "retry_count": retry_count},
        )
        db.rollback()
        raise self.retry(exc=exc)


@celery_app.task(
    bind=True,
    base=DatabaseTask,
    name="server.billing.celery_tasks.archive_old_metrics",
    max_retries=3,
    default_retry_delay=300,
)
def archive_old_metrics(self):
    """
    Archive old usage metrics to cold storage.

    BILL-014: Archives usage events older than retention period (default: 90 days).
    """
    try:
        db = self.db
        archive_service = MetricsArchivalService(db, retention_days=90)

        results = archive_service.archive_old_metrics()

        db.commit()
        logger.info(f"Archived old metrics: {results}")

        return {"success": True, **results}

    except Exception as exc:
        logger.error(f"Error archiving old metrics: {exc}", exc_info=True)
        db.rollback()
        raise self.retry(exc=exc)


@celery_app.task(
    bind=True,
    base=DatabaseTask,
    name="server.billing.celery_tasks.generate_weekly_cost_summary",
    max_retries=2,
    default_retry_delay=300,
)
def generate_weekly_cost_summary(self):
    """
    Generate weekly cost summary report.

    SPEC-120: Weekly cost summary automation.
    Runs every Monday morning to generate previous week's cost summary.
    """
    try:
        db = self.db
        summary_service = WeeklyCostSummaryService(db)

        # Generate summary for previous week
        summary = summary_service.generate_weekly_summary()

        # Generate markdown report
        markdown_report = summary_service.generate_markdown_report(summary)

        # Export to cost exporter format
        exporter_events = summary_service.export_to_cost_exporter_format(summary)

        # Log summary
        logger.info(
            f"Weekly cost summary generated: Total=${summary['total_cost']:.2f}, "
            f"Services={len(summary['costs_by_service'])}, "
            f"ROI={summary['spec_099_roi']['cost_reduction_percent']:.1f}%"
        )

        # TODO: Send notifications (email, Slack, etc.)
        # TODO: Store report in storage backend

        return {
            "success": True,
            "summary": summary,
            "markdown_report": markdown_report,
            "exporter_events": exporter_events,
        }

    except Exception as exc:
        logger.error(f"Error generating weekly cost summary: {exc}", exc_info=True)
        db.rollback()
        raise self.retry(exc=exc)
