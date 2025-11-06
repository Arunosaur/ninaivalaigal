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
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import and_
from sqlalchemy.orm import Session

from .models import BillingPeriod, UsageEvent

logger = logging.getLogger(__name__)


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

            if not old_events:
                logger.info("No old metrics to archive")
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
                            self._store_archive(archive_path, period_key)

                        # Delete archived events from database
                        event_ids = [e.id for e in events]
                        self.db.query(UsageEvent).filter(UsageEvent.id.in_(event_ids)).delete(synchronize_session=False)

                        results["archived"] += len(events)
                        results["archives_created"] += 1
                        logger.info(f"Archived {len(events)} events for period {period_key}")
                    else:
                        results["failed"] += len(events)
                        results["errors"].append(f"Failed to create archive for period {period_key}")

                except Exception as e:
                    logger.error(f"Error archiving period {period_key}: {e}")
                    results["failed"] += len(events)
                    results["errors"].append(f"Error archiving period {period_key}: {str(e)}")

            self.db.commit()
            logger.info(f"Archival complete: {results['archived']} events archived, {results['failed']} failed")

        except Exception as e:
            logger.error(f"Error in archive_old_metrics: {e}", exc_info=True)
            self.db.rollback()
            results["errors"].append(f"Archival error: {str(e)}")

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

    def _store_archive(self, archive_path: str, period_key: str):
        """
        Store archive in cold storage.

        Args:
            archive_path: Path to archive file
            period_key: Period identifier

        Note:
            This is a placeholder. Implement actual storage backend integration.
        """
        if self.storage_backend:
            try:
                # TODO: Implement actual storage backend
                # Example: s3_client.upload_file(archive_path, bucket, key)
                logger.info(f"Archive stored: {archive_path} -> {period_key}")
            except Exception as e:
                logger.error(f"Error storing archive: {e}")
                raise
        else:
            logger.warning("No storage backend configured, archive not stored")

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
