#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# SPEC-147: Celery Worker Entry Point
# Developer D - January 2025
#
# BILL-007: Celery Worker Architecture

"""
Celery worker entry point for billing system.

Usage:
    celery -A server.billing.worker worker --loglevel=info --queues=billing,stripe,notify
    celery -A server.billing.worker beat --loglevel=info
"""

from .celery_app import celery_app

if __name__ == "__main__":
    celery_app.start()
