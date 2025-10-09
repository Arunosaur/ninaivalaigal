# SPEC-090: Approval Chain Processing (ACP)

## 🎯 Objective
Define a robust and modular **Approval Chain Processing (ACP)** framework for workflow-driven memory and action validation within the Ninaivalaigal platform.

## 🧩 Context
Many agentic and memory-layer operations (publishing, sharing, or mutating data) require approval workflows across roles or systems. This SPEC defines a scalable approval chain engine with role-based routing, retry logic, and audit persistence.

## 🏗️ Architecture Overview
1. **Workflow Engine** — built atop the async task queue layer.
2. **Role Graph Mapper** — identifies approvers dynamically based on RBAC and project/team graphs.
3. **State Machine** — moves requests through: `Draft → Pending → Approved → Rejected → Finalized`.
4. **Persistence Layer** — uses the internal event store with rollback and journaling.

## ⚙️ Key Components
- `approval_manager.py` — defines the workflow orchestration class.
- `approval_chain_table` — tracks approval states.
- `event_hooks/approval_hooks.py` — triggers system reactions post-approval.

## 🧪 Deliverables
- REST + GraphQL APIs for approval chains.
- UI integration for approval dashboards.
- Integration with audit and metrics subsystems.

## 🔒 Security & Compliance
- Signatures and timestamps recorded for all transitions.
- Enforced policy via SPEC‑009 (Security Middleware Redaction).

## 🧠 Dependencies
- SPEC‑009, SPEC‑010, SPEC‑014, SPEC‑025, SPEC‑040

## 🏁 Status
Planned – To be implemented after Phase 2B validation.
