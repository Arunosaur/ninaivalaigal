# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC

"""
Event Handlers
SPEC-100: Event-Driven Architecture
"""

from .analytics_handler import handle_user_event

__all__ = ["handle_user_event"]
