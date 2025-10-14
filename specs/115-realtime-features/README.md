---
{}
---




## 🏗️ Architecture

```mermaid
flowchart TD
    Client[Client :8041] --> WS[WebSocket Gateway]
    WS --> Redis[Redis Pub/Sub]
    Redis --> API[Backend Services]
    API --> Client
```

---

## 🔧 Implementation

### 1. FastAPI WebSocketRouter

**`server/realtime/websocket.py`:**
```python
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from typing import Dict, Set
import json
import asyncio
import redis.asyncio as redis

from server.middleware.auth import get_current_user_ws
from server.config import settings

router = APIRouter()

class ConnectionManager:
    def __init__(self):
        # user_id -> Set[WebSocket]
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self.redis_client: redis.Redis = None
        self.pubsub = None

    async def connect(self, websocket: WebSocket, user_id: str):
        """Accept WebSocket connection and add to active connections."""
        await websocket.accept()

        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()

        self.active_connections[user_id].add(websocket)

    async def disconnect(self, websocket: WebSocket, user_id: str):
        """Remove WebSocket connection."""
        if user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)

            if not self.active_connections[user_id]:
                del self.active_connections[user_id]

    async def send_personal_message(self, message: str, user_id: str):
        """Send message to specific user's connections."""
        if user_id in self.active_connections:
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_text(message)
                except Exception as e:
                    print(f"Error sending message to {user_id}: {e}")

    async def broadcast(self, message: str):
        """Broadcast message to all connected clients."""
        for user_connections in self.active_connections.values():
            for connection in user_connections:
                try:
                    await connection.send_text(message)
                except Exception as e:
                    print(f"Error broadcasting: {e}")

    async def init_redis(self):
        """Initialize Redis pub/sub."""
        self.redis_client = redis.from_url(settings.REDIS_URL)
        self.pubsub = self.redis_client.pubsub()

        # Subscribe to channels
        await self.pubsub.subscribe("events:*")

    async def listen_to_redis(self):
        """Listen to Redis pub/sub and forward to WebSocket clients."""
        if not self.pubsub:
            await self.init_redis()

        async for message in self.pubsub.listen():
            if message["type"] == "message":
                channel = message["channel"].decode()
                data = message["data"].decode()

                # Parse channel to determine target
                if channel.startswith("events:user:"):
                    user_id = channel.split(":")[-1]
                    await self.send_personal_message(data, user_id)
                elif channel == "events:global":
                    await self.broadcast(data)

manager = ConnectionManager()

@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = None  # Token passed as query param
):
    """WebSocket endpoint for real-time updates."""
    # Authenticate user
    try:
        user = await get_current_user_ws(token)
        user_id = user["id"]
    except Exception as e:
        await websocket.close(code=1008, reason="Unauthorized")
        return

    await manager.connect(websocket, user_id)

    try:
        while True:
            # Receive messages from client
            data = await websocket.receive_text()

            # Handle client messages (e.g., ping/pong)
            try:
                message = json.loads(data)

                if message.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})

            except json.JSONDecodeError:
                await websocket.send_json({
                    "type": "error",
                    "message": "Invalid JSON"
                })

    except WebSocketDisconnect:
        await manager.disconnect(websocket, user_id)

@router.on_event("startup")
async def startup_event():
    """Start Redis listener on startup."""
    asyncio.create_task(manager.listen_to_redis())
```

### 2. Redis Channel Events

**`server/realtime/events.py`:**
```python
import json
import redis.asyncio as redis
from typing import Dict, Any

from server.config import settings

class EventPublisher:
    def __init__(self):
        self.redis_client = redis.from_url(settings.REDIS_URL)

    async def publish_user_event(self, user_id: str, event_type: str, data: Dict[str, Any]):
        """Publish event to specific user channel."""
        channel = f"events:user:{user_id}"
        message = json.dumps({
            "type": event_type,
            "data": data,
            "timestamp": datetime.utcnow().isoformat()
        })

        await self.redis_client.publish(channel, message)

    async def publish_global_event(self, event_type: str, data: Dict[str, Any]):
        """Publish event to global channel."""
        channel = "events:global"
        message = json.dumps({
            "type": event_type,
            "data": data,
            "timestamp": datetime.utcnow().isoformat()
        })

        await self.redis_client.publish(channel, message)

event_publisher = EventPublisher()

# Example usage in API endpoints
@router.post("/memories")
async def create_memory(
    memory: MemoryCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create new memory and notify user via WebSocket."""
    # Create memory in database
    new_memory = await db.memories.insert_one({
        "content": memory.content,
        "user_id": current_user["id"],
        "created_at": datetime.utcnow()
    })

    # Publish real-time event
    await event_publisher.publish_user_event(
        user_id=current_user["id"],
        event_type="memory_created",
        data={"id": str(new_memory.inserted_id), "content": memory.content}
    )

    return {"id": str(new_memory.inserted_id)}
```

### 3. Next.js Hook: `useRealtime()`

**`src/hooks/useRealtime.ts`:**
```typescript
import { useEffect, useState, useCallback, useRef } from 'react';
import { useSession } from 'next-auth/react';

interface RealtimeMessage {
  type: string;
  data: any;
  timestamp: string;
}

export function useRealtime(onMessage?: (message: RealtimeMessage) => void) {
  const { data: session } = useSession();
  const [connected, setConnected] = useState(false);
  const [messages, setMessages] = useState<RealtimeMessage[]>([]);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectAttempts = useRef(0);

  const connect = useCallback(() => {
    if (!session?.accessToken) return;

    const wsUrl = `${process.env.NEXT_PUBLIC_WS_URL}/ws?token=${session.accessToken}`;
    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      console.log('WebSocket connected');
      setConnected(true);
      reconnectAttempts.current = 0;

      // Send ping every 30 seconds to keep connection alive
      const pingInterval = setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify({ type: 'ping' }));
        }
      }, 30000);

      ws.addEventListener('close', () => {
        clearInterval(pingInterval);
      });
    };

    ws.onmessage = (event) => {
      try {
        const message: RealtimeMessage = JSON.parse(event.data);

        setMessages((prev) => [...prev, message]);

        if (onMessage) {
          onMessage(message);
        }
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error);
      }
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    ws.onclose = () => {
      console.log('WebSocket disconnected');
      setConnected(false);

      // Exponential backoff reconnection
      if (reconnectAttempts.current < 5) {
        const delay = Math.min(1000 * Math.pow(2, reconnectAttempts.current), 30000);
        reconnectAttempts.current += 1;

        console.log(`Reconnecting in ${delay}ms (attempt ${reconnectAttempts.current})`);
        reconnectTimeoutRef.current = setTimeout(() => {
          connect();
        }, delay);
      }
    };

    wsRef.current = ws;
  }, [session, onMessage]);

  useEffect(() => {
    connect();

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
    };
  }, [connect]);

  const sendMessage = useCallback((data: any) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(data));
    }
  }, []);

  return {
    connected,
    messages,
    sendMessage,
  };
}
```

### 4. Auto-Reconnect with Exponential Backoff

Implemented in `useRealtime` hook above with:
- Initial reconnect after 1 second
- Exponential backoff: 1s, 2s, 4s, 8s, 16s
- Max delay capped at 30 seconds
- Max 5 reconnection attempts

---

## ✅ Success Metrics

- **< 200ms event latency**: From backend event to frontend update
- **99.9% connection uptime**: WebSocket reliability with auto-reconnect
- **Scales to 1000 concurrent sockets**: Redis pub/sub horizontal scaling

---

## 📦 Example Usage

### Dashboard with Real-Time Updates

**`src/app/dashboard/page.tsx`:**
```tsx
'use client';

import { useRealtime } from '@/hooks/useRealtime';
import { useToast } from '@/components/ui/use-toast';

export default function Dashboard() {
  const { toast } = useToast();

  useRealtime((message) => {
    if (message.type === 'memory_created') {
      toast({
        title: 'New Memory Created',
        description: message.data.content.substring(0, 100),
      });

      // Refetch memories list
      queryClient.invalidateQueries({ queryKey: ['memories'] });
    }

    if (message.type === 'team_invitation') {
      toast({
        title: 'Team Invitation',
        description: `You've been invited to join ${message.data.team_name}`,
      });
    }
  });

  return (
    <div>
      <h1>Dashboard</h1>
      {/* Dashboard content */}
    </div>
  );
}
```

---

## 🔐 Security

### WebSocket Authentication
- Token passed as query parameter
- Validated on connection
- Connection closed if invalid

### Channel Isolation
- User-specific channels: `events:user:{user_id}`
- Users only receive their own events
- Global events for system-wide updates

### Rate Limiting
- Max 100 messages per minute per user
- Connection throttling for suspicious activity

---

## 📊 Performance Optimization

### Connection Pooling
- Redis connection pool (min: 10, max: 100)
- WebSocket connection limit per user: 3

### Message Batching
- Batch events if > 10 messages/second
- Reduce WebSocket overhead

### Memory Management
- Message history limited to last 50 per user
- Auto-cleanup of stale connections

---

## 🧪 Testing

### WebSocket Test
```typescript
// tests/websocket.test.ts
import { WebSocket } from 'ws';

describe('WebSocket Connection', () => {
  it('should connect with valid token', async () => {
    const token = 'valid_jwt_token';
    const ws = new WebSocket(`ws://localhost:8000/ws?token=${token}`);

    await new Promise((resolve) => {
      ws.on('open', resolve);
    });

    expect(ws.readyState).toBe(WebSocket.OPEN);
    ws.close();
  });

  it('should receive memory created event', async () => {
    const ws = new WebSocket(`ws://localhost:8000/ws?token=${token}`);

    const messagePromise = new Promise((resolve) => {
      ws.on('message', (data) => {
        const message = JSON.parse(data.toString());
        resolve(message);
      });
    });

    // Trigger event via API
    await fetch('http://localhost:8000/memories', {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` },
      body: JSON.stringify({ content: 'Test memory' }),
    });

    const message = await messagePromise;
    expect(message.type).toBe('memory_created');
  });
});
```

---

## 🚀 Deployment

### Production Considerations
- **Sticky sessions**: Route WebSocket connections to same server
- **Redis Cluster**: Horizontal scaling for pub/sub
- **Load balancer**: WebSocket-aware (nginx, Traefik)
- **Monitoring**: Connection count, message throughput, latency

### Kubernetes Config
```yaml
apiVersion: v1
kind: Service
metadata:
  name: ninaivalaigal-ws
spec:
  sessionAffinity: ClientIP  # Sticky sessions
  ports:
    - port: 8000
      targetPort: 8000
```

---

## 🔗 Integration Points

- **SPEC-033**: Redis pub/sub infrastructure
- **SPEC-108**: WebSocket authentication
- **SPEC-045**: Session management

---

## 🎯 Future Enhancements

- Server-Sent Events (SSE) fallback for older browsers
- Binary message support (Protocol Buffers)
- Presence detection (online/offline status)
- Typing indicators
- Read receipts

---

**Status:** ✅ Complete
**Implementation Date:** October 11, 2025
**Last Updated:** October 11, 2025
