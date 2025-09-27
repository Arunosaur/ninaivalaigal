"""
Foundation SPEC Tests

This package contains comprehensive test suites for all 7 Foundation SPECs:

- SPEC-007: Unified Context Scope System
- SPEC-012: Memory Substrate  
- SPEC-016: CI/CD Pipeline Architecture
- SPEC-020: Memory Provider Architecture
- SPEC-049: Memory Sharing Collaboration
- SPEC-052: Comprehensive Test Coverage
- SPEC-058: Documentation Expansion

Each SPEC has its own subdirectory with focused test modules covering:
- Core functionality validation
- Edge case testing
- Performance benchmarking
- Integration testing
- Chaos/failure scenario testing

Usage:
    pytest tests/foundation/                    # Run all foundation tests
    pytest tests/foundation/spec_007/           # Run SPEC-007 tests only
    pytest tests/foundation/ -k "sharing"       # Run sharing-related tests
    pytest tests/foundation/ --cov=server       # Run with coverage
"""

__version__ = "1.0.0"
__author__ = "Ninaivalaigal Foundation Test Team"

# Test configuration
FOUNDATION_SPECS = [
    "SPEC-007",
    "SPEC-012", 
    "SPEC-016",
    "SPEC-020",
    "SPEC-049",
    "SPEC-052",
    "SPEC-058"
]

COVERAGE_TARGETS = {
    "SPEC-007": 95.0,
    "SPEC-012": 90.0,
    "SPEC-016": 95.0,
    "SPEC-020": 95.0,
    "SPEC-049": 95.0,
    "SPEC-052": 90.0,
    "SPEC-058": 95.0
}

# Test markers for pytest
pytest_markers = [
    "foundation: Foundation SPEC tests",
    "scope: Context scope system tests",
    "substrate: Memory substrate tests", 
    "cicd: CI/CD pipeline tests",
    "provider: Memory provider tests",
    "sharing: Memory sharing tests",
    "coverage: Test coverage validation",
    "documentation: Documentation tests"
]
