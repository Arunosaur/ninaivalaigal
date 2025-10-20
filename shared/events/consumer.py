# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC

"""
Event Consumer for Redis Streams
SPEC-100: Event-Driven Architecture
"""

import asyncio
import logging
from typing import Callable, Dict, Optional

import redis.asyncio as redis

from .schema import Event
from .types import StreamTopic

logger = logging.getLogger(__name__)


class EventConsumer:
    """
    Consumes events from Redis Streams.

    Supports consumer groups for parallel processing and guarantees
    each event is processed at least once.
    """

    def __init__(
        self,
        redis_url: str = "redis://localhost:6399",
        consumer_group: str = "default",
        consumer_name: str = "consumer-1",
    ):
        """
        Initialize event consumer.

        Args:
            redis_url: Redis connection URL
            consumer_group: Consumer group name for this consumer
            consumer_name: Unique name for this consumer instance
        """
        self.redis_url = redis_url
        self.consumer_group = consumer_group
        self.consumer_name = consumer_name
        self._redis: Optional[redis.Redis] = None
        self._running = False
        self._handlers: Dict[str, Callable] = {}

    async def connect(self):
        """Establish Redis connection"""
        if not self._redis:
            self._redis = await redis.from_url(self.redis_url, encoding="utf-8", decode_responses=True)
            logger.info(f"Event consumer connected: group={self.consumer_group}, " f"name={self.consumer_name}")

    async def disconnect(self):
        """Close Redis connection"""
        if self._redis:
            await self._redis.close()
            self._redis = None
            logger.info("Event consumer disconnected")

    def register_handler(self, event_type: str, handler: Callable):
        """
        Register a handler function for a specific event type.

        Args:
            event_type: Event type to handle (e.g., "user.created")
            handler: Async function that takes Event as parameter

        Example:
            async def handle_user_created(event: Event):
                print(f"User created: {event.payload}")

            consumer.register_handler("user.created", handle_user_created)
        """
        self._handlers[event_type] = handler
        logger.info(f"Registered handler for event type: {event_type}")

    async def ensure_consumer_group(self, stream: str):
        """
        Create consumer group if it doesn't exist.

        Args:
            stream: Redis stream name
        """
        try:
            await self._redis.xgroup_create(stream, self.consumer_group, id="0", mkstream=True)  # Start from beginning
            logger.info(f"Created consumer group '{self.consumer_group}' for stream '{stream}'")
        except redis.ResponseError as e:
            if "BUSYGROUP" in str(e):
                # Group already exists
                pass
            else:
                raise

    async def consume(self, streams: list[StreamTopic], block_ms: int = 5000):
        """
        Start consuming events from specified streams.

        Args:
            streams: List of stream topics to consume from
            block_ms: How long to block waiting for new messages (milliseconds)

        Example:
            await consumer.consume([
                StreamTopic.USERS,
                StreamTopic.MEMORIES
            ])
        """
        if not self._redis:
            await self.connect()

        # Ensure consumer groups exist for all streams
        for stream in streams:
            await self.ensure_consumer_group(stream.value)

        # Build stream dict for XREADGROUP
        stream_dict = {stream.value: ">" for stream in streams}

        self._running = True
        logger.info(f"Starting event consumption from streams: {[s.value for s in streams]}")

        try:
            while self._running:
                # Read from streams using consumer group
                messages = await self._redis.xreadgroup(
                    self.consumer_group,
                    self.consumer_name,
                    stream_dict,
                    count=10,  # Process up to 10 messages at a time
                    block=block_ms,
                )

                if not messages:
                    continue

                # Process messages
                for stream_name, stream_messages in messages:
                    for message_id, message_data in stream_messages:
                        await self._process_message(stream_name, message_id, message_data)

        except asyncio.CancelledError:
            logger.info("Event consumer cancelled")
        except Exception as e:
            logger.error(f"Error in event consumer: {e}", exc_info=True)
        finally:
            self._running = False

    async def _process_message(self, stream: str, message_id: str, message_data: Dict):
        """
        Process a single message from the stream.

        Args:
            stream: Stream name
            message_id: Redis message ID
            message_data: Message data
        """
        try:
            # Parse event
            event = Event.from_dict(message_data)

            # Find and execute handler
            handler = self._handlers.get(event.event_type)

            if handler:
                await handler(event)
                logger.debug(f"Processed event: {event.event_type} (id: {message_id})")
            else:
                logger.warning(f"No handler for event type: {event.event_type}")

            # Acknowledge message
            await self._redis.xack(stream, self.consumer_group, message_id)

        except Exception as e:
            logger.error(f"Failed to process message {message_id} from {stream}: {e}", exc_info=True)
            # Message will remain in pending list and can be retried

    def stop(self):
        """Stop consuming events"""
        self._running = False
        logger.info("Stopping event consumer...")
