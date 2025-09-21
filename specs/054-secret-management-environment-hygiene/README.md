# SPEC-054: Secret Management & Environment Hygiene

## Objective
Remove all secrets from version control and enforce secure secret management practices using environment variables and `.env` files.

## Motivation
Multiple secrets were found hardcoded in `docker-compose.yml` and committed via `mcp.json`. This poses a critical security risk.

## Implementation Plan
- [ ] Remove all live secrets from version control.
- [ ] Add `.env`, `.vscode/`, and secret config files to `.gitignore`.
- [ ] Refactor `docker-compose.yml` to reference environment variables.
- [ ] Use dotenv loaders for local development.
- [ ] Run Git history scan using `git-secrets` or `BFG` to remove past secret commits.

## Deliverables
- `.env.example` template
- Refactored `docker-compose.yml`
- Updated `.gitignore`
- Git cleanup instructions
