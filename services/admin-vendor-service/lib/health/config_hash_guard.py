#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""config hash guard module."""

import hashlib
import json
import os

from fastapi import APIRouter

router = APIRouter()

SECURITY_CONFIG = {
    "JWT_SECRET": os.getenv("JWT_SECRET", "dev-secret"),
    "UPLOAD_LIMIT": os.getenv("UPLOAD_LIMIT", "10MB"),
    "REDIS_URL": os.getenv("REDIS_URL", "memory://"),
}


def compute_hash():
    """Function implementation."""
    return hashlib.sha256(json.dumps(SECURITY_CONFIG, sort_keys=True).encode()).hexdigest()


@router.get("/healthz/config")
async def health_config():
    """Health check endpoint returning security configuration hash."""
    return {"security_config_hash": compute_hash()}
