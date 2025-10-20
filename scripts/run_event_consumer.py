#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC

"""
Event Consumer Runner
SPEC-100: Event-Driven Architecture

Runs event consumer to process events from Redis Streams.
Can be run as a standalone service or in a container.
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

# Add shared directory to path
shared_dir = Path(__file__).parent.parent / "shared"
sys.path.insert(0, str(shared_dir))

from events import EventConsumer, StreamTopic  # noqa: E402
from events.handlers import handle_user_event  # noqa: E402

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

logger = logging.getLogger(__name__)


async def main():
    """Run event consumer"""
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6399")
    consumer_group = os.getenv("CONSUMER_GROUP", "analytics-service")
    consumer_name = os.getenv("CONSUMER_NAME", "worker-1")

    logger.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    logger.info("🎧 Starting Event Consumer")
    logger.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    logger.info(f"Redis URL: {redis_url}")
    logger.info(f"Consumer Group: {consumer_group}")
    logger.info(f"Consumer Name: {consumer_name}")

    # Create consumer
    consumer = EventConsumer(redis_url=redis_url, consumer_group=consumer_group, consumer_name=consumer_name)

    # Register event handlers
    consumer.register_handler("user.created", handle_user_event)
    consumer.register_handler("user.login", handle_user_event)
    consumer.register_handler("user.updated", handle_user_event)
    consumer.register_handler("user.deleted", handle_user_event)

    logger.info("✅ Event handlers registered")
    logger.info("")
    logger.info("Listening for events on streams:")
    logger.info(f"  - {StreamTopic.USERS.value}")
    logger.info(f"  - {StreamTopic.TEAMS.value}")
    logger.info("")
    logger.info("Press Ctrl+C to stop...")
    logger.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    try:
        # Start consuming events
        await consumer.consume(
            [
                StreamTopic.USERS,
                StreamTopic.TEAMS,
            ]
        )
    except KeyboardInterrupt:
        logger.info("\n🛑 Shutting down...")
        consumer.stop()
    except Exception as e:
        logger.error(f"Consumer error: {e}", exc_info=True)
    finally:
        await consumer.disconnect()
        logger.info("✅ Consumer stopped")


if __name__ == "__main__":
    asyncio.run(main())
