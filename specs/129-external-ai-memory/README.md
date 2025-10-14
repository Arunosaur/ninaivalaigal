---
{}
---




## 🔑 Scope

### 1. Adapter Layer

**Implement pluggable adapters for external vendor APIs:**

- Normalize vendor responses into Ninaivalaigal's **Memory Substrate (SPEC-012)**.
- Support at least:
  - Anthropic Claude Memory Tool
  - OpenAI Persistent Threads / Assistants API
  - GitHub Copilot context memory

### 2. Federation

**Integrate vendor memory into Graph Intelligence (SPEC-060/061):**

- Vendor memories are marked as **external** but queryable alongside native Nina memories.
- Clear origin tags distinguish Nina-native vs vendor-sourced memories.

### 3. Governance & Security

**Apply RBAC policies (SPEC-009) and Security Middleware (SPEC-008) to all vendor memory data:**

- Lifecycle and retention follow **SPEC-011**.
- Assign **Trust Scores (SPEC-080)** to vendor data based on reliability and usage frequency.

### 4. Admin & Transparency

**UI toggle in Admin Console (SPEC-025, SPEC-068) to enable/disable vendor memory connectors per tenant:**

- Logs and analytics (SPEC-030, SPEC-082) must clearly show whether a memory originated from Nina or an external vendor.

---

## 🛡️ Security & Compliance

- **Vendor APIs must not bypass Ninaivalaigal's compliance gates.**
- **All vendor data flows through Nina's redaction, encryption, and audit pipeline.**
- **Data sovereignty:** external memory storage is **flagged as external** to avoid confusion in compliance reporting.

---

## 📈 Impact

### Keeps Nina AI-agnostic and future-proof
- No vendor lock-in

### Strengthens Nina's value
- Enterprise memory with governance vs. personal memory in Claude/OpenAI

### Supports hybrid adoption
- Customers can test vendor memory APIs while centralizing enterprise memory in Nina

### Marketing/BD advantage
- *"Claude and OpenAI store memory for individuals. Nina federates, secures, and scales memory across enterprises."*

---

## 🔗 Dependencies

- **SPEC-012:** Memory Substrate
- **SPEC-020:** Memory Provider Architecture
- **SPEC-060/061:** Graph Intelligence & Reasoning
- **SPEC-080:** Trust Score System
- **SPEC-082:** Narrative Analytics Layer

---

## 📊 Status

- 📋 **Planned** – target **Q1 2025** for prototype adapters (Claude + OpenAI).
- 🚀 **Integration rollout** with GitHub Copilot in **Q2 2025**.

---

## ✅ Acceptance Criteria

1. **Adapters exist for at least 2 vendor memory APIs.**
2. **Vendor memories can be federated into Nina queries with clear origin tags.**
3. **RBAC, Trust Scores, and retention policies apply consistently.**
4. **Admin UI allows toggling vendor connectors per tenant.**
5. **External memory logs are visible in Audit & Analytics dashboards.**

---

## 🎯 Implementation Notes

### Adapter Pattern
```python
class ExternalMemoryAdapter(ABC):
    """Base adapter for external AI memory APIs"""

    @abstractmethod
    async def fetch_memories(self, user_id: str, context: str) -> List[Memory]:
        """Fetch memories from external API"""
        pass

    @abstractmethod
    async def normalize_to_substrate(self, external_data: Any) -> Memory:
        """Convert external format to Nina Memory Substrate"""
        pass

    @abstractmethod
    def get_trust_score(self) -> float:
        """Return trust score for this vendor (0.0-1.0)"""
        pass
```

### Claude Memory Adapter
```python
class ClaudeMemoryAdapter(ExternalMemoryAdapter):
    """Adapter for Anthropic Claude Memory Tool"""

    async def fetch_memories(self, user_id: str, context: str) -> List[Memory]:
        # Call Claude API
        # Mark as external=True
        # Apply trust score
        pass
```

### OpenAI Threads Adapter
```python
class OpenAIThreadsAdapter(ExternalMemoryAdapter):
    """Adapter for OpenAI Persistent Threads"""

    async def fetch_memories(self, user_id: str, context: str) -> List[Memory]:
        # Call OpenAI Assistants API
        # Extract thread context
        # Normalize to Memory Substrate
        pass
```

### Federation Query
```python
async def query_federated_memories(
    user_id: str,
    query: str,
    include_external: bool = True
) -> List[Memory]:
    """Query both Nina and external memories"""

    # Get Nina-native memories
    nina_memories = await memory_service.query(user_id, query)

    if include_external:
        # Get external memories from enabled adapters
        external_memories = []
        for adapter in enabled_adapters:
            ext_mems = await adapter.fetch_memories(user_id, query)
            external_memories.extend(ext_mems)

        # Combine and rank by relevance + trust score
        all_memories = nina_memories + external_memories
        return rank_by_relevance_and_trust(all_memories)

    return nina_memories
```

---

## 🔐 Security Considerations

### API Key Management
- Store vendor API keys in secure vault (SPEC-054)
- Per-tenant API key configuration
- Rate limiting per vendor

### Data Isolation
- External memories stored separately
- Clear tagging: `source=external`, `vendor=claude`
- Audit trail for all external API calls

### Compliance
- GDPR: Right to delete includes external memories
- Data residency: Flag external storage locations
- Encryption: All vendor API calls over TLS

---

## 📋 Rollout Plan

### Phase 1: Prototype (Q1 2025)
- Implement Claude Memory adapter
- Implement OpenAI Threads adapter
- Basic federation queries

### Phase 2: Production (Q2 2025)
- Admin UI for vendor toggles
- Trust score integration
- Analytics dashboard updates

### Phase 3: Expansion (Q3 2025)
- GitHub Copilot adapter
- Additional vendor support
- Advanced federation strategies

---

**Related SPECs:**
- SPEC-012: Memory Substrate
- SPEC-020: Memory Provider Architecture
- SPEC-060/061: Graph Intelligence
- SPEC-080: Trust Score System
- SPEC-082: Narrative Analytics
