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

# Worker count by environment (TRUE PARITY - same process manager, different worker counts)
env = os.getenv("ENV", "prod").lower()
if env == "dev":
    workers = 1  # Single worker for development with hot reload
elif env == "test":
    workers = 1  # Single worker for test (mirrors prod but simpler for stability)
else:  # prod
    workers = multiprocessing.cpu_count() * 2 + 1  # Production: CPU-based scaling

timeout = 120
loglevel = os.getenv("LOG_LEVEL", "info")

# Reload on code changes (development only)
reload = env == "dev"
