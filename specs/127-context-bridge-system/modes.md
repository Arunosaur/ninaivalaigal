# Reference vs Clone vs Hybrid Modes

## Mode Comparison

| Feature | Reference Mode | Clone Mode | Hybrid Mode |
|---------|---------------|------------|-------------|
| **Storage** | Pointer to original | Full copy | Copy + sync metadata |
| **Updates** | Live, automatic | Never | Triggered sync |
| **Performance** | Fast (no duplication) | Slower (duplication) | Balanced |
| **Security** | Requires high trust | Fully isolated | Configurable |
| **Use Case** | Internal collaboration | External partners | Staged rollout |
| **Data Consistency** | Always current | Point-in-time | Eventually consistent |
| **Revocation** | Instant | N/A (already copied) | Stops future syncs |
| **Trust Required** | ≥70 | ≥50 | ≥70 |

---

## Reference Mode

**Description**: Live link to original memory - no duplication.

**When to Use**:
- Internal team collaboration
- High-trust contexts (same org)
- Need latest data always
- Want to minimize storage

**Implementation**:
```python
class ReferenceLink:
    def resolve(self):
        """Always fetch latest from source"""
        if self.current_trust_score < 70:
            raise InsufficientTrustError()
        return Memory.get(self.source_memory_id)
```

---

## Clone Mode

**Description**: Deep copy - isolated from original.

**When to Use**:
- External partners
- Lower-trust contexts
- Need data stability
- Compliance requirements (data isolation)

**Implementation**:
```python
class MemoryClone:
    def create(self):
        """Create independent copy"""
        original = Memory.get(self.source_memory_id)
        clone = Memory.create(
            content=original.content.copy(),
            context_id=self.target_context_id,
            derived_from=self.source_memory_id
        )
        return clone
```

---

## Hybrid Mode

**Description**: Clone with sync triggers.

**When to Use**:
- Partner organizations
- Staged rollout
- Need both isolation and updates
- Periodic sync acceptable

**Sync Triggers**:
- `on_update`: Sync when original changes
- `scheduled`: Sync on schedule (hourly/daily)
- `manual`: Sync on demand

**Implementation**:
```python
class HybridSync:
    def on_source_update(self, original_memory):
        if self.should_sync():
            clone = Memory.get(self.clone.id)
            clone.update_from_source(original_memory)
```
