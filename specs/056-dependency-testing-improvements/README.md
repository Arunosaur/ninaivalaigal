# SPEC-056: Dependency & Testing Improvements

## Objective
Ensure clean dependency management and strengthen testing practices with mocks and fixtures.

## Issues Found
- Conflicts between `requirements.txt` and `requirements-dev.txt`
- Heavy integration tests starting real services

## Plan
- [ ] Consolidate and lock package versions.
- [ ] Add `pip-tools` or `poetry` for reproducible installs.
- [ ] Replace live integration tests with mocks for services like Redis, DB, Auth.
- [ ] Use fixtures for test setup and teardown.

## Deliverables
- Unified `requirements/` directory or toolchain
- Updated test suite with mocks and fixtures
- Improved Makefile targets
