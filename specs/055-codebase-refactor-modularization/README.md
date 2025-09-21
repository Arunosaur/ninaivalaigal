# SPEC-055: Codebase Refactor & Modularization

## Objective
Split monolithic files into smaller, domain-specific modules to improve maintainability, testing, and collaboration.

## Files to Refactor
- `main.py` (1051 lines)
- `database.py` (955 lines)
- `mcp_server.py` (880 lines)

## Modularization Plan
- [ ] Create `routes/`, `services/`, `models/`, and `utils/` directories.
- [ ] Move domain-specific logic to respective modules.
- [ ] Update imports and references.
- [ ] Document module responsibilities in README.

## Deliverables
- Refactored directory structure
- Updated test paths and imports
- Internal documentation per module
