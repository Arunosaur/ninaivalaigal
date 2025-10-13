#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""Cost exporter stub for SPEC-120 governance."""


def get_cluster_cost(events):
    """Get current cluster cost metrics."""
    total = sum(e.get("usd", 0.0) for e in events)
    by_service = {}
    for e in events:
        by_service[e["service"]] = by_service.get(e["service"], 0) + e.get("usd", 0)
    print({"total_usd": total, "by_service": by_service})


if __name__ == "__main__":
    sample = [{"service": "api", "usd": 12.3}, {"service": "ui", "usd": 5.7}]
    get_cluster_cost(sample)
