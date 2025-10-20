#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC

"""
Event Bus Validation Script
SPEC-100: Event-Driven Architecture

Validates that the event bus is working correctly.
"""

import asyncio
import sys
import time
from pathlib import Path
from uuid import uuid4

# Add shared directory to path
shared_dir = Path(__file__).parent.parent / "shared"
sys.path.insert(0, str(shared_dir))

from events import EventMetadata, EventPublisher, EventType  # noqa: E402


async def validate_event_bus():
    """Validate event bus functionality"""

    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("🧪 Validating Event Bus")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    try:
        # Test 1: Connection
        print("\n✅ Test 1: Redis Connection...")
        publisher = EventPublisher("redis://localhost:6399")
        await publisher.connect()
        print("   ✅ Connected to Redis")

        # Test 2: Single Event Publishing
        print("\n✅ Test 2: Single Event Publishing...")
        user_id = uuid4()
        event_id = await publisher.publish(
            event_type=EventType.USER_CREATED,
            source_service="validation",
            payload={
                "user_id": str(user_id),
                "email": "validate@example.com",
                "name": "Validation User",
            },
            metadata=EventMetadata(user_id=user_id),
        )
        print(f"   ✅ Published event: {event_id}")

        # Test 3: Batch Publishing
        print("\n✅ Test 3: Batch Event Publishing...")
        events = [
            {
                "event_type": EventType.USER_CREATED,
                "source_service": "validation",
                "payload": {
                    "user_id": str(uuid4()),
                    "email": f"batch{i}@example.com",
                },
            }
            for i in range(5)
        ]
        event_ids = await publisher.publish_batch(events)
        print(f"   ✅ Published {len(event_ids)} events")

        # Test 4: Performance
        print("\n✅ Test 4: Performance Benchmark...")
        num_events = 50
        start_time = time.time()

        for i in range(num_events):
            await publisher.publish(
                event_type=EventType.USER_LOGIN,
                source_service="validation",
                payload={"index": i},
            )

        elapsed = time.time() - start_time
        throughput = num_events / elapsed
        avg_latency = (elapsed / num_events) * 1000

        print(f"   ✅ Throughput: {throughput:.2f} events/sec")
        print(f"   ✅ Average latency: {avg_latency:.2f} ms/event")

        # Test 5: Different Event Types
        print("\n✅ Test 5: Multiple Event Types...")
        test_events = [
            (EventType.USER_CREATED, "user.created"),
            (EventType.USER_LOGIN, "user.login"),
            (EventType.TEAM_CREATED, "team.created"),
            (EventType.MEMORY_CREATED, "memory.created"),
        ]

        for event_type, name in test_events:
            event_id = await publisher.publish(
                event_type=event_type, source_service="validation", payload={"test": name}
            )
            print(f"   ✅ {name}: {event_id}")

        # Cleanup
        await publisher.disconnect()

        print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print("✅ All Validation Tests Passed!")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print("\n📊 Performance Summary:")
        print(f"   • Throughput: {throughput:.2f} events/sec")
        print(f"   • Average Latency: {avg_latency:.2f} ms")
        print(f"   • Total Events Published: {num_events + len(event_ids) + len(test_events) + 1}")
        print("\n✅ Event Bus is fully operational!")

        return 0

    except Exception as e:
        print(f"\n❌ Validation Failed: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(validate_event_bus())
    sys.exit(exit_code)
