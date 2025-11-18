# Multi-Language Test Coverage Guide

**Date**: January 2025
**Purpose**: Comprehensive guide for ensuring test coverage across Python, TypeScript/JavaScript, Rust, and Go

---

## 🎯 Overview

This project uses multiple programming languages:
- **Python**: Main backend (`server/`, `services/`)
- **TypeScript/JavaScript**: Frontend applications (`frontend-nextjs-customer/`, `frontend-shared/`)
- **Rust**: High-performance services (`rust-services/graphops/`, `rust-services/memory-service/`)
- **Go**: gRPC gateway and CLI tools (`go-services/`)

Each language has its own test framework and conventions. This guide explains how to ensure comprehensive test coverage across all languages.

---

## 📋 Test Framework Summary

| Language | Test Framework | Coverage Tool | Threshold | Test File Pattern |
|----------|----------------|---------------|------------|-------------------|
| **Python** | pytest | pytest-cov | 85% overall | `tests/test_<name>.py` |
| **TypeScript/JS** | Jest/Vitest | @vitest/coverage-v8 | 80% | `<dir>/__tests__/<name>.test.ts` |
| **Rust** | Built-in | cargo-tarpaulin | 80% | `tests/<name>_test.rs` or inline |
| **Go** | Built-in | go test -cover | 80% | `<name>_test.go` (same directory) |

---

## 🔧 Current Test Infrastructure

### **1. Python (Backend)**

**Test Framework**: pytest
**Coverage Tool**: pytest-cov, coverage.py
**Configuration**: `pytest.ini`, `pyproject.toml`

**Test Locations**:
- `tests/unit/` - Unit tests
- `tests/integration/` - Integration tests
- `tests/functional/` - Functional tests
- `tests/intelligence/` - Intelligence layer tests

**Running Tests**:
```bash
# All tests
make test-all

# With coverage
make test-coverage

# Specific suite
pytest tests/unit/ -v --cov=server --cov-report=html
```

**CI/CD**: ✅ Runs in `.github/workflows/comprehensive-test-validation.yml`

**Pre-Commit**: ✅ Checks new Python files have tests

---

### **2. TypeScript/JavaScript (Frontend)**

**Test Frameworks**:
- **Jest**: Legacy frontend (`frontend/`)
- **Vitest**: Modern Next.js apps (`frontend-nextjs-customer/`, `frontend-shared/`)

**Coverage Tool**: `@vitest/coverage-v8` (Vitest), `jest --coverage` (Jest)

**Test Locations**:
- `<component-dir>/__tests__/<name>.test.tsx`
- `<component-dir>/<name>.test.tsx`
- `tests/unit/<name>.test.ts`
- `tests/integration/<name>.test.tsx`
- `tests/e2e/<name>.spec.ts` (Playwright)

**Running Tests**:

**Next.js Customer App**:
```bash
cd frontend-nextjs-customer

# Unit tests
npm run test

# With coverage
npm run test:coverage

# E2E tests
npm run test:e2e
```

**Legacy Frontend**:
```bash
cd frontend

# Unit tests
npm run test

# With coverage
npm run test:coverage
```

**CI/CD**: ✅ Runs in `.github/workflows/frontend-nextjs-customer-ci.yml`

**Pre-Commit**: ✅ Checks new TypeScript files have tests (NEW)

---

### **3. Rust**

**Test Framework**: Built-in (`cargo test`)
**Coverage Tool**: `cargo-tarpaulin`, `cargo-llvm-cov`

**Test Locations**:
- `tests/<name>_test.rs` - Integration tests
- `tests/<name>.rs` - Integration tests (alternative)
- Inline `#[cfg(test)]` modules in source files

**Running Tests**:

**GraphOps Service**:
```bash
cd rust-services/graphops

# All tests
cargo test

# With coverage (requires cargo-tarpaulin)
cargo tarpaulin --out Html

# Specific test
cargo test test_name
```

**Memory Service**:
```bash
cd rust-services/memory-service

# All tests
cargo test

# Benchmarks
cargo bench
```

**CI/CD**: ⚠️ Partially - Runs `cargo test` in `.github/workflows/ci-lint.yml`
**Coverage**: ⚠️ Not yet enforced in CI

**Pre-Commit**: ✅ Runs `cargo test --lib` (formatting/linting only, not coverage)

---

### **4. Go**

**Test Framework**: Built-in (`go test`)
**Coverage Tool**: `go test -cover`, `gocov`

**Test Locations**:
- `<name>_test.go` in same directory as source

**Running Tests**:

**CLI Tools**:
```bash
cd go-services/cli-tools

# All tests
make test

# With coverage
make test-coverage

# Or directly
go test -v -coverprofile=coverage.out ./...
go tool cover -html=coverage.out -o coverage.html
```

**gRPC Gateway**:
```bash
cd go-services/grpc-gateway

# All tests
go test -v ./...

# With coverage
go test -v -coverprofile=coverage.out ./...
```

**Load Tester**:
```bash
cd go-services/load-tester

# All tests
go test -v ./...
```

**CI/CD**: ⚠️ Not yet configured (linting only)
**Coverage**: ⚠️ Not yet enforced in CI

**Pre-Commit**: ✅ Runs `go vet` and `golangci-lint` (formatting/linting only, not coverage)

---

## 🚀 Enhanced Test Coverage Checking

### **New Multi-Language Test Checker**

Created `scripts/check_multi_lang_test_coverage.py` to check test coverage across all languages.

**Features**:
- ✅ Detects language from file extension
- ✅ Finds test files using language-specific patterns
- ✅ Checks new files have tests (pre-commit)
- ✅ Analyzes existing code coverage
- ✅ Supports Python, TypeScript, Rust, Go

**Usage**:

```bash
# Check new files have tests
python scripts/check_multi_lang_test_coverage.py --check-new-files

# Analyze coverage for existing code
python scripts/check_multi_lang_test_coverage.py --analyze-coverage

# Check specific language
python scripts/check_multi_lang_test_coverage.py --analyze-coverage --language python
python scripts/check_multi_lang_test_coverage.py --analyze-coverage --language typescript
python scripts/check_multi_lang_test_coverage.py --analyze-coverage --language rust
python scripts/check_multi_lang_test_coverage.py --analyze-coverage --language go

# Check specific file
python scripts/check_multi_lang_test_coverage.py --file server/new_module.py
python scripts/check_multi_lang_test_coverage.py --file frontend-nextjs-customer/components/NewComponent.tsx
```

---

## 🔍 Test File Conventions

### **Python**

**Source**: `server/module/file.py`
**Test**: `tests/test_file.py` or `tests/module/test_file.py`

**Example**:
```python
# server/memory/engine.py
class MemoryEngine:
    def create_memory(self, content: str):
        ...

# tests/test_memory_engine.py
def test_create_memory():
    engine = MemoryEngine()
    result = engine.create_memory("test")
    assert result is not None
```

---

### **TypeScript/JavaScript**

**Source**: `components/LoginForm.tsx`
**Test**: `components/__tests__/LoginForm.test.tsx` or `components/LoginForm.test.tsx`

**Example**:
```typescript
// components/LoginForm.tsx
export function LoginForm() {
  // ...
}

// components/__tests__/LoginForm.test.tsx
import { render, screen } from '@testing-library/react';
import { LoginForm } from '../LoginForm';

test('renders login form', () => {
  render(<LoginForm />);
  expect(screen.getByRole('form')).toBeInTheDocument();
});
```

---

### **Rust**

**Source**: `src/handlers/cypher.rs`
**Test**: `tests/cypher_test.rs` or inline `#[cfg(test)]` module

**Example**:
```rust
// src/handlers/cypher.rs
pub fn execute_query(query: &str) -> Result<String> {
    // ...
}

// tests/cypher_test.rs
#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_execute_query() {
        let result = execute_query("MATCH (n) RETURN n");
        assert!(result.is_ok());
    }
}
```

---

### **Go**

**Source**: `config.go`
**Test**: `config_test.go` (same directory)

**Example**:
```go
// config.go
package main

func LoadConfig() (*Config, error) {
    // ...
}

// config_test.go
package main

import "testing"

func TestLoadConfig(t *testing.T) {
    config, err := LoadConfig()
    if err != nil {
        t.Fatalf("LoadConfig() error = %v", err)
    }
    if config == nil {
        t.Fatal("LoadConfig() returned nil config")
    }
}
```

---

## ✅ Pre-Commit Hooks

Updated `.pre-commit-config.yaml` to check tests for all languages:

1. **Python**: `check-new-files-have-tests` - Python files only
2. **Multi-Language**: `check-multi-lang-tests` - Python, Rust, Go
3. **TypeScript**: `check-typescript-tests` - TypeScript/JavaScript files

**How It Works**:
- Runs automatically on `git commit`
- Checks newly staged files (added, not modified)
- Blocks commit if test file missing
- Provides guidance on expected test file location

---

## 📊 CI/CD Integration

### **Current Status**:

| Language | Tests Run | Coverage Enforced | Quality Gates |
|----------|-----------|-------------------|---------------|
| **Python** | ✅ Yes | ✅ Yes (85%) | ✅ Yes |
| **TypeScript/JS** | ✅ Yes | ✅ Yes (80%) | ✅ Yes |
| **Rust** | ⚠️ Partial | ❌ No | ⚠️ Partial |
| **Go** | ❌ No | ❌ No | ⚠️ Partial |

### **Recommendations**:

#### **1. Enhance Rust CI/CD**

Add to `.github/workflows/rust-tests.yml`:
```yaml
name: Rust Tests & Coverage

on:
  pull_request:
    paths:
      - 'rust-services/**'
  push:
    branches: [main, master]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install Rust toolchain
        uses: actions-rs/toolchain@v1
        with:
          toolchain: stable
          override: true

      - name: Run tests
        run: |
          cd rust-services/graphops
          cargo test --all-targets
          cd ../memory-service
          cargo test --all-targets

      - name: Generate coverage
        uses: actions-rs/tarpaulin@v0.1
        with:
          args: '--out Html --output-dir coverage'

      - name: Upload coverage
        uses: actions/upload-artifact@v4
        with:
          name: rust-coverage
          path: coverage/
```

#### **2. Enhance Go CI/CD**

Add to `.github/workflows/go-tests.yml`:
```yaml
name: Go Tests & Coverage

on:
  pull_request:
    paths:
      - 'go-services/**'
  push:
    branches: [main, master]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Go
        uses: actions/setup-go@v5
        with:
          go-version: '1.21'

      - name: Run tests
        run: |
          cd go-services/cli-tools
          go test -v -coverprofile=coverage.out ./...
          go tool cover -html=coverage.out -o coverage.html

          cd ../grpc-gateway
          go test -v -coverprofile=coverage.out ./...
          go tool cover -html=coverage.out -o coverage.html

          cd ../load-tester
          go test -v -coverprofile=coverage.out ./...
          go tool cover -html=coverage.out -o coverage.html

      - name: Upload coverage
        uses: actions/upload-artifact@v4
        with:
          name: go-coverage
          path: go-services/**/coverage.html
```

---

## 📈 Coverage Analysis

### **How to Analyze Coverage**

```bash
# Python
python scripts/check_multi_lang_test_coverage.py --analyze-coverage --language python

# TypeScript
python scripts/check_multi_lang_test_coverage.py --analyze-coverage --language typescript

# Rust
python scripts/check_multi_lang_test_coverage.py --analyze-coverage --language rust

# Go
python scripts/check_multi_lang_test_coverage.py --analyze-coverage --language go

# All languages
python scripts/check_multi_lang_test_coverage.py --analyze-coverage
```

### **Expected Output**:

```
📊 Test Coverage Analysis

============================================================

PYTHON:
  Total files: 245
  Files with tests: 198
  Files without tests: 47
  Coverage: 80.8%

  ⚠️  Files without tests (showing first 10):
    - server/admin_analytics_api.py
    - server/billing_console_api.py
    ...

TYPESCRIPT:
  Total files: 89
  Files with tests: 67
  Files without tests: 22
  Coverage: 75.3%

RUST:
  Total files: 34
  Files with tests: 28
  Files without tests: 6
  Coverage: 82.4%

GO:
  Total files: 18
  Files with tests: 15
  Files without tests: 3
  Coverage: 83.3%

============================================================
```

---

## ✅ Best Practices

### **For All Languages**:

1. **Write Tests Alongside Code**:
   - Create test file when creating source file
   - Pre-commit hooks will remind you if forgotten

2. **Follow Language Conventions**:
   - Python: `tests/test_*.py`
   - TypeScript: `__tests__/*.test.tsx`
   - Rust: `tests/*_test.rs` or inline
   - Go: `*_test.go` in same directory

3. **Aim for High Coverage**:
   - Python: 85%+ overall
   - TypeScript: 80%+ overall
   - Rust: 80%+ overall
   - Go: 80%+ overall

4. **Run Tests Before Committing**:
   - Python: `make test-unit`
   - TypeScript: `npm run test`
   - Rust: `cargo test`
   - Go: `go test ./...`

---

## 🎯 Summary

### **Current State**:

✅ **Python**: Comprehensive test infrastructure with CI/CD and pre-commit
✅ **TypeScript**: Test infrastructure with CI/CD, pre-commit added
⚠️ **Rust**: Tests run but coverage not enforced
⚠️ **Go**: Tests run locally but not in CI/CD

### **Enhancements Added**:

✅ Multi-language test checker script
✅ Pre-commit hooks for all languages
✅ Coverage analysis tool
📋 CI/CD recommendations for Rust and Go

### **Next Steps**:

1. ✅ Use multi-language checker in pre-commit (DONE)
2. 🔧 Add Rust coverage to CI/CD
3. 🔧 Add Go coverage to CI/CD
4. 📊 Monitor coverage trends across all languages
5. 🎯 Set coverage thresholds for Rust and Go in CI

---

**Last Updated**: January 2025
**Status**: ✅ Multi-language test checking implemented, CI/CD enhancements recommended




