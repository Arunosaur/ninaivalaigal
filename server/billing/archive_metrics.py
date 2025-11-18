#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# SPEC-147: Usage Data Archival
# Developer D - January 2025
#
# BILL-014: Usage Data Archival

"""
Archival service for old usage metrics.

Archives usage events older than retention period to cold storage.
"""

import gzip
import json
import logging
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import and_
from sqlalchemy.orm import Session

from .models import BillingPeriod, UsageEvent

logger = logging.getLogger(__name__)

# Import Prometheus metrics if available
try:
    from .prometheus_metrics import (
        archive_duration_seconds,
        archive_eligible_events,
        archive_events_archived,
        archive_operations_total,
        archive_size_bytes,
    )

    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False

    # Create dummy metrics
    class DummyMetric:
        def labels(self, *args, **kwargs):
            return self

        def inc(self, *args, **kwargs):
            pass

        def observe(self, *args, **kwargs):
            pass

        def set(self, *args, **kwargs):
            pass

    archive_operations_total = DummyMetric()
    archive_events_archived = DummyMetric()
    archive_size_bytes = DummyMetric()
    archive_duration_seconds = DummyMetric()
    archive_eligible_events = DummyMetric()


class MetricsArchivalService:
    """
    Service for archiving old usage metrics to cold storage.
    """

    DEFAULT_RETENTION_DAYS = 90
    ARCHIVE_BATCH_SIZE = 1000

    def __init__(
        self, db: Session, storage_backend: Optional[Any] = None, retention_days: int = DEFAULT_RETENTION_DAYS
    ):
        """
        Initialize archival service.

        Args:
            db: Database session
            storage_backend: Storage backend (S3, etc.) - optional
            retention_days: Days to retain data before archiving
        """
        self.db = db
        self.storage_backend = storage_backend
        self.retention_days = retention_days

    def archive_old_metrics(self, archive_date: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Archive usage events older than retention period.

        Args:
            archive_date: Date threshold for archiving (default: retention_days ago)

        Returns:
            Archival results
        """
        if archive_date is None:
            archive_date = datetime.now(timezone.utc) - timedelta(days=self.retention_days)

        results = {
            "archived": 0,
            "failed": 0,
            "archives_created": 0,
            "errors": [],
        }

        start_time = time.time()

        try:
            # Get usage events older than archive_date
            old_events = (
                self.db.query(UsageEvent)
                .filter(
                    UsageEvent.recorded_at < archive_date, UsageEvent.processed == True  # Only archive processed events
                )
                .order_by(UsageEvent.recorded_at)
                .limit(self.ARCHIVE_BATCH_SIZE)
                .all()
            )

            # Update Prometheus metrics
            if PROMETHEUS_AVAILABLE:
                archive_eligible_events.set(len(old_events))

            if not old_events:
                logger.info("No old metrics to archive")
                if PROMETHEUS_AVAILABLE:
                    archive_operations_total.labels(operation_type="archive", status="no_events").inc()
                return results

            # Group events by billing period for efficient archiving
            events_by_period: Dict[str, List[UsageEvent]] = {}
            for event in old_events:
                period_key = str(event.billing_period_id) if event.billing_period_id else "none"
                if period_key not in events_by_period:
                    events_by_period[period_key] = []
                events_by_period[period_key].append(event)

            # Archive each period's events
            for period_key, events in events_by_period.items():
                try:
                    archive_data = self._prepare_archive_data(events)
                    archive_path = self._create_archive(archive_data, period_key)

                    if archive_path:
                        # Store archive
                        if self.storage_backend:
                            archive_key = self._store_archive(archive_path, period_key)

                            # Index archive for fast lookup
                            try:
                                from .archive_index import ArchiveIndex

                                index = ArchiveIndex(self.db)
                                index.index_archive(
                                    archive_key=archive_key or archive_path,
                                    billing_period_id=period_key if period_key != "none" else None,
                                    event_count=len(events),
                                    archive_size_bytes=(
                                        os.path.getsize(archive_path) if os.path.exists(archive_path) else None
                                    ),
                                    storage_backend="s3" if self.storage_backend and archive_key else "local",
                                    metadata={"archived_at": archive_data.get("archived_at")},
                                )
                            except Exception as e:
                                logger.warning(f"Failed to index archive: {e}")
                        else:
                            archive_key = archive_path

                        # Delete archived events from database
                        event_ids = [e.id for e in events]
                        self.db.query(UsageEvent).filter(UsageEvent.id.in_(event_ids)).delete(synchronize_session=False)

                        results["archived"] += len(events)
                        results["archives_created"] += 1

                        # Update Prometheus metrics
                        if PROMETHEUS_AVAILABLE:
                            archive_events_archived.labels(billing_period_id=period_key).inc(len(events))
                            archive_operations_total.labels(operation_type="archive", status="success").inc()
                            # Get archive file size if available
                            import os

                            if os.path.exists(archive_path):
                                archive_size = os.path.getsize(archive_path)
                                archive_size_bytes.labels(archive_key=period_key).set(archive_size)

                        logger.info(f"Archived {len(events)} events for period {period_key}")
                    else:
                        results["failed"] += len(events)
                        results["errors"].append(f"Failed to create archive for period {period_key}")

                except Exception as e:
                    logger.error(f"Error archiving period {period_key}: {e}")
                    results["failed"] += len(events)
                    results["errors"].append(f"Error archiving period {period_key}: {str(e)}")

            self.db.commit()

            # Update Prometheus metrics
            duration = time.time() - start_time
            if PROMETHEUS_AVAILABLE:
                archive_duration_seconds.labels(operation_type="archive").observe(duration)
                if results["failed"] > 0:
                    archive_operations_total.labels(operation_type="archive", status="partial_failure").inc()
                elif results["archived"] > 0:
                    archive_operations_total.labels(operation_type="archive", status="success").inc()

            logger.info(f"Archival complete: {results['archived']} events archived, {results['failed']} failed")

        except Exception as e:
            logger.error(f"Error in archive_old_metrics: {e}", exc_info=True)
            self.db.rollback()
            results["errors"].append(f"Archival error: {str(e)}")

            # Update Prometheus metrics for failure
            if PROMETHEUS_AVAILABLE:
                archive_operations_total.labels(operation_type="archive", status="failure").inc()
                duration = time.time() - start_time
                archive_duration_seconds.labels(operation_type="archive").observe(duration)

        return results

    def _prepare_archive_data(self, events: List[UsageEvent]) -> Dict[str, Any]:
        """
        Prepare events data for archiving.

        Args:
            events: List of usage events

        Returns:
            Archive data dictionary
        """
        archive_data = {
            "version": "1.0",
            "archived_at": datetime.now(timezone.utc).isoformat(),
            "event_count": len(events),
            "events": [
                {
                    "id": str(event.id),
                    "billing_account_id": str(event.billing_account_id),
                    "billing_period_id": str(event.billing_period_id) if event.billing_period_id else None,
                    "resource_type": event.resource_type,
                    "quantity": float(event.quantity),
                    "recorded_at": event.recorded_at.isoformat(),
                    "metadata": event.event_metadata,
                }
                for event in events
            ],
        }

        return archive_data

    def _create_archive(self, archive_data: Dict[str, Any], period_key: str) -> Optional[str]:
        """
        Create compressed archive file.

        Args:
            archive_data: Archive data dictionary
            period_key: Period identifier

        Returns:
            Archive file path or None
        """
        try:
            import os
            import tempfile

            # Create temporary archive file
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            archive_filename = f"usage_metrics_{period_key}_{timestamp}.json.gz"

            temp_dir = tempfile.gettempdir()
            archive_path = os.path.join(temp_dir, archive_filename)

            # Compress and write archive
            with gzip.open(archive_path, "wt", encoding="utf-8") as f:
                json.dump(archive_data, f, indent=2)

            logger.debug(f"Created archive: {archive_path}")
            return archive_path

        except Exception as e:
            logger.error(f"Error creating archive: {e}")
            return None

    def _store_archive(self, archive_path: str, period_key: str) -> str:
        """
        Store archive in cold storage.

        Args:
            archive_path: Path to archive file
            period_key: Period identifier

        Returns:
            Archive key (S3 key or local path)
        """
        if not self.storage_backend:
            logger.warning("No storage backend configured, archive not stored")
            return archive_path

        try:
            # Generate S3 key with date-based path for organization
            from datetime import datetime

            now = datetime.now(timezone.utc)
            date_path = now.strftime("%Y/%m")
            archive_key = (
                f"usage_metrics/{date_path}/usage_metrics_{period_key}_{now.strftime('%Y%m%d_%H%M%S')}.json.gz"
            )

            # Upload to storage backend
            if hasattr(self.storage_backend, "upload_archive"):
                success = self.storage_backend.upload_archive(archive_path, archive_key)
                if success:
                    logger.info(f"Archive stored: {archive_path} -> {archive_key}")
                    return archive_key
                else:
                    raise Exception(f"Failed to upload archive to storage backend")
            else:
                # Fallback for custom storage backends
                logger.info(f"Archive stored: {archive_path} -> {period_key}")
                return archive_path
        except Exception as e:
            logger.error(f"Error storing archive: {e}")
            raise

    def get_archive_stats(self) -> Dict[str, Any]:
        """
        Get archival statistics.

        Returns:
            Archive statistics
        """
        archive_date = datetime.now(timezone.utc) - timedelta(days=self.retention_days)

        total_old_events = (
            self.db.query(UsageEvent)
            .filter(UsageEvent.recorded_at < archive_date, UsageEvent.processed == True)
            .count()
        )

        return {
            "retention_days": self.retention_days,
            "archive_threshold_date": archive_date.isoformat(),
            "events_eligible_for_archive": total_old_events,
            "storage_backend_configured": self.storage_backend is not None,
        }
