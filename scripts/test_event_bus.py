#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC

"""
Event Bus Test Script
SPEC-100: Event-Driven Architecture

Tests event publishing and consumption end-to-end.
"""

import asyncio
import logging
import os
import sys
from pathlib import Path
from uuid import uuid4

# Add shared directory to path
shared_dir = Path(__file__).parent.parent / "shared"
sys.path.insert(0, str(shared_dir))

from events import EventMetadata, EventPublisher, EventType  # noqa: E402

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_event_publishing():
    """Test event publishing"""

    logger.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    logger.info("🧪 Testing Event Bus")
    logger.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    redis_url = os.getenv("REDIS_URL", "redis://localhost:6399")
    logger.info(f"Redis URL: {redis_url}")

    # Create publisher
    publisher = EventPublisher(redis_url)
    await publisher.connect()
    logger.info("✅ Publisher connected")

    # Test 1: Publish user.created event
    logger.info("\n📤 Test 1: Publishing user.created event...")
    user_id = uuid4()

    event_id = await publisher.publish(
        event_type=EventType.USER_CREATED,
        source_service="test-script",
        payload={
            "user_id": str(user_id),
            "email": "test@example.com",
            "name": "Test User",
            "account_type": "individual",
        },
        metadata=EventMetadata(user_id=user_id),
    )

    logger.info(f"✅ Published event: {event_id}")

    # Test 2: Publish user.login event
    logger.info("\n📤 Test 2: Publishing user.login event...")

    event_id = await publisher.publish(
        event_type=EventType.USER_LOGIN,
        source_service="test-script",
        payload={
            "user_id": str(user_id),
            "email": "test@example.com",
            "account_type": "individual",
        },
        metadata=EventMetadata(user_id=user_id),
    )

    logger.info(f"✅ Published event: {event_id}")

    # Test 3: Batch publish
    logger.info("\n📤 Test 3: Publishing batch events...")

    events = [
        {
            "event_type": EventType.USER_CREATED,
            "source_service": "test-script",
            "payload": {
                "user_id": str(uuid4()),
                "email": f"user{i}@example.com",
                "name": f"User {i}",
            },
        }
        for i in range(3)
    ]

    event_ids = await publisher.publish_batch(events)
    logger.info(f"✅ Published {len(event_ids)} events")

    # Disconnect
    await publisher.disconnect()

    logger.info("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    logger.info("✅ Event Bus Test Complete!")
    logger.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    logger.info("\nNext steps:")
    logger.info("1. Run event consumer: python scripts/run_event_consumer.py")
    logger.info("2. Check Redis streams: redis-cli XINFO STREAM ninaivalaigal:events:users")
    logger.info("3. View events: redis-cli XRANGE ninaivalaigal:events:users - +")


if __name__ == "__main__":
    asyncio.run(test_event_publishing())
