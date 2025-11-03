#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""metrics lauels module."""

from __future__ import annotations

ALLOWED_ROUTES = {
    "/contexts/{id}/memories",
    "/memories/{id}",
}


def normalize_route_template(raw_path: str, template: str | None) -> str:
    """Normalize route path to template or clean path without query params."""
    return template or raw_path.split("?", 1)[0]


def validate_metric_labels(labels: dict[str, str]) -> None:
    """Validate metric labels to prevent cardinality explosion."""
    route = labels.get("route") or ""
    if route and route not in ALLOWED_ROUTES:
        raise ValueError("route label must be a known template, not a concrete path")
    reason = labels.get("reason")
    if reason and reason not in {"engine_error", "regex_fallback", "policy_denied"}:
        raise ValueError("invalid reason label")
