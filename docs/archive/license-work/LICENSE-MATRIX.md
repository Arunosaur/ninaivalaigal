# Ninaivalaigal Open-Core Licensing Matrix

| Directory / Component | Description | License | Visibility |
|------------------------|-------------|----------|-------------|
| `/frontend-nextjs-customer/` | Public UI for individuals and teams | MIT | Public |
| `/frontend-nextjs-admin/` | Internal admin console (without analytics) | MIT | Public |
| `/cli/` | e^M CLI + VS Code extension | Apache 2.0 | Public |
| `/sdk/` | Developer SDKs | Apache 2.0 | Public |
| `/server/api/public_routes/` | Public API surface | Apache 2.0 | Public |
| `/server/api/internal_routes/` | Internal admin & system APIs | Proprietary | Private |
| `/server/memory_core/` | Core e^M algorithms, token ranking, decay logic | Proprietary | Private |
| `/server/graph/` | Apache AGE / pgvector fusion, graph reasoning | Proprietary | Private |
| `/server/feedback/` | Adaptive learning & scoring engine | Proprietary | Private |
| `/server/monetization/` | Stripe, billing, usage tracking | Proprietary | Private |
| `/server/auth/` | OAuth, RBAC, encryption | Proprietary | Private |
| `/infra/docker/` | Dockerfiles, Apple Container CLI stacks | Elastic License 2.0 | Source-available |
| `/infra/terraform/` | IaC templates (no secrets) | Elastic License 2.0 | Source-available |
| `/scripts/` | Generic health & start/stop scripts | MIT | Public |
| `/specs/core/` | Foundation specs (000–020) | CC BY-NC 4.0 | Public |
| `/specs/advanced/` | Graph, Feedback, Monetization | Proprietary | Private |
