# SPEC-057: Microservice & Config Architecture

## Objective
Restructure the codebase to support microservice isolation and unified configuration management.

## Tasks
- [ ] Extract MCP logic into a service (if not already)
- [ ] Create central `config.py` using environment-based settings
- [ ] Use Pydantic or similar for config validation
- [ ] Add service-specific env loading and config separation

## Deliverables
- Standalone MCP service entrypoint
- Centralized config loading with fallbacks
- Diagram of service relationships
