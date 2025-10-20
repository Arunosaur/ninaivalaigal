# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC

"""
Event Bus Module
SPEC-100: Event-Driven Architecture

This module provides event publishing and consumption capabilities
using Redis Streams for async, event-driven communication between
microservices.
"""

from .publisher import EventPublisher, get_event_publisher
from .schema import Event, EventMetadata
from .types import EventType, StreamTopic

__all__ = [
    "Event",
    "EventMetadata",
    "EventPublisher",
    "EventType",
    "StreamTopic",
    "get_event_publisher",
]
