#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""Gunicorn Configuration for Ninaivalaigal API
SPEC-107: Unified Runtime Parity & Deployment Standard
"""

import multiprocessing
import os

# Server socket
bind = "0.0.0.0:8000"

# Worker processes
worker_class = "uvicorn.workers.UvicornWorker"
workers = multiprocessing.cpu_count() * 2 + 1
timeout = 120
loglevel = os.getenv("LOG_LEVEL", "info")

# Reload on code changes (development only)
reload = os.getenv("ENV") == "dev"
