# Script Portability Guide

## Overview

All auth testing scripts are designed to be **portable** - they work on:
- ✅ **macOS (BSD)** - Local development
- ✅ **Linux (GNU)** - Container/CI environments

## Key Design Decisions

### POSIX-Compliant Commands

We use standard POSIX commands that work across all Unix-like systems:

| Command | Why Portable | Alternative (Not Used) |
|---------|--------------|------------------------|
| `sed '$d'` | POSIX standard, works on BSD/GNU | `head -n -1` (GNU only) |
| `tail -n 1` | Universal standard | `tail -1` (deprecated) |
| `date +%s` | Widely supported | Platform-specific time commands |
| `curl -w` | Standard curl feature | wget (not always available) |

### Example: Why `sed '$d'` Instead of `head -n -1`

```bash
# ❌ GNU-only (fails on macOS)
head -n -1 file.txt

# ✅ Portable (works everywhere)
sed '$d' file.txt
```

## Testing Portability

### On macOS (Local)
```bash
./scripts/test_portability.sh
```

### In Linux Container
```bash
# Test in running container
container exec ninaivalaigal-dev-core-api bash /app/scripts/test_portability.sh

# Or build a test container
docker run --rm -v $(pwd):/app alpine:latest sh -c "apk add bash curl && /app/scripts/test_portability.sh"
```

## Scripts Affected

All these scripts are now portable:

- ✅ `scripts/debug_auth_tests.sh` - Main auth diagnostic script
- ✅ `scripts/test_portability.sh` - Portability validation
- ✅ Any future test scripts using similar patterns

## Benefits

### 1. **Local Development**
Run tests on your Mac without containers:
```bash
conda activate nina
python services/core-api/local_run.py
./scripts/debug_auth_tests.sh
```

### 2. **Container Testing**
Same scripts work inside containers:
```bash
docker exec -it ninaivalaigal-dev-core-api bash
./scripts/debug_auth_tests.sh
```

### 3. **CI/CD**
GitHub Actions can use the same scripts:
```yaml
- name: Run Auth Tests
  run: |
    ./scripts/debug_auth_tests.sh
```

## Common Pitfalls Avoided

| Pitfall | Why It Breaks | Our Solution |
|---------|---------------|--------------|
| `head -n -1` | BSD `head` doesn't support negative offsets | Use `sed '$d'` |
| `echo -e` | Not POSIX standard | Use printf or plain echo |
| `[[` conditionals | Bashism, not POSIX | Use `[` for portability |
| GNU-specific flags | Fail on BSD systems | Use POSIX subset |

## Validation

Before committing new scripts:

```bash
# 1. Test on macOS
./scripts/test_portability.sh

# 2. Test in Alpine (minimal Linux)
docker run --rm -v $(pwd):/app alpine:latest sh -c "apk add bash && /app/scripts/test_portability.sh"

# 3. Test in Ubuntu (common CI)
docker run --rm -v $(pwd):/app ubuntu:latest bash /app/scripts/test_portability.sh
```

## References

- [POSIX Shell Command Language](https://pubs.opengroup.org/onlinepubs/9699919799/utilities/V3_chap02.html)
- [Portable Shell Programming](https://www.gnu.org/software/autoconf/manual/autoconf.html#Portable-Shell)
- [BSD vs GNU Differences](https://ponderthebits.com/2017/01/know-your-tools-linux-gnu-vs-mac-bsd-command-line-utilities-grep-strings-sed-and-find/)

## Summary

**All testing scripts work in both environments** - no need for separate macOS and Linux versions! 🎉

When adding new scripts, follow these patterns and they'll work everywhere.
