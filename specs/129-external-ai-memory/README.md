# SPEC-129: External AI Memory API Integration

**Status:** 📋 Planned  
**Priority:** High  
**Owner:** Architecture / Platform  
**Version:** 0.1 (Draft)  
**Last Updated:** January 2025

**Note:** This SPEC was renumbered from SPEC-085 to SPEC-129.

---

## 🎯 Objective

Enable Ninaivalaigal to integrate with **external AI vendor memory APIs** (Claude Memory Tool, OpenAI Threads, GitHub Copilot memory, etc.) while ensuring Nina remains the **authoritative source of truth** for enterprise memory.

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

## 17. Implementation Status

**Status:** ⚠️ **Not Implemented** (0% implemented)

**Last Updated:** January 2025

### Current Status

**Not Implemented:**
- ❌ **Adapter Layer** - No `ExternalMemoryAdapter` base class or vendor adapters
- ❌ **Federation** - No federated query function or origin tagging
- ❌ **Governance & Security** - No RBAC/security middleware for vendor memory
- ❌ **Admin & Transparency** - No admin UI or origin tracking in logs/analytics
- ❌ **Security Infrastructure** - No API key management or rate limiting for vendors

**Dependencies Status:**
- ✅ **SPEC-012**: Memory Substrate - Complete - Ready
- ✅ **SPEC-020**: Memory Provider Architecture - Complete - Ready
- ✅ **SPEC-060/061**: Graph Intelligence & Reasoning - Complete - Ready
- ⚠️ **SPEC-080**: Trust Score System - **Planned** - Not blocking (can implement basic trust scoring)
- ⚠️ **SPEC-082**: Narrative Analytics Layer - **Planned** - Not blocking (can use SPEC-030 for basic analytics)
- ✅ **SPEC-009**: RBAC Policy Enforcement - Complete - Ready
- ✅ **SPEC-008**: Security Middleware - Complete - Ready
- ✅ **SPEC-011**: Data Lifecycle Management - Complete - Ready
- ✅ **SPEC-054**: Secret Management - Complete - Ready

**Note:** Basic AI integration code exists (`ai_integrations.py`) but is for general AI tool usage (queries/responses), not memory federation. SPEC-129 requires fetching memories from external vendor APIs and federating them with Nina memories.

**Dependency Assessment:**
- **SPEC-080 (Trust Score)**: Planned, not implemented. Can proceed with basic trust scoring (0.0-1.0) for vendors without full SPEC-080 implementation.
- **SPEC-082 (Narrative Analytics)**: Planned, not implemented. Can use SPEC-030 (Admin Analytics Console) for basic origin tracking until SPEC-082 is available.

---

## 18. Implementation Stories

**Status**: ✅ **Stories Created** (January 2025)

The following Taiga stories have been created to implement SPEC-129:

**Phase 1: Adapter Layer (3 weeks, HIGH)**
- **US#851**: SPEC-129 Phase 1: Adapter Layer (Claude + OpenAI) (unassigned)
  - `ExternalMemoryAdapter` base class, Claude adapter, OpenAI adapter, normalization

**Phase 2: Federation & Origin Tagging (2 weeks, HIGH)**
- **US#852**: SPEC-129 Phase 2: Federation & Origin Tagging (unassigned)
  - Federated query function, origin tagging, Graph Intelligence integration, trust-based ranking

**Phase 3: Governance & Admin UI (3 weeks, MEDIUM)**
- **US#853**: SPEC-129 Phase 3: Governance & Admin UI (unassigned)
  - RBAC application, security middleware, trust scores, admin UI toggles, analytics updates

**Phase 4: Security Infrastructure & Expansion (2 weeks, MEDIUM)**
- **US#854**: SPEC-129 Phase 4: Security Infrastructure & Expansion (unassigned)
  - API key management, rate limiting, audit trail, GitHub Copilot adapter

All stories are tagged with `spec-129` and are unassigned (can be picked up by any developer).

**Total Estimated Effort:** 10 weeks (50 story points)

**Status**: ✅ Created successfully (January 2025)

---

**Next Steps:**
1. ✅ Complete SPEC README document (done)
2. ✅ Verify dependencies (done - SPEC-080 and SPEC-082 are Planned, not blocking)
3. 📝 Create stories for implementation phases
4. 📋 Begin Phase 1 implementation (adapters)
