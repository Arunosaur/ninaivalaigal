#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""Tests for benchmark storage service (US#409, SPEC-069)."""

from uuid import UUID

import pytest

from server.performance.benchmark_storage import BenchmarkStorage


@pytest.fixture
def mock_db_session(mocker):
    """Mock database session."""
    return mocker.MagicMock()


@pytest.fixture
def benchmark_storage(mock_db_session):
    """Create BenchmarkStorage instance."""
    return BenchmarkStorage(mock_db_session)


def test_create_benchmark_run(benchmark_storage, mock_db_session):
    """Test creating a benchmark run."""
    # Mock database execute
    mock_db_session.execute.return_value.fetchone.return_value = None

    run_id = benchmark_storage.create_benchmark_run(
        run_type="automated",
        environment="development",
    )

    assert isinstance(run_id, UUID)
    assert mock_db_session.execute.called
    assert mock_db_session.commit.called


def test_record_benchmark_result(benchmark_storage, mock_db_session):
    """Test recording a benchmark result."""
    run_id = UUID("12345678-1234-5678-1234-567812345678")

    # Mock database execute
    mock_db_session.execute.return_value.fetchone.return_value = None

    result_id = benchmark_storage.record_benchmark_result(
        run_id=run_id,
        metric_name="api_latency_p95_ms",
        metric_category="api",
        metric_value=85.5,
        metric_unit="ms",
        target_value=100.0,
    )

    assert isinstance(result_id, UUID)
    assert mock_db_session.execute.called
    assert mock_db_session.commit.called


def test_complete_benchmark_run(benchmark_storage, mock_db_session):
    """Test completing a benchmark run."""
    run_id = UUID("12345678-1234-5678-1234-567812345678")

    benchmark_storage.complete_benchmark_run(run_id, "completed")

    assert mock_db_session.execute.called
    assert mock_db_session.commit.called


def test_get_benchmark_history(benchmark_storage, mock_db_session):
    """Test getting benchmark history."""
    # Mock database execute to return empty result
    mock_result = mock_db_session.execute.return_value
    mock_result.fetchall.return_value = []

    history = benchmark_storage.get_benchmark_history(days=30, limit=100)

    assert isinstance(history, list)
    assert mock_db_session.execute.called


def test_detect_regressions(benchmark_storage, mock_db_session):
    """Test regression detection."""
    run_id = UUID("12345678-1234-5678-1234-567812345678")

    # Mock database execute to return no regressions
    mock_result = mock_db_session.execute.return_value
    mock_result.fetchall.return_value = []

    regressions = benchmark_storage.detect_regressions(run_id)

    assert isinstance(regressions, list)
    assert mock_db_session.execute.called


def test_compare_with_baseline_no_baseline(benchmark_storage, mock_db_session):
    """Test comparison with no baseline found."""
    run_id = UUID("12345678-1234-5678-1234-567812345678")

    # Mock database execute to return None (no baseline)
    mock_result = mock_db_session.execute.return_value
    mock_result.fetchone.return_value = None

    comparisons = benchmark_storage.compare_with_baseline(run_id)

    assert isinstance(comparisons, list)
    assert len(comparisons) == 0  # No baseline found
