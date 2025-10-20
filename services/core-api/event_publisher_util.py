# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC

"""
Event Publishing Utility for Core API
SPEC-100: Event-Driven Architecture
"""

from typing import Any, Dict, Optional
from uuid import UUID

import structlog
from fastapi import Request

logger = structlog.get_logger(__name__)


async def publish_event(
    request: Request,
    event_type: str,
    payload: Dict[str, Any],
    user_id: Optional[UUID] = None,
    organization_id: Optional[UUID] = None,
    team_id: Optional[UUID] = None,
):
    """
    Publish an event to the event bus.

    Args:
        request: FastAPI request object (to get event_publisher)
        event_type: Event type (e.g., "user.created")
        payload: Event payload
        user_id: Optional user ID for metadata
        organization_id: Optional organization ID
        team_id: Optional team ID

    Returns:
        Event ID if successful, None if failed
    """
    try:
        # Get event publisher from app state
        event_publisher = getattr(request.app.state, "event_publisher", None)

        if not event_publisher:
            logger.warning("Event publisher not available, skipping event")
            return None

        # Import here to avoid circular imports
        from events import EventMetadata, EventType

        # Create metadata
        metadata = EventMetadata(user_id=user_id, organization_id=organization_id, team_id=team_id)

        # Publish event
        event_id = await event_publisher.publish(
            event_type=EventType(event_type), source_service="core-api", payload=payload, metadata=metadata
        )

        logger.info(f"Published event: {event_type}", event_id=event_id)
        return event_id

    except Exception as e:
        logger.error(f"Failed to publish event {event_type}: {e}", exc_info=True)
        return None
