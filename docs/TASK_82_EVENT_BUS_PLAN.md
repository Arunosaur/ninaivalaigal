# Task #82: Deploy Event Bus (Redis Streams)

**Epic:** SPEC-100
**Assigned:** Developer C
**Started:** October 19, 2025
**Estimated:** 2-3 days

---

## 🎯 Objective

Implement async messaging infrastructure using **Redis Streams** to enable event-driven architecture and loose coupling between microservices.

---

## 💡 Technology Decision: Redis Streams

**Why Redis Streams over NATS:**
- ✅ Already have Redis infrastructure (port 6399)
- ✅ Simpler integration for our scale
- ✅ Built-in persistence and consumer groups
- ✅ No new infrastructure to manage
- ✅ Familiar tooling for team

---

## 📋 Implementation Plan

### Phase 1: Infrastructure Setup (Today)
1. ✅ Document event bus architecture
2. 🔄 Design event schema format
3. 🔄 Create event types/topics
4. 🔄 Set up Redis Streams connection library

### Phase 2: Publisher Implementation
1. Create event publisher utility
2. Integrate into Core API service
3. Integrate into Business Service
4. Add event publishing to key operations

### Phase 3: Consumer Implementation
1. Create event consumer framework
2. Implement consumer groups
3. Add event handlers
4. Error handling and retries

### Phase 4: Testing & Documentation
1. Integration tests
2. Event replay testing
3. Documentation
4. Update Taiga

---

## 🗂️ Event Schema Design

### Standard Event Format
```json
{
  "event_id": "uuid-v4",
  "event_type": "user.created",
  "timestamp": "2025-10-19T22:00:00Z",
  "version": "1.0",
  "source_service": "core-api",
  "payload": {
    // Event-specific data
  },
  "metadata": {
    "user_id": "uuid",
    "organization_id": "uuid",
    "correlation_id": "uuid"
  }
}
```

---

## 📢 Event Types (Initial Set)

### Core API Events
- `user.created`
- `user.updated`
- `user.deleted`
- `team.created`
- `team.member_added`
- `organization.created`

### Memory Service Events
- `memory.created`
- `memory.updated`
- `memory.deleted`
- `memory.recalled`

### Business Service Events
- `subscription.created`
- `subscription.updated`
- `usage.recorded`
- `invoice.generated`

---

## 🔧 Technical Implementation

### Redis Streams Topics
```
streams:
  - ninaivalaigal:events:users
  - ninaivalaigal:events:teams
  - ninaivalaigal:events:memories
  - ninaivalaigal:events:subscriptions
  - ninaivalaigal:events:system
```

### Consumer Groups
```
consumers:
  - analytics-consumer (processes all events for analytics)
  - notification-consumer (sends notifications)
  - audit-consumer (audit logging)
```

---

## 🏗️ File Structure

```
shared/
├── events/
│   ├── __init__.py
│   ├── publisher.py       # Event publishing utility
│   ├── consumer.py        # Event consumer framework
│   ├── types.py           # Event type definitions
│   ├── schema.py          # Event schema validation
│   └── handlers/          # Event handlers
│       ├── __init__.py
│       ├── user_events.py
│       ├── memory_events.py
│       └── business_events.py
```

---

## ✅ Acceptance Criteria

- [ ] Redis Streams connection established
- [ ] Event schema defined and validated
- [ ] Publisher utility created
- [ ] 2+ services publishing events
- [ ] Consumer framework implemented
- [ ] 1+ consumer group processing events
- [ ] Integration tests passing
- [ ] Event replay capability verified
- [ ] Documentation complete
- [ ] Taiga updated

---

## 🚀 Next Steps (Immediate)

Starting implementation now...
