#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""
Performance Benchmark Storage Service (US#409, SPEC-069)
Stores and retrieves benchmark results with historical tracking and regression detection
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

import structlog
from sqlalchemy import text
from sqlalchemy.orm import Session

logger = structlog.get_logger(__name__)


class BenchmarkStorage:
    """Service for storing and retrieving performance benchmark results"""

    def __init__(self, db_session: Session):
        """Initialize benchmark storage service"""
        self.db = db_session
        self.logger = logging.getLogger(__name__)

    def create_benchmark_run(
        self,
        run_type: str = "automated",
        environment: str = "development",
        commit_sha: Optional[str] = None,
        branch_name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> UUID:
        """
        Create a new benchmark run record

        Args:
            run_type: Type of run ('automated', 'manual', 'ci', 'scheduled')
            environment: Environment name ('production', 'staging', 'development', 'ci')
            commit_sha: Git commit SHA (optional)
            branch_name: Git branch name (optional)
            metadata: Additional metadata as dict (optional)

        Returns:
            UUID of the created run
        """
        try:
            run_id = uuid4()
            metadata_json = metadata or {}

            query = text(
                """
                INSERT INTO performance_benchmark_runs
                (run_id, run_type, environment, commit_sha, branch_name, metadata, status)
                VALUES (:run_id, :run_type, :environment, :commit_sha, :branch_name, :metadata, 'running')
                RETURNING run_id
            """
            )

            self.db.execute(
                query,
                {
                    "run_id": str(run_id),
                    "run_type": run_type,
                    "environment": environment,
                    "commit_sha": commit_sha,
                    "branch_name": branch_name,
                    "metadata": str(metadata_json).replace("'", '"'),  # Simple JSON conversion
                },
            )
            self.db.commit()

            self.logger.info(
                "Created benchmark run",
                run_id=str(run_id),
                run_type=run_type,
                environment=environment,
            )
            return run_id

        except Exception as e:
            self.db.rollback()
            self.logger.error("Failed to create benchmark run", error=str(e))
            raise

    def record_benchmark_result(
        self,
        run_id: UUID,
        metric_name: str,
        metric_category: str,
        metric_value: float,
        metric_unit: Optional[str] = None,
        target_value: Optional[float] = None,
        percentile_p50: Optional[float] = None,
        percentile_p95: Optional[float] = None,
        percentile_p99: Optional[float] = None,
        sample_count: int = 1,
        tags: Optional[Dict[str, Any]] = None,
    ) -> UUID:
        """
        Record a benchmark result for a metric

        Args:
            run_id: UUID of the benchmark run
            metric_name: Name of the metric (e.g., 'api_latency_p95_ms')
            metric_category: Category ('api', 'database', 'cache', 'graph', 'system')
            metric_value: Measured value
            metric_unit: Unit of measurement (optional)
            target_value: Target/threshold value (optional)
            percentile_p50: 50th percentile value (optional)
            percentile_p95: 95th percentile value (optional)
            percentile_p99: 99th percentile value (optional)
            sample_count: Number of samples (default: 1)
            tags: Additional tags as dict (optional)

        Returns:
            UUID of the created result
        """
        try:
            # Determine status based on target comparison
            status = "good"
            if target_value is not None:
                if metric_category in ["api", "database", "graph"]:
                    # For latency/time metrics, higher is worse
                    if metric_value > target_value * 1.1:  # 10% over target
                        status = "critical"
                    elif metric_value > target_value * 1.05:  # 5% over target
                        status = "warning"
                elif metric_category in ["cache", "system"]:
                    # For hit rate/throughput metrics, lower is worse
                    if metric_value < target_value * 0.9:  # 10% below target
                        status = "critical"
                    elif metric_value < target_value * 0.95:  # 5% below target
                        status = "warning"

            result_id = uuid4()
            tags_json = tags or {}

            query = text(
                """
                INSERT INTO performance_benchmark_results
                (result_id, run_id, metric_name, metric_category, metric_value, metric_unit,
                 target_value, status, percentile_p50, percentile_p95, percentile_p99,
                 sample_count, tags)
                VALUES (:result_id, :run_id, :metric_name, :metric_category, :metric_value, :metric_unit,
                        :target_value, :status, :percentile_p50, :percentile_p95, :percentile_p99,
                        :sample_count, :tags)
                RETURNING result_id
            """
            )

            self.db.execute(
                query,
                {
                    "result_id": str(result_id),
                    "run_id": str(run_id),
                    "metric_name": metric_name,
                    "metric_category": metric_category,
                    "metric_value": float(metric_value),
                    "metric_unit": metric_unit,
                    "target_value": float(target_value) if target_value else None,
                    "status": status,
                    "percentile_p50": float(percentile_p50) if percentile_p50 else None,
                    "percentile_p95": float(percentile_p95) if percentile_p95 else None,
                    "percentile_p99": float(percentile_p99) if percentile_p99 else None,
                    "sample_count": sample_count,
                    "tags": str(tags_json).replace("'", '"'),
                },
            )
            self.db.commit()

            self.logger.debug(
                "Recorded benchmark result",
                result_id=str(result_id),
                metric_name=metric_name,
                metric_value=metric_value,
            )
            return result_id

        except Exception as e:
            self.db.rollback()
            self.logger.error("Failed to record benchmark result", error=str(e))
            raise

    def complete_benchmark_run(self, run_id: UUID, status: str = "completed"):
        """Mark a benchmark run as completed"""
        try:
            query = text(
                """
                UPDATE performance_benchmark_runs
                SET status = :status
                WHERE run_id = :run_id
            """
            )

            self.db.execute(query, {"run_id": str(run_id), "status": status})
            self.db.commit()

            self.logger.info("Completed benchmark run", run_id=str(run_id), status=status)

        except Exception as e:
            self.db.rollback()
            self.logger.error("Failed to complete benchmark run", error=str(e))
            raise

    def compare_with_baseline(
        self,
        current_run_id: UUID,
        baseline_run_id: Optional[UUID] = None,
        regression_threshold: float = -5.0,
    ) -> List[Dict[str, Any]]:
        """
        Compare current run results with baseline run

        Args:
            current_run_id: UUID of current benchmark run
            baseline_run_id: UUID of baseline run (if None, uses most recent completed run)
            regression_threshold: Percentage change threshold for regression (default -5%)

        Returns:
            List of comparison results
        """
        try:
            # If no baseline specified, find most recent completed run in same environment
            if baseline_run_id is None:
                query = text(
                    """
                    SELECT run_id FROM performance_benchmark_runs
                    WHERE environment = (
                        SELECT environment FROM performance_benchmark_runs WHERE run_id = :current_run_id
                    )
                    AND run_timestamp < (
                        SELECT run_timestamp FROM performance_benchmark_runs WHERE run_id = :current_run_id
                    )
                    AND status = 'completed'
                    ORDER BY run_timestamp DESC
                    LIMIT 1
                """
                )

                result = self.db.execute(query, {"current_run_id": str(current_run_id)})
                row = result.fetchone()
                if row:
                    baseline_run_id = UUID(row[0])
                else:
                    self.logger.warning("No baseline run found for comparison", current_run_id=str(current_run_id))
                    return []

            # Get comparisons using the database function
            query = text(
                """
                SELECT
                    c.metric_name,
                    c.metric_category,
                    c.baseline_value,
                    c.current_value,
                    c.change_percent,
                    c.change_absolute,
                    c.is_regression,
                    c.regression_severity
                FROM performance_benchmark_comparisons c
                WHERE c.current_run_id = :current_run_id
                  AND c.baseline_run_id = :baseline_run_id
                ORDER BY c.is_regression DESC, ABS(c.change_percent) DESC
            """
            )

            result = self.db.execute(
                query,
                {
                    "current_run_id": str(current_run_id),
                    "baseline_run_id": str(baseline_run_id),
                },
            )

            comparisons = []
            for row in result.fetchall():
                comparisons.append(
                    {
                        "metric_name": row[0],
                        "metric_category": row[1],
                        "baseline_value": float(row[2]),
                        "current_value": float(row[3]),
                        "change_percent": float(row[4]),
                        "change_absolute": float(row[5]),
                        "is_regression": row[6],
                        "regression_severity": row[7],
                    }
                )

            return comparisons

        except Exception as e:
            self.logger.error("Failed to compare with baseline", error=str(e))
            return []

    def get_benchmark_history(
        self,
        metric_name: Optional[str] = None,
        metric_category: Optional[str] = None,
        environment: Optional[str] = None,
        days: int = 30,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Get historical benchmark results

        Args:
            metric_name: Filter by metric name (optional)
            metric_category: Filter by category (optional)
            environment: Filter by environment (optional)
            days: Number of days of history to retrieve (default: 30)
            limit: Maximum number of results (default: 100)

        Returns:
            List of historical benchmark results
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)

            conditions = ["r.run_timestamp >= :cutoff_date"]
            params = {"cutoff_date": cutoff_date}

            if metric_name:
                conditions.append("res.metric_name = :metric_name")
                params["metric_name"] = metric_name

            if metric_category:
                conditions.append("res.metric_category = :metric_category")
                params["metric_category"] = metric_category

            if environment:
                conditions.append("r.environment = :environment")
                params["environment"] = environment

            where_clause = " AND ".join(conditions)

            query = text(
                f"""
                SELECT
                    res.result_id,
                    res.run_id,
                    res.metric_name,
                    res.metric_category,
                    res.metric_value,
                    res.metric_unit,
                    res.target_value,
                    res.status,
                    r.run_timestamp,
                    r.environment,
                    r.commit_sha
                FROM performance_benchmark_results res
                JOIN performance_benchmark_runs r ON res.run_id = r.run_id
                WHERE {where_clause}
                ORDER BY r.run_timestamp DESC, res.metric_name
                LIMIT :limit
            """
            )

            params["limit"] = limit

            result = self.db.execute(query, params)

            history = []
            for row in result.fetchall():
                history.append(
                    {
                        "result_id": str(row[0]),
                        "run_id": str(row[1]),
                        "metric_name": row[2],
                        "metric_category": row[3],
                        "metric_value": float(row[4]),
                        "metric_unit": row[5],
                        "target_value": float(row[6]) if row[6] else None,
                        "status": row[7],
                        "run_timestamp": row[8].isoformat() if row[8] else None,
                        "environment": row[9],
                        "commit_sha": row[10],
                    }
                )

            return history

        except Exception as e:
            self.logger.error("Failed to get benchmark history", error=str(e))
            return []

    def detect_regressions(self, run_id: UUID, regression_threshold: float = -5.0) -> List[Dict[str, Any]]:
        """
        Detect regressions in benchmark run using database function

        Args:
            run_id: UUID of benchmark run to check
            regression_threshold: Percentage change threshold (default -5%)

        Returns:
            List of detected regressions
        """
        try:
            # First, we need to create comparisons for all metrics in the run
            # This will use the detect_benchmark_regression function
            query = text(
                """
                SELECT
                    res.metric_name,
                    res.metric_category,
                    res.metric_value as current_value,
                    (
                        SELECT r2.metric_value
                        FROM performance_benchmark_results r2
                        JOIN performance_benchmark_runs runs2 ON r2.run_id = runs2.run_id
                        WHERE r2.metric_name = res.metric_name
                          AND r2.metric_category = res.metric_category
                          AND runs2.environment = (
                              SELECT environment
                              FROM performance_benchmark_runs
                              WHERE run_id = :run_id
                          )
                          AND runs2.run_timestamp < (
                              SELECT run_timestamp
                              FROM performance_benchmark_runs
                              WHERE run_id = :run_id
                          )
                          AND runs2.status = 'completed'
                        ORDER BY runs2.run_timestamp DESC
                        LIMIT 1
                    ) as baseline_value
                FROM performance_benchmark_results res
                WHERE res.run_id = :run_id
            """
            )

            result = self.db.execute(query, {"run_id": str(run_id)})

            regressions = []
            for row in result.fetchall():
                metric_name, metric_category, current_value, baseline_value = row

                if baseline_value is None:
                    continue

                change_percent = ((current_value - baseline_value) / baseline_value) * 100
                change_absolute = current_value - baseline_value

                # Check if regression
                is_regression = change_percent < regression_threshold

                if is_regression:
                    # Determine severity
                    if change_percent < -20:
                        severity = "critical"
                    elif change_percent < -10:
                        severity = "major"
                    else:
                        severity = "minor"

                    regressions.append(
                        {
                            "metric_name": metric_name,
                            "metric_category": metric_category,
                            "baseline_value": float(baseline_value),
                            "current_value": float(current_value),
                            "change_percent": float(change_percent),
                            "change_absolute": float(change_absolute),
                            "regression_severity": severity,
                        }
                    )

            return regressions

        except Exception as e:
            self.logger.error("Failed to detect regressions", error=str(e))
            return []
