# Implementation Guide

## Implementation Hooks

These hooks are the primary integration points for the Context Bridge system into the existing codebase. They are designed to be minimally invasive and leverage existing infrastructure where possible.

### 1. e*M Memory Provider Interface Extension

**File**: `server/memory_provider.py`

```python
class MemoryProvider:
    """Extended for cross-context fetch"""
    
    async def fetch_cross_context(
        self, 
        memory_id: str, 
        source_context: str,
        trust_score: int
    ) -> Memory:
        """
        Fetch memory from another context via bridge
        
        Integration Point: Extends existing e*M interface
        """
        bridge = ContextBridge.get_active(memory_id, source_context)
        
        if not bridge:
            raise NoBridgeError()
        
        if bridge.trust_score < trust_score:
            raise InsufficientTrustError()
        
        if bridge.mode == "reference":
            return bridge.resolve()  # Live fetch
        elif bridge.mode == "clone":
            return Memory.get(bridge.clone_id)  # Local copy
        elif bridge.mode == "hybrid":
            return bridge.get_with_sync()  # Smart fetch
```

---

### 2. ContextBridgeResolver Class

**File**: `server/context_bridge_resolver.py` (new)

```python
class ContextBridgeResolver:
    """
    Resolves cross-context references
    Integration: SPEC-063 Reasoner Layer
    """
    
    def __init__(self, reasoner):
        self.reasoner = reasoner  # From SPEC-063
        
    async def resolve_reference(
        self,
        memory_id: str,
        requesting_context: str
    ) -> Memory:
        """
        Resolve reference with trust checking
        
        Integrates with:
        - SPEC-043 (ACL)
        - SPEC-063 (Reasoner)
        - SPEC-101 (Federation)
        """
        # Check ACL
        if not self.reasoner.check_acl(memory_id, requesting_context):
            raise AccessDeniedError()
        
        # Get trust score
        trust = TrustScoreCalculator().calculate_trust_score(
            source=requesting_context,
            target=Memory.get(memory_id).context_id
        )
        
        # Resolve via bridge
        bridge = ContextBridge.find(memory_id, requesting_context)
        
        if bridge.mode == "reference":
            return await self.resolve_reference_mode(bridge, trust)
        elif bridge.mode == "clone":
            return await self.resolve_clone_mode(bridge, trust)
        elif bridge.mode == "hybrid":
            return await self.resolve_hybrid_mode(bridge, trust)
```

---

### 3. Integration with nv-api Routes

**File**: `server/routers/context_bridge.py` (new)

```python
from fastapi import APIRouter, Depends
from server.auth import get_current_user
from server.context_bridge_resolver import ContextBridgeResolver

router = APIRouter(prefix="/v1/context/bridge", tags=["context-bridge"])

@router.post("/share")
async def create_bridge(
    request: BridgeCreateRequest,
    current_user: User = Depends(get_current_user)
):
    """Create context bridge - integrates with existing auth"""
    # Uses existing JWT auth from SPEC-045
    # Uses existing ACL from SPEC-043
    # Uses existing GraphOps from SPEC-061
    
    bridge = await ContextBridgeService.create(
        source_memory_id=request.source_memory_id,
        target_context_id=request.target_context_id,
        mode=request.mode,
        user_id=current_user.id
    )
    
    return bridge.to_dict()
```

**Integration**: Add to `server/main.py`:
```python
from server.routers import context_bridge

app.include_router(context_bridge.router)
```

---

## Codebase Tie-ins

### With e*M (Existing Memory System)

```python
# server/memory.py (existing)
class Memory:
    # ... existing fields ...
    
    # NEW: Cross-context fields
    derived_from: Optional[UUID]  # For clone mode
    bridge_id: Optional[UUID]     # Link to active bridge
    
    @property
    def is_cross_context(self) -> bool:
        """Check if this memory is cross-context"""
        return self.bridge_id is not None
    
    async def resolve_if_reference(self) -> "Memory":
        """
        If this is a reference, resolve to actual memory
        Integration: Transparent to existing code
        """
        if not self.is_cross_context:
            return self
        
        bridge = ContextBridge.get(self.bridge_id)
        if bridge.mode == "reference":
            return await bridge.resolve()
        else:
            return self  # Already local (clone/hybrid)
```

### With nv-api (Existing API Layer)

```python
# server/routers/memories.py (existing)
@router.get("/memories/{memory_id}")
async def get_memory(
    memory_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Existing endpoint - NO CHANGES NEEDED
    Cross-context resolution happens transparently
    """
    memory = await MemoryService.get(memory_id)
    
    # NEW: Automatic cross-context resolution
    if memory.is_cross_context:
        memory = await memory.resolve_if_reference()
    
    return memory
```

---

## Database Migrations

### Alembic Migration: 0128_context_bridges

**File**: `alembic/versions/0128_context_bridges.py`

```python
"""Add context bridge tables

Revision ID: 0128_context_bridges
Revises: 0114_refresh_tokens
Create Date: 2025-10-13 08:00:00

"""

def upgrade() -> None:
    # Add bridge_id to memories table
    op.add_column('memories', 
        sa.Column('bridge_id', postgresql.UUID(as_uuid=True), nullable=True)
    )
    op.add_column('memories',
        sa.Column('derived_from', postgresql.UUID(as_uuid=True), nullable=True)
    )
    
    # Create context_bridges table
    op.create_table(
        'context_bridges',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('source_memory_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('target_context_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('mode', sa.String(20), nullable=False),
        sa.Column('trust_score', sa.Integer, nullable=False),
        sa.Column('created_at', sa.DateTime, nullable=False),
        # ... more columns from database-schema.md
    )
    
    # Create trust_scores table
    op.create_table('trust_scores', ...)
    
    # Create bridge_access_history table
    op.create_table('bridge_access_history', ...)
```

---

## GraphOps Integration

### Graph Schema Extension

**File**: `server/graphops/schema.py`

```python
# Existing graph schema (SPEC-061)
# NEW: Add bridge relationships

class ContextBridgeGraph:
    """
    Extends existing Apache AGE schema
    Integration: SPEC-061 (Property Graph)
    """
    
    @staticmethod
    def create_reference_edge(source_mem_id, target_mem_id, trust_score):
        """Create REFERENCES edge in graph"""
        query = """
        MATCH (source:Memory {id: $source_id})
        MATCH (target:Memory {id: $target_id})
        CREATE (source)-[r:REFERENCES {
            trust_score: $trust_score,
            created_at: timestamp()
        }]->(target)
        RETURN r
        """
        return graph.cypher_query(query, {
            "source_id": source_mem_id,
            "target_id": target_mem_id,
            "trust_score": trust_score
        })
```

---

## Success Criteria (Measurable)

### Performance Targets:

1. **<50ms traversal latency per bridge edge** (target)
   - Measure: `SELECT AVG(response_time_ms) FROM bridge_access_history`
   
2. **Full audit via /context-bridge/audit endpoint**
   - Measure: Every access logged
   - Test: `SELECT COUNT(*) FROM bridge_access_history WHERE action='reference_accessed'`

### Compliance:
- All access auditable
- Trust scores calculated per formula
- SPEC-050 policy alignment enforced

---

## Testing Strategy

### Unit Tests:
```python
# tests/test_context_bridge.py
def test_reference_mode_resolution():
    bridge = ReferenceLink(source_mem_id, target_ctx_id)
    resolved = bridge.resolve()
    assert resolved.id == source_mem_id
    
def test_trust_score_calculation():
    score = TrustScoreCalculator().calculate_trust_score(ctx_a, ctx_b)
    assert 0 <= score <= 100
```

### Integration Tests:
```python
# tests/integration/test_cross_context_fetch.py
async def test_cross_context_memory_fetch():
    # Create bridge
    bridge = await ContextBridgeService.create(...)
    
    # Fetch via bridge
    memory = await MemoryProvider().fetch_cross_context(...)
    
    # Verify audit log
    audit = AuditLog.get_latest()
    assert audit.action == "reference_accessed"
```

### E2E Tests:
```python
# tests/e2e/test_context_bridge_flow.py
async def test_complete_bridge_lifecycle():
    # Create → Access → Update → Revoke
    bridge = await client.post("/context-bridge/share", ...)
    memory = await client.get(f"/memories/{mem_id}")
    update = await client.patch(f"/context-bridge/share/{bridge.id}", ...)
    revoke = await client.delete(f"/context-bridge/share/{bridge.id}")
```

---

## Performance Benchmarks

Performance is a critical success factor for the Context Bridge system. The following benchmarks must be met before this SPEC is considered complete.

| Metric | Threshold | Measurement Method |
|---|---|---|
| Bridge Creation | < 100ms | Time from API request to DB commit for a new bridge. |
| Federated Query (1-hop) | < 150ms | Time to resolve a query that traverses one bridge. |
| Federated Query (3-hops) | < 400ms | Time to resolve a query that traverses three bridges. |
| Trust Score Calculation | < 20ms | Time to calculate a trust score between two contexts. |
| Cache Hit Rate | > 90% | Percentage of federated queries served from the cache. |

---

## Deployment Checklist

- [ ] Database migrations applied (`alembic upgrade head`)
- [ ] GraphOps schema updated
- [ ] Redis cache configured
- [ ] API routes registered
- [ ] Trust score calculator deployed
- [ ] Audit logging enabled
- [ ] Performance monitoring active (<50ms target)
- [ ] Documentation deployed

