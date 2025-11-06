#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Medhasys LLC
#
"""
Create Taiga stories for SPEC-115: Real-Time Features (WebSockets & SSE)

This script creates stories for the missing implementation items identified
during SPEC-115 validation.
"""

import os
import sys
from typing import Dict, List, Optional

import requests

# Taiga API configuration
TAIGA_URL = os.getenv("TAIGA_URL", "http://localhost:9000")
API_ENDPOINT = f"{TAIGA_URL}/api/v1"
TAIGA_USERNAME = os.getenv("TAIGA_USERNAME", "admin")
TAIGA_PASSWORD = os.getenv("TAIGA_PASSWORD", "admin123")

# SPEC-115 stories to create (with priorities per strategic implementation plan)
STORIES = [
    {
        "subject": "SPEC-115: Implement general-purpose FastAPI WebSocket router",
        "priority": "P1",
        "description": """**Goal**: Create general-purpose WebSocket router as specified in SPEC-115

**Priority:** P1 (Foundation)
**Dependency:** None - Base infrastructure for all other SPEC-115 stories

**Context**: SPEC-115 requires a general-purpose WebSocket router at `server/realtime/websocket.py`. Currently, only specific WebSocket endpoints exist for monitoring dashboards and widgets. This story creates the general-purpose infrastructure.

**Tasks**:
- [ ] Create `server/realtime/websocket.py` (or `services/core-api/realtime/websocket.py`)
- [ ] Implement FastAPI WebSocket router
- [ ] Create `/ws` endpoint (or `/realtime/ws`)
- [ ] Add WebSocket authentication (token validation)
- [ ] Implement connection acceptance
- [ ] Handle WebSocket disconnection
- [ ] Add ping/pong support
- [ ] Test WebSocket connection
- [ ] Document WebSocket endpoint

**Technical Requirements**:
- Endpoint: `/ws` (or `/realtime/ws`)
- Authentication: Token-based (query param or header)
- Support: Multiple connections per user
- Error handling: Graceful disconnection

**Acceptance Criteria**:
- ✅ General-purpose WebSocket router exists
- ✅ `/ws` endpoint accepts connections
- ✅ Authentication works
- ✅ Multiple connections per user supported
- ✅ Disconnection handled gracefully
- ✅ Tests pass
- ✅ Documentation complete

**Reference**: SPEC-115 Section 1 (FastAPI WebSocketRouter)""",
        "tags": ["spec-115", "websocket", "fastapi", "realtime"],
    },
    {
        "subject": "SPEC-115: Implement ConnectionManager class with Redis pub/sub integration",
        "priority": "P1",
        "description": """**Goal**: Implement ConnectionManager class with Redis pub/sub as specified in SPEC-115

**Priority:** P1 (Foundation)
**Dependency:** Requires Redis integration from SPEC-033

**Context**: SPEC-115 requires a ConnectionManager class that manages WebSocket connections and integrates with Redis pub/sub for event distribution. This is core infrastructure for real-time features.

**Tasks**:
- [ ] Create ConnectionManager class
- [ ] Implement `active_connections: Dict[str, Set[WebSocket]]`
- [ ] Implement `connect()` method
- [ ] Implement `disconnect()` method
- [ ] Implement `send_personal_message()` method
- [ ] Implement `broadcast()` method
- [ ] Implement `init_redis()` method
- [ ] Implement `listen_to_redis()` method
- [ ] Subscribe to Redis channels (`events:*`)
- [ ] Forward Redis messages to WebSocket clients
- [ ] Test connection management
- [ ] Test Redis pub/sub integration

**Technical Requirements**:
- Connection storage: `user_id -> Set[WebSocket]`
- Redis pub/sub: Subscribe to `events:*` pattern
- Message forwarding: Parse channel and route to appropriate users
- Error handling: Graceful failure handling

**Acceptance Criteria**:
- ✅ ConnectionManager class exists
- ✅ Connection management works (connect, disconnect)
- ✅ Personal messages work
- ✅ Broadcast messages work
- ✅ Redis pub/sub integration works
- ✅ Messages forwarded from Redis to WebSocket
- ✅ Tests pass
- ✅ Documentation complete

**Reference**: SPEC-115 Section 1 (ConnectionManager)""",
        "tags": ["spec-115", "websocket", "redis", "pubsub", "connection-manager"],
    },
    {
        "subject": "SPEC-115: Implement user-specific and global event channels",
        "priority": "P2",
        "description": """**Goal**: Implement Redis pub/sub channels for user-specific and global events

**Priority:** P2 (Core Integration)
**Dependency:** Builds on US#739 (WebSocket router) and US#740 (ConnectionManager)

**Context**: SPEC-115 requires Redis channels for routing events:
- User-specific: `events:user:{user_id}` - Events for specific users
- Global: `events:global` - System-wide events

**Tasks**:
- [ ] Design channel naming convention
- [ ] Implement user-specific channel routing (`events:user:{user_id}`)
- [ ] Implement global channel routing (`events:global`)
- [ ] Update ConnectionManager to subscribe to channels
- [ ] Parse channel names to determine target users
- [ ] Route messages to appropriate WebSocket connections
- [ ] Test user-specific event delivery
- [ ] Test global event delivery
- [ ] Document channel structure

**Channel Structure**:
- `events:user:{user_id}` - User-specific events
- `events:global` - Global events (broadcast to all)

**Acceptance Criteria**:
- ✅ User-specific channels work (`events:user:{user_id}`)
- ✅ Global channels work (`events:global`)
- ✅ Messages routed correctly
- ✅ Tests pass
- ✅ Documentation complete

**Reference**: SPEC-115 Section 2 (Redis Channel Events)""",
        "tags": ["spec-115", "redis", "pubsub", "channels", "events"],
    },
    {
        "subject": "SPEC-115: Implement EventPublisher for Redis pub/sub",
        "priority": "P3",
        "description": """**Goal**: Create EventPublisher class for publishing events to Redis pub/sub channels

**Priority:** P3 (Enhancement)
**Dependency:** Optional enhancement - can be implemented once US#740 (ConnectionManager) is stable

**Context**: SPEC-115 requires an EventPublisher class that publishes events to Redis pub/sub channels. Current implementation uses Redis Streams (different pattern). This story creates the pub/sub publisher.

**Tasks**:
- [ ] Create EventPublisher class (`server/realtime/events.py`)
- [ ] Implement `publish_user_event()` method
- [ ] Implement `publish_global_event()` method
- [ ] Connect to Redis pub/sub
- [ ] Format event messages (JSON with type, data, timestamp)
- [ ] Publish to user-specific channels
- [ ] Publish to global channels
- [ ] Integrate into API endpoints (e.g., memory creation)
- [ ] Test event publishing
- [ ] Document event format

**Event Format**:
```json
{
  "type": "memory_created",
  "data": {...},
  "timestamp": "2025-11-04T00:00:00Z"
}
```

**Acceptance Criteria**:
- ✅ EventPublisher class exists
- ✅ `publish_user_event()` works
- ✅ `publish_global_event()` works
- ✅ Events published to correct channels
- ✅ Event format matches SPEC
- ✅ Integration with API endpoints works
- ✅ Tests pass
- ✅ Documentation complete

**Reference**: SPEC-115 Section 2 (Redis Channel Events)""",
        "tags": ["spec-115", "redis", "pubsub", "events", "publisher"],
    },
    {
        "subject": "SPEC-115: Implement WebSocket authentication with token validation",
        "priority": "P2",
        "description": """**Goal**: Implement token-based authentication for WebSocket connections

**Priority:** P2 (Core Integration)
**Dependency:** Integrates with existing authentication middleware

**Context**: SPEC-115 requires WebSocket authentication using JWT tokens. Connections should be validated and closed if invalid.

**Tasks**:
- [ ] Create `get_current_user_ws()` function (WebSocket auth)
- [ ] Extract token from query parameter or header
- [ ] Validate JWT token
- [ ] Extract user_id from token
- [ ] Close connection if token invalid (code 1008, reason "Unauthorized")
- [ ] Test authentication success
- [ ] Test authentication failure
- [ ] Document authentication flow

**Authentication Flow**:
1. Client connects with token: `ws://host/ws?token=JWT_TOKEN`
2. Server validates token
3. If valid: Extract user_id, accept connection
4. If invalid: Close with code 1008

**Acceptance Criteria**:
- ✅ `get_current_user_ws()` function exists
- ✅ Token validation works
- ✅ Invalid tokens rejected
- ✅ User ID extracted correctly
- ✅ Tests pass
- ✅ Documentation complete

**Reference**: SPEC-115 Section 1 (WebSocket Authentication)""",
        "tags": ["spec-115", "websocket", "authentication", "jwt", "security"],
    },
    {
        "subject": "SPEC-115: Implement auto-reconnect with exponential backoff (frontend)",
        "priority": "P3",
        "description": """**Goal**: Implement auto-reconnect logic with exponential backoff for WebSocket connections

**Priority:** P3 (Enhancement)
**Dependency:** Can follow once backend infrastructure (US#739, US#740, US#741, US#743) is stable

**Context**: SPEC-115 requires automatic reconnection with exponential backoff for frontend WebSocket connections. Since architecture uses FastAPI templating (not Next.js), this needs to be implemented in Alpine.js or vanilla JavaScript.

**Tasks**:
- [ ] Create WebSocket connection wrapper (Alpine.js or vanilla JS)
- [ ] Implement connection state tracking
- [ ] Implement exponential backoff reconnection
- [ ] Backoff strategy: 1s, 2s, 4s, 8s, 16s (max 30s)
- [ ] Max 5 reconnection attempts
- [ ] Handle reconnection success
- [ ] Handle reconnection failure (after max attempts)
- [ ] Add ping/pong keepalive (every 30 seconds)
- [ ] Test reconnection logic
- [ ] Document usage

**Reconnection Strategy**:
- Initial delay: 1 second
- Exponential: 1s, 2s, 4s, 8s, 16s
- Max delay: 30 seconds
- Max attempts: 5

**Acceptance Criteria**:
- ✅ Auto-reconnect works
- ✅ Exponential backoff works
- ✅ Max attempts enforced
- ✅ Ping/pong keepalive works
- ✅ Tests pass
- ✅ Documentation complete

**Note**: Since architecture uses FastAPI templating (not Next.js), implement in Alpine.js or vanilla JavaScript instead of React hook.

**Reference**: SPEC-115 Section 3 (Auto-Reconnect), Section 4 (Next.js Hook - adapt for FastAPI templating)""",
        "tags": ["spec-115", "websocket", "frontend", "reconnect", "alpine.js"],
    },
    {
        "subject": "SPEC-115: Implement SSE fallback for older browsers",
        "priority": "P3",
        "description": """**Goal**: Implement Server-Sent Events (SSE) fallback for browsers that don't support WebSocket

**Priority:** P3 (Enhancement)
**Dependency:** Can follow once backend infrastructure (US#739, US#740, US#741, US#743) is stable

**Context**: SPEC-115 mentions SSE as a future enhancement for older browsers. This story implements SSE fallback.

**Tasks**:
- [ ] Create SSE endpoint (`/sse` or `/realtime/sse`)
- [ ] Implement SSE streaming response
- [ ] Detect WebSocket support in frontend
- [ ] Fallback to SSE if WebSocket not available
- [ ] Convert WebSocket messages to SSE format
- [ ] Test SSE connection
- [ ] Test SSE fallback
- [ ] Document SSE usage

**SSE Format**:
```
data: {"type": "memory_created", "data": {...}}\n\n
```

**Acceptance Criteria**:
- ✅ SSE endpoint exists
- ✅ SSE streaming works
- ✅ Frontend detects WebSocket support
- ✅ SSE fallback works
- ✅ Message format compatible
- ✅ Tests pass
- ✅ Documentation complete

**Reference**: SPEC-115 Section 9 (Future Enhancements - SSE fallback)""",
        "tags": ["spec-115", "sse", "server-sent-events", "fallback", "browser-compat"],
    },
]


def authenticate() -> str:
    """Authenticate with Taiga and return auth token."""
    response = requests.post(
        f"{API_ENDPOINT}/auth", json={"username": TAIGA_USERNAME, "password": TAIGA_PASSWORD, "type": "normal"}
    )
    response.raise_for_status()
    return response.json()["auth_token"]


def get_project_id(headers: Dict[str, str]) -> int:
    """Get ninaivalaigal project ID."""
    response = requests.get(f"{API_ENDPOINT}/projects/by_slug?slug=ninaivalaigal", headers=headers)
    response.raise_for_status()
    return response.json()["id"]


def create_story(headers: Dict[str, str], project_id: int, story: Dict, assignee_id: Optional[int]) -> Dict:
    """Create a Taiga user story."""
    # Add priority tag
    tags = story["tags"].copy()
    priority = story.get("priority", "")
    if priority:
        tags.append(f"priority-{priority.lower()}")

    story_data = {
        "project": project_id,
        "subject": story["subject"],
        "description": story["description"],
        "tags": tags,
        "status": 1,  # New
    }

    if assignee_id:
        story_data["assigned_to"] = assignee_id

    response = requests.post(f"{API_ENDPOINT}/userstories", headers=headers, json=story_data)
    response.raise_for_status()
    return response.json()


def main():
    """Main function."""
    print("🔐 Authenticating with Taiga...")
    auth_token = authenticate()
    headers = {"Authorization": f"Bearer {auth_token}"}

    print("📦 Getting project ID...")
    project_id = get_project_id(headers)

    print(f"\n📝 Creating {len(STORIES)} SPEC-115 stories...\n")

    created_stories = []
    for i, story in enumerate(STORIES, 1):
        priority = story.get("priority", "")
        print(f"{i}. Creating: {story['subject'][:60]}... (Priority: {priority})")
        try:
            # All stories unassigned
            created = create_story(headers, project_id, story, None)
            created_stories.append(created)
            print(f"   ✅ Created US#{created['ref']} (Priority: {priority}, unassigned)")
        except Exception as e:
            print(f"   ❌ Error: {e}")

    print(f"\n✅ Created {len(created_stories)} stories:")
    print("\n📊 Priority Breakdown:")
    print("   P1 (Foundation):")
    p1_stories = [s for s in created_stories if "priority-p1" in " ".join([str(t) for t in s.get("tags", [])]).lower()]
    for story in p1_stories:
        print(f"      - US#{story['ref']}: {story['subject'][:60]}...")
    print("   P2 (Core Integration):")
    p2_stories = [s for s in created_stories if "priority-p2" in " ".join([str(t) for t in s.get("tags", [])]).lower()]
    for story in p2_stories:
        print(f"      - US#{story['ref']}: {story['subject'][:60]}...")
    print("   P3 (Enhancements):")
    p3_stories = [s for s in created_stories if "priority-p3" in " ".join([str(t) for t in s.get("tags", [])]).lower()]
    for story in p3_stories:
        print(f"      - US#{story['ref']}: {story['subject'][:60]}...")

    print(f"\n📋 All Stories:")
    for story in created_stories:
        print(f"   - US#{story['ref']}: {story['subject'][:60]}...")
        print(f"     URL: {TAIGA_URL}/project/ninaivalaigal/us/{story['ref']}")


if __name__ == "__main__":
    main()
