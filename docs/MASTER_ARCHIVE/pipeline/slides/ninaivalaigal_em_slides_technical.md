# Ninaivalaigal + eM — Technical Slides
## Responsibilities
- Persistent memory (multi-user, multi-team).
- Alignment agent (eM) injects correct context.
- Guardrails: provenance, redaction, time windows.
## Components
- FastAPI server + PostgreSQL backend.
- JWT auth, orgs/teams/roles.
- CLI (mem0), VS Code extension, shell hook.
## Architecture
```mermaid
flowchart LR
  User --> Tool
  Tool --> NV[Ninaivalaigal+eM]
  NV --> DB[(Postgres)]
```
## Sequence
```mermaid
sequenceDiagram
  User->>Tool: Ask AI
  Tool->>NV: Request context
  NV->>DB: Query memory
  DB-->>NV: Return data
  NV-->>Tool: Inject aligned memory
```
