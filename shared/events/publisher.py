# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC

"""
Event Publisher for Redis Streams
SPEC-100: Event-Driven Architecture
"""

import logging
from typing import Any, Dict, Optional

import redis.asyncio as redis

from .schema import Event, EventMetadata
from .types import EVENT_TO_TOPIC, EventType

logger = logging.getLogger(__name__)


class EventPublisher:
    """
    Publishes events to Redis Streams.

    This provides a simple interface for any service to publish events
    to the event bus without worrying about the underlying implementation.
    """

    def __init__(self, redis_url: str = "redis://localhost:6399"):
        """
        Initialize event publisher.

        Args:
            redis_url: Redis connection URL
        """
        self.redis_url = redis_url
        self._redis: Optional[redis.Redis] = None

    async def connect(self):
        """Establish Redis connection"""
        if not self._redis:
            self._redis = await redis.from_url(self.redis_url, encoding="utf-8", decode_responses=True)
            logger.info(f"Event publisher connected to Redis: {self.redis_url}")

    async def disconnect(self):
        """Close Redis connection"""
        if self._redis:
            await self._redis.close()
            self._redis = None
            logger.info("Event publisher disconnected")

    async def publish(
        self,
        event_type: EventType,
        source_service: str,
        payload: Dict[str, Any],
        metadata: Optional[EventMetadata] = None,
    ) -> str:
        """
        Publish an event to the event bus.

        Args:
            event_type: Type of event (from EventType enum)
            source_service: Name of service publishing the event
            payload: Event-specific data
            metadata: Optional event metadata (user_id, org_id, etc.)

        Returns:
            Event ID (UUID string)

        Example:
            publisher = EventPublisher()
            await publisher.connect()

            event_id = await publisher.publish(
                event_type=EventType.USER_CREATED,
                source_service="core-api",
                payload={
                    "user_id": str(user.id),
                    "email": user.email,
                    "name": user.name
                },
                metadata=EventMetadata(
                    user_id=user.id,
                    organization_id=user.organization_id
                )
            )
        """
        if not self._redis:
            await self.connect()

        # Create event
        event = Event(
            event_type=event_type.value,
            source_service=source_service,
            payload=payload,
            metadata=metadata or EventMetadata(),
        )

        # Get topic for this event type
        topic = EVENT_TO_TOPIC.get(event_type)
        if not topic:
            logger.warning(f"No topic mapping for event type: {event_type}")
            topic = "ninaivalaigal:events:system"

        # Publish to Redis Stream
        event_dict = event.to_dict()

        try:
            # XADD to Redis Stream
            message_id = await self._redis.xadd(
                topic.value, event_dict, maxlen=10000  # Keep last 10k events per stream
            )

            logger.info(
                f"Published event: {event_type.value} "
                f"to {topic.value} "
                f"(id: {message_id}, event_id: {event.event_id})"
            )

            return str(event.event_id)

        except Exception as e:
            logger.error(f"Failed to publish event: {e}", exc_info=True)
            raise

    async def publish_batch(self, events: list[Dict[str, Any]]) -> list[str]:
        """
        Publish multiple events in a batch.

        Args:
            events: List of event dictionaries with keys:
                - event_type: EventType
                - source_service: str
                - payload: dict
                - metadata: Optional[EventMetadata]

        Returns:
            List of event IDs
        """
        event_ids = []

        for event_data in events:
            event_id = await self.publish(
                event_type=event_data["event_type"],
                source_service=event_data["source_service"],
                payload=event_data["payload"],
                metadata=event_data.get("metadata"),
            )
            event_ids.append(event_id)

        return event_ids


# Singleton instance for easy import
_publisher_instance: Optional[EventPublisher] = None


async def get_event_publisher(redis_url: str = "redis://localhost:6399") -> EventPublisher:
    """
    Get the singleton event publisher instance.

    Args:
        redis_url: Redis connection URL

    Returns:
        EventPublisher instance
    """
    global _publisher_instance

    if _publisher_instance is None:
        _publisher_instance = EventPublisher(redis_url)
        await _publisher_instance.connect()

    return _publisher_instance
