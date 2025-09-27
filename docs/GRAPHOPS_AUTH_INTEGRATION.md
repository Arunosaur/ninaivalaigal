# 🧠 GraphOps Auth Token Linking - Intelligence Routing Strategy

## Overview
This document outlines the integration strategy for linking authentication tokens with GraphOps infrastructure to enable intelligent memory routing and context-aware AI operations.

## 🎯 Strategic Vision

### Current State
- ✅ **Auth Layer**: JWT tokens with user context (user_id, email, account_type, role)
- ✅ **GraphOps Infrastructure**: Apache AGE + Redis with dual-architecture deployment
- ✅ **API Foundation**: FastAPI with proper route registration and validation

### Future State
- 🧠 **Intelligence Routing**: JWT tokens automatically create graph nodes and relationships
- 🔗 **Context Linking**: User sessions tied to memory graph embeddings
- 🚀 **Agent Inference**: Context tokens route to appropriate AI agent endpoints

## 🏗️ Architecture Integration

### Phase 1: Token-to-Graph Mapping (Immediate)
```python
# Enhanced JWT payload with graph context
jwt_payload = {
    "user_id": user.id,
    "email": user.email,
    "account_type": user.account_type,
    "role": user.role,
    "graph_node_id": f"user_{user.id}",           # Graph node reference
    "context_window": [],                          # Active memory contexts
    "agent_preferences": user.agent_preferences,   # AI routing preferences
    "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS),
}
```

### Phase 2: Memory Graph Integration (Next Sprint)
```python
# Auto-create user nodes in graph on login
@router.post("/login")
async def enhanced_login(login_data: UserLogin) -> dict[str, Any]:
    # ... existing auth logic ...

    # Create/update user node in graph
    await graph_reasoner.ensure_user_node(
        user_id=user.id,
        email=user.email,
        account_type=user.account_type,
        login_timestamp=datetime.utcnow()
    )

    # Link to active memory contexts
    active_contexts = await get_user_active_contexts(user.id)
    context_window = [ctx.id for ctx in active_contexts]

    # Enhanced JWT with graph context
    jwt_payload.update({
        "graph_node_id": f"user_{user.id}",
        "context_window": context_window,
        "last_graph_sync": datetime.utcnow().isoformat()
    })
```

### Phase 3: Agent Routing (Future)
```python
# Route API calls based on JWT context
@app.middleware("http")
async def intelligence_routing_middleware(request: Request, call_next):
    # Extract JWT and graph context
    jwt_token = extract_jwt_from_request(request)
    if jwt_token and "graph_node_id" in jwt_token:
        # Inject graph context into request
        request.state.graph_context = {
            "user_node": jwt_token["graph_node_id"],
            "context_window": jwt_token["context_window"],
            "agent_preferences": jwt_token.get("agent_preferences", {})
        }

    response = await call_next(request)
    return response
```

## 🔗 Implementation Roadmap

### Sprint 1: Foundation Enhancement
**Goal**: Link JWT tokens to graph nodes

#### Tasks:
1. **Enhance JWT Payload Structure**
   ```python
   # server/auth.py
   def create_enhanced_jwt(user, active_contexts=None):
       payload = {
           # ... existing fields ...
           "graph_node_id": f"user_{user.id}",
           "context_window": active_contexts or [],
           "agent_routing": {
               "preferred_model": user.preferred_ai_model,
               "context_depth": user.context_depth_preference,
               "memory_scope": user.memory_scope_preference
           }
       }
       return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
   ```

2. **Graph Node Auto-Creation**
   ```python
   # server/graph/auth_integration.py
   async def sync_user_to_graph(user_id: str, user_data: dict):
       """Create or update user node in graph on auth events"""
       user_node = UserNode(
           id=f"user_{user_id}",
           label="User",
           properties={
               "email": user_data["email"],
               "account_type": user_data["account_type"],
               "last_login": datetime.utcnow().isoformat(),
               "active_contexts": user_data.get("context_window", [])
           }
       )
       await graph_client.upsert_node(user_node)
   ```

3. **Context Window Management**
   ```python
   # server/context_manager.py
   async def get_user_context_window(user_id: str) -> List[str]:
       """Get active memory contexts for user"""
       # Query recent memory interactions
       # Return list of context IDs for JWT inclusion
       pass
   ```

### Sprint 2: Memory Routing
**Goal**: Route memory operations through graph context

#### Tasks:
1. **Memory-Graph Linking**
   ```python
   # Enhanced memory storage with graph relationships
   @router.post("/memory/store")
   async def store_memory_with_graph(
       memory_data: MemoryInput,
       current_user: User = Depends(get_current_user)
   ):
       # Store memory in traditional storage
       memory = await store_memory(memory_data)

       # Create memory node in graph
       memory_node = MemoryNode(
           id=f"memory_{memory.id}",
           content=memory.content,
           user_id=current_user.id
       )

       # Create relationships
       await graph_reasoner.create_relationship(
           from_node=f"user_{current_user.id}",
           to_node=f"memory_{memory.id}",
           relationship_type="CREATED"
       )

       return memory
   ```

2. **Context-Aware Retrieval**
   ```python
   @router.get("/memory/relevant")
   async def get_relevant_memories(
       query: str,
       current_user: User = Depends(get_current_user),
       graph_context: dict = Depends(get_graph_context)
   ):
       # Use graph context to enhance relevance scoring
       relevant_memories = await graph_reasoner.find_relevant_memories(
           user_node=graph_context["user_node"],
           query=query,
           context_window=graph_context["context_window"]
       )

       return relevant_memories
   ```

### Sprint 3: Agent Intelligence
**Goal**: Route to AI agents based on graph analysis

#### Tasks:
1. **Agent Routing Middleware**
   ```python
   # server/middleware/agent_routing.py
   @app.middleware("http")
   async def agent_intelligence_middleware(request: Request, call_next):
       if request.url.path.startswith("/ai/"):
           # Analyze graph context for optimal agent routing
           graph_context = request.state.graph_context
           optimal_agent = await determine_optimal_agent(graph_context)

           # Route to specialized agent endpoint
           request.state.target_agent = optimal_agent

       return await call_next(request)
   ```

2. **Context Injection**
   ```python
   # Inject relevant memories into AI requests
   @router.post("/ai/chat")
   async def ai_chat_with_context(
       message: str,
       current_user: User = Depends(get_current_user)
   ):
       # Get relevant context from graph
       context_memories = await graph_reasoner.get_conversation_context(
           user_id=current_user.id,
           current_message=message
       )

       # Inject into AI prompt
       enhanced_prompt = build_contextual_prompt(message, context_memories)

       return await ai_agent.process(enhanced_prompt)
   ```

## 🔧 Technical Implementation

### Database Schema Extensions
```sql
-- Add graph context to users table
ALTER TABLE users ADD COLUMN graph_node_id VARCHAR(255);
ALTER TABLE users ADD COLUMN agent_preferences JSONB DEFAULT '{}';
ALTER TABLE users ADD COLUMN context_depth_preference INTEGER DEFAULT 5;

-- Memory-graph linking table
CREATE TABLE memory_graph_links (
    id SERIAL PRIMARY KEY,
    memory_id INTEGER REFERENCES memories(id),
    graph_node_id VARCHAR(255),
    relationship_type VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW()
);
```

### Redis Caching Strategy
```python
# Cache graph context for performance
GRAPH_CONTEXT_CACHE_TTL = 300  # 5 minutes

async def cache_user_graph_context(user_id: str, context: dict):
    await redis_client.setex(
        f"graph_context:{user_id}",
        GRAPH_CONTEXT_CACHE_TTL,
        json.dumps(context)
    )

async def get_cached_graph_context(user_id: str) -> dict:
    cached = await redis_client.get(f"graph_context:{user_id}")
    return json.loads(cached) if cached else {}
```

### API Endpoint Extensions
```python
# New endpoints for graph-auth integration
@router.get("/auth/graph-context")
async def get_user_graph_context(current_user: User = Depends(get_current_user)):
    """Get current user's graph context and relationships"""
    return await graph_reasoner.get_user_context(current_user.id)

@router.post("/auth/sync-graph")
async def sync_user_to_graph(current_user: User = Depends(get_current_user)):
    """Manually sync user data to graph (for debugging)"""
    await sync_user_to_graph(current_user.id, current_user.dict())
    return {"status": "synced"}

@router.get("/auth/agent-preferences")
async def get_agent_preferences(current_user: User = Depends(get_current_user)):
    """Get user's AI agent routing preferences"""
    return current_user.agent_preferences
```

## 🧪 Testing Strategy

### Unit Tests
```python
# tests/test_graph_auth_integration.py
async def test_jwt_includes_graph_context():
    user = create_test_user()
    jwt_token = create_enhanced_jwt(user, ["context_1", "context_2"])

    decoded = jwt.decode(jwt_token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    assert "graph_node_id" in decoded
    assert decoded["context_window"] == ["context_1", "context_2"]

async def test_user_node_creation_on_login():
    # Test that login creates/updates graph node
    pass

async def test_memory_graph_linking():
    # Test that memory storage creates graph relationships
    pass
```

### Integration Tests
```python
# tests/test_agent_routing.py
async def test_context_aware_memory_retrieval():
    # Test that graph context improves memory relevance
    pass

async def test_agent_routing_based_on_context():
    # Test that AI requests route to optimal agents
    pass
```

## 📊 Performance Considerations

### Optimization Strategies
1. **Graph Context Caching**: 5-minute Redis cache for user graph context
2. **Lazy Loading**: Load graph context only when needed for AI operations
3. **Batch Operations**: Batch graph updates for multiple auth events
4. **Connection Pooling**: Dedicated graph database connection pool

### Monitoring Metrics
- Graph context cache hit rate
- Average graph query response time
- Memory retrieval relevance scores
- Agent routing accuracy

## 🚀 Deployment Strategy

### Phase 1 Deployment (Low Risk)
- Deploy enhanced JWT structure
- Add graph context caching
- No breaking changes to existing auth flow

### Phase 2 Deployment (Medium Risk)
- Enable memory-graph linking
- Add context-aware retrieval
- Gradual rollout with feature flags

### Phase 3 Deployment (High Value)
- Enable full agent routing
- Context injection for AI operations
- Complete intelligence platform activation

## 🔮 Future Enhancements

### Advanced Features
1. **Predictive Context Loading**: Pre-load likely relevant memories
2. **Cross-User Context Sharing**: Team/org memory context sharing
3. **Temporal Graph Analysis**: Time-based context evolution
4. **Multi-Modal Context**: Image, audio, document context linking

### AI Agent Specialization
1. **Code Context Agent**: Specialized for development contexts
2. **Meeting Context Agent**: Optimized for meeting memories
3. **Research Context Agent**: Enhanced for research and documentation
4. **Creative Context Agent**: Tuned for creative and brainstorming contexts

---

**Implementation Priority**: Start with Phase 1 (JWT enhancement) immediately after current auth stabilization is complete. This provides the foundation for all future intelligence features while maintaining backward compatibility.
