# Event Bus Module

**Task #82:** Deploy Event Bus (Redis Streams)
**SPEC-100:** Event-Driven Architecture
**Status:** Phase 1 Complete - Infrastructure Setup

---

## Overview

This module provides event-driven communication between microservices using **Redis Streams**. It enables loose coupling, async processing, and event replay capabilities.

---

## Quick Start

### Publishing Events

```python
from shared.events import EventPublisher, EventType, EventMetadata

# Initialize publisher
publisher = EventPublisher(redis_url="redis://localhost:6399")
await publisher.connect()

# Publish an event
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
```

### Consuming Events

```python
from shared.events import EventConsumer, StreamTopic
from shared.events.schema import Event

# Define event handler
async def handle_user_created(event: Event):
    print(f"New user: {event.payload['email']}")
    # Process the event...

# Initialize consumer
consumer = EventConsumer(
    redis_url="redis://localhost:6399",
    consumer_group="analytics-service",
    consumer_name="worker-1"
)

# Register handlers
consumer.register_handler("user.created", handle_user_created)

# Start consuming
await consumer.consume([StreamTopic.USERS, StreamTopic.TEAMS])
```

---

## Event Types

All events follow a standard schema:

```json
{
  "event_id": "uuid-v4",
  "event_type": "user.created",
  "timestamp": "2025-10-19T22:00:00Z",
  "version": "1.0",
  "source_service": "core-api",
  "payload": {
    "user_id": "...",
    "email": "...",
    "name": "..."
  },
  "metadata": {
    "user_id": "uuid",
    "organization_id": "uuid",
    "correlation_id": "uuid"
  }
}
```

### Available Event Types

**Users:**
- `user.created`
- `user.updated`
- `user.deleted`

**Teams:**
- `team.created`
- `team.member_added`
- `team.member_removed`

**Memories:**
- `memory.created`
- `memory.recalled`
- `memory.feedback`

**Business:**
- `subscription.created`
- `usage.recorded`
- `payment.received`

See `types.py` for complete list.

---

## Redis Streams Topics

Events are routed to topics automatically:

- `ninaivalaigal:events:users` - All user events
- `ninaivalaigal:events:teams` - All team events
- `ninaivalaigal:events:memories` - All memory events
- `ninaivalaigal:events:subscriptions` - All business events
- `ninaivalaigal:events:system` - System events

---

## Consumer Groups

Multiple consumers can process events in parallel using consumer groups:

```python
# Analytics service
consumer = EventConsumer(consumer_group="analytics-service")

# Notification service
consumer = EventConsumer(consumer_group="notification-service")

# Audit service
consumer = EventConsumer(consumer_group="audit-service")
```

Each consumer group receives ALL events, but within a group, events are distributed across consumers.

---

## Architecture

```
┌─────────────┐      Publish      ┌──────────────┐
│ Core API    │ ────────────────> │ Redis        │
│             │                    │ Streams      │
└─────────────┘                    │              │
                                   │ - users      │
┌─────────────┐      Publish      │ - teams      │
│ Business    │ ────────────────> │ - memories   │
│ Service     │                    │ - subs       │
└─────────────┘                    └──────┬───────┘
                                          │
                                   Consume│
                                          │
                            ┌─────────────┴──────────────┐
                            │                            │
                       ┌────▼─────┐              ┌──────▼──────┐
                       │Analytics │              │Notification │
                       │Consumer  │              │Consumer     │
                       └──────────┘              └─────────────┘
```

---

## Files

- `types.py` - Event type enums and topic routing
- `schema.py` - Pydantic models for event validation
- `publisher.py` - Event publishing utility
- `consumer.py` - Event consumption framework
- `handlers/` - Event handler implementations

---

## Next Steps

**Phase 2:** Integrate publishers into services
- [ ] Add event publishing to Core API
- [ ] Add event publishing to Business Service
- [ ] Add event publishing to Memory Service

**Phase 3:** Implement consumers
- [ ] Analytics consumer
- [ ] Notification consumer
- [ ] Audit logging consumer

**Phase 4:** Testing
- [ ] Integration tests
- [ ] Event replay testing
- [ ] Performance benchmarking

---

## Configuration

Set Redis URL via environment variable:

```bash
export REDIS_URL="redis://localhost:6399"
```

Or pass directly:

```python
publisher = EventPublisher(redis_url="redis://localhost:6399")
```

---

## Monitoring

Redis Streams provide built-in monitoring:

```bash
# View stream info
redis-cli XINFO STREAM ninaivalaigal:events:users

# View consumer group info
redis-cli XINFO GROUPS ninaivalaigal:events:users

# View pending messages
redis-cli XPENDING ninaivalaigal:events:users analytics-service
```

---

**Status:** Infrastructure complete ✅
**Next:** Integrate into services (Phase 2)
