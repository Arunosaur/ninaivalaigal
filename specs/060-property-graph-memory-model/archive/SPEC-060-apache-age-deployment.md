# SPEC-060: Apache AGE Dual Architecture Deployment

## Objective
Deploy Apache AGE with support for both local Apple Silicon and CI environments for x86_64, enabling advanced property graph capabilities in our memory system.

## Architecture Overview
- **Local (Apple Container)**: Leverage Apple Container CLI to run PostgreSQL + Apache AGE natively on ARM64.
- **CI/CD (x86_64)**: Use GitHub-hosted runners or Docker x86 emulation for building/testing.

## Key Components
- PostgreSQL 13+
- Apache AGE extension
- Docker multi-arch setup (arm64, amd64)
- Graph initialization scripts

## Setup Plan
1. Build multi-arch Docker image with AGE + Postgres
2. Configure container to load `age` extension
3. Verify graph creation and Cypher support on both platforms

## Deliverables
- Multi-arch Dockerfile
- Apple Container CLI config for local use
- `init.sql` to create initial graph
- Compatibility matrix (Apple M1/Intel CI)
