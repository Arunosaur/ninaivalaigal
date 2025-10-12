#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""RBAC context provider for FastAPI integration."""

from __future__ import annotations

from collections.abc import Callable

from fastapi import HTTPException, Request, status


def install_subject_ctx_provider(app, provider: Callable):
    """Install RBAC subject context provider into FastAPI app."""
    app.state.subject_ctx_provider = provider


def get_subject_ctx_dep(app):
    """Get dependency function for extracting subject context from requests."""

    def _dep(request: Request):
        prov = getattr(app.state, "subject_ctx_provider", None)
        if prov is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="subject_ctx_provider not installed",
            )
        return prov(request)

    return _dep
