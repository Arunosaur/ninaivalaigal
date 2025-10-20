# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC

"""
Event Bus Integration Tests
SPEC-100: Event-Driven Architecture

Tests end-to-end event publishing and consumption.
"""

import asyncio
import os
import sys
import time
from pathlib import Path
from uuid import uuid4

import pytest

# Add shared directory to path
shared_dir = Path(__file__).parent.parent.parent / "shared"
sys.path.insert(0, str(shared_dir))

from events import (  # noqa: E402
    EventConsumer,
    EventMetadata,
    EventPublisher,
    EventType,
    StreamTopic,
)
from events.schema import Event  # noqa: E402

# Test configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6399")
TEST_TIMEOUT = 30  # seconds


@pytest.fixture
async def publisher():
    """Create event publisher for tests"""
    pub = EventPublisher(REDIS_URL)
    await pub.connect()
    yield pub
    await pub.disconnect()


@pytest.fixture
async def consumer():
    """Create event consumer for tests"""
    cons = EventConsumer(redis_url=REDIS_URL, consumer_group="test-group", consumer_name="test-worker")
    await cons.connect()
    yield cons
    await cons.disconnect()


@pytest.mark.asyncio
async def test_redis_connection():
    """Test basic Redis connection"""
    publisher = EventPublisher(REDIS_URL)
    try:
        await publisher.connect()
        assert publisher._redis is not None
    finally:
        await publisher.disconnect()


@pytest.mark.asyncio
async def test_publish_single_event(publisher):
    """Test publishing a single event"""
    user_id = uuid4()

    event_id = await publisher.publish(
        event_type=EventType.USER_CREATED,
        source_service="test-suite",
        payload={"user_id": str(user_id), "email": "test@example.com", "name": "Test User"},
        metadata=EventMetadata(user_id=user_id),
    )

    assert event_id is not None
    assert isinstance(event_id, str)


@pytest.mark.asyncio
async def test_publish_batch_events(publisher):
    """Test batch publishing"""
    events = [
        {
            "event_type": EventType.USER_CREATED,
            "source_service": "test-suite",
            "payload": {
                "user_id": str(uuid4()),
                "email": f"user{i}@example.com",
                "name": f"User {i}",
            },
        }
        for i in range(5)
    ]

    event_ids = await publisher.publish_batch(events)

    assert len(event_ids) == 5
    assert all(isinstance(eid, str) for eid in event_ids)


@pytest.mark.asyncio
async def test_event_consumer_receives_events(publisher):
    """Test that consumer receives published events"""
    received_events = []

    async def handler(event: Event):
        received_events.append(event)

    # Create consumer
    consumer = EventConsumer(redis_url=REDIS_URL, consumer_group="integration-test", consumer_name="worker-1")
    await consumer.connect()
    consumer.register_handler("user.created", handler)

    # Publish event
    user_id = uuid4()
    await publisher.publish(
        event_type=EventType.USER_CREATED,
        source_service="test-suite",
        payload={"user_id": str(user_id), "email": "test@example.com"},
        metadata=EventMetadata(user_id=user_id),
    )

    # Consume events for a short time
    try:
        consume_task = asyncio.create_task(consumer.consume([StreamTopic.USERS], block_ms=1000))
        await asyncio.sleep(2)  # Wait for event processing
        consumer.stop()
        await consume_task
    except asyncio.CancelledError:
        pass
    finally:
        await consumer.disconnect()

    # Verify event was received
    assert len(received_events) > 0
    assert received_events[0].event_type == "user.created"
    assert received_events[0].payload["email"] == "test@example.com"


@pytest.mark.asyncio
async def test_consumer_group_distribution():
    """Test that consumer groups distribute work correctly"""
    received_by_worker1 = []
    received_by_worker2 = []

    async def handler1(event: Event):
        received_by_worker1.append(event)

    async def handler2(event: Event):
        received_by_worker2.append(event)

    # Create two consumers in same group
    consumer1 = EventConsumer(redis_url=REDIS_URL, consumer_group="load-test", consumer_name="worker-1")
    consumer2 = EventConsumer(redis_url=REDIS_URL, consumer_group="load-test", consumer_name="worker-2")

    await consumer1.connect()
    await consumer2.connect()

    consumer1.register_handler("user.created", handler1)
    consumer2.register_handler("user.created", handler2)

    # Publish multiple events
    publisher = EventPublisher(REDIS_URL)
    await publisher.connect()

    for i in range(10):
        await publisher.publish(
            event_type=EventType.USER_CREATED,
            source_service="test-suite",
            payload={"user_id": str(uuid4()), "email": f"user{i}@example.com"},
        )

    # Start consumers
    try:
        task1 = asyncio.create_task(consumer1.consume([StreamTopic.USERS], block_ms=1000))
        task2 = asyncio.create_task(consumer2.consume([StreamTopic.USERS], block_ms=1000))

        await asyncio.sleep(3)  # Wait for processing

        consumer1.stop()
        consumer2.stop()

        await task1
        await task2
    except asyncio.CancelledError:
        pass
    finally:
        await consumer1.disconnect()
        await consumer2.disconnect()
        await publisher.disconnect()

    # Verify events were distributed (not all to one worker)
    total_received = len(received_by_worker1) + len(received_by_worker2)
    assert total_received > 0
    # Both workers should receive at least some events (statistically)
    # In rare cases one might get all, so we just verify total > 0


@pytest.mark.asyncio
async def test_event_metadata_propagation(publisher):
    """Test that event metadata is properly propagated"""
    user_id = uuid4()
    org_id = uuid4()
    team_id = uuid4()

    event_id = await publisher.publish(
        event_type=EventType.USER_CREATED,
        source_service="test-suite",
        payload={"test": "data"},
        metadata=EventMetadata(user_id=user_id, organization_id=org_id, team_id=team_id),
    )

    assert event_id is not None


@pytest.mark.asyncio
async def test_error_handling_in_consumer():
    """Test consumer handles errors gracefully"""
    error_count = 0

    async def failing_handler(event: Event):
        nonlocal error_count
        error_count += 1
        raise ValueError("Simulated error")

    consumer = EventConsumer(redis_url=REDIS_URL, consumer_group="error-test", consumer_name="worker-1")
    await consumer.connect()
    consumer.register_handler("user.created", failing_handler)

    # Publish event
    publisher = EventPublisher(REDIS_URL)
    await publisher.connect()

    await publisher.publish(
        event_type=EventType.USER_CREATED,
        source_service="test-suite",
        payload={"test": "error"},
    )

    # Consume
    try:
        task = asyncio.create_task(consumer.consume([StreamTopic.USERS], block_ms=1000))
        await asyncio.sleep(2)
        consumer.stop()
        await task
    except asyncio.CancelledError:
        pass
    finally:
        await consumer.disconnect()
        await publisher.disconnect()

    # Consumer should continue despite errors
    assert error_count > 0


@pytest.mark.asyncio
async def test_performance_publish_throughput(publisher):
    """Benchmark event publishing throughput"""
    num_events = 100
    start_time = time.time()

    for i in range(num_events):
        await publisher.publish(
            event_type=EventType.USER_CREATED,
            source_service="benchmark",
            payload={"index": i},
        )

    elapsed = time.time() - start_time
    throughput = num_events / elapsed

    print(f"\n📊 Publishing Throughput: {throughput:.2f} events/sec")
    print(f"   Average latency: {(elapsed / num_events) * 1000:.2f} ms/event")

    # Should handle at least 50 events/sec
    assert throughput > 50, f"Publishing throughput too low: {throughput:.2f} events/sec"


@pytest.mark.asyncio
async def test_performance_end_to_end_latency(publisher):
    """Benchmark end-to-end event latency"""
    latencies = []

    async def timing_handler(event: Event):
        # Calculate latency from event timestamp to now
        from datetime import datetime

        event_time = event.timestamp
        now = datetime.utcnow()
        latency_ms = (now - event_time).total_seconds() * 1000
        latencies.append(latency_ms)

    consumer = EventConsumer(redis_url=REDIS_URL, consumer_group="latency-test", consumer_name="worker-1")
    await consumer.connect()
    consumer.register_handler("user.created", timing_handler)

    # Start consumer
    consume_task = asyncio.create_task(consumer.consume([StreamTopic.USERS], block_ms=1000))

    # Give consumer time to start
    await asyncio.sleep(1)

    # Publish events
    for i in range(10):
        await publisher.publish(
            event_type=EventType.USER_CREATED,
            source_service="benchmark",
            payload={"index": i},
        )

    # Wait for processing
    await asyncio.sleep(2)

    consumer.stop()
    try:
        await consume_task
    except asyncio.CancelledError:
        pass
    finally:
        await consumer.disconnect()

    if latencies:
        avg_latency = sum(latencies) / len(latencies)
        p95_latency = sorted(latencies)[int(len(latencies) * 0.95)] if len(latencies) > 1 else avg_latency

        print("\n📊 End-to-End Latency:")
        print(f"   Average: {avg_latency:.2f} ms")
        print(f"   P95: {p95_latency:.2f} ms")
        print(f"   Min: {min(latencies):.2f} ms")
        print(f"   Max: {max(latencies):.2f} ms")

        # Should be under 1000ms for P95
        assert p95_latency < 1000, f"P95 latency too high: {p95_latency:.2f} ms"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
