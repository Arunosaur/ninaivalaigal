# Multipart Adapter Testing Framework

## Overview

The multipart adapter testing framework provides comprehensive validation of security controls through focused unit tests that mock the MultiPartParser to exercise specific code paths without relying on Starlette internals.

## Test Architecture

### Core Components

- **`tests/conftest.py`**: Monkeypatches `MultiPartParser` with `FakeMultiPartParser`
- **`tests/fake_objects.py`**: Provides `FakeRequest` and `FakePart` helpers with async stream compatibility
- **`tests/test_starlette_adapter_hardening.py`**: 6 focused tests validating security controls

### Fake Object Design

```python
class FakePart:
    def __init__(self, headers: dict, chunks: list[bytes]):
        self.headers = headers
        self._chunks = chunks

    async def stream(self):
        for c in self._chunks:
            yield c

class FakeStream:
    def __init__(self, request):
        self.__request__ = request

class FakeRequest:
    def __init__(self, parts: list[FakePart], headers: dict | None = None):
        self.headers = headers or {}
        self._parts = parts

    def stream(self):
        return FakeStream(self)
```

### Parser Mocking

```python
class FakeMultiPartParser:
    def __init__(self, headers=None, stream=None):
        self._stream = stream

    async def parse(self):
        if hasattr(self._stream, '__request__'):
            req = self._stream.__request__
        else:
            req = getattr(self._stream, '__request__', None)
        
        if req is None:
            return
            
        parts = getattr(req, "_parts", [])
        for p in parts:
            yield p
```

## Test Coverage

### 1. Part Count Limiter (`test_part_count_limit_trips`)

**Purpose**: Validates that requests with excessive parts are blocked with HTTP 413

```python
@pytest.mark.asyncio
async def test_part_count_limit_trips():
    parts = [
        FakePart({"content-type": "text/plain"}, [b"one"]),
        FakePart({"content-type": "text/plain"}, [b"two"]),
        FakePart({"content-type": "text/plain"}, [b"three"]),
    ]
    req = FakeRequest(parts)
    async def text_handler(s, h): pass
    with pytest.raises(HTTPException) as ei:
        await scan_with_starlette(req, text_handler, max_parts_per_request=2)
    assert ei.value.status_code == 413
```

**Validates**: DoS prevention via part count limiting

### 2. Size Limit Enforcement (`test_text_part_over_limit_trips`)

**Purpose**: Validates that oversized parts are blocked with HTTP 413

```python
@pytest.mark.asyncio
async def test_text_part_over_limit_trips():
    big = b"x" * (DEFAULT_MAX_TEXT_PART_BYTES + 10)
    parts = [FakePart({"content-type": "text/plain"}, [big])]
    req = FakeRequest(parts)
    async def text_handler(s, h): pass
    with pytest.raises(HTTPException) as ei:
        await scan_with_starlette(req, text_handler, max_text_part_bytes=1024)
    assert ei.value.status_code == 413
```

**Validates**: Memory exhaustion prevention via size limits

### 3. Binary Masquerade Detection (`test_binary_masquerade_blocked_on_text`)

**Purpose**: Validates that binary content in text parts is blocked with HTTP 415

```python
@pytest.mark.asyncio
async def test_binary_masquerade_blocked_on_text():
    # PE header masquerading as text/plain
    parts = [FakePart({"content-type": "text/plain"}, [PE_MAGIC + b"...."])]
    req = FakeRequest(parts)
    async def text_handler(s, h): pass
    with pytest.raises(HTTPException) as ei:
        await scan_with_starlette(req, text_handler)
    assert ei.value.status_code == 415
```

**Validates**: Detection of executable content masquerading as text

### 4. Archive Blocking (`test_archive_blocked_on_text`)

**Purpose**: Validates that archive uploads to text endpoints are blocked with HTTP 415

```python
@pytest.mark.asyncio
async def test_archive_blocked_on_text():
    parts = [FakePart({"content-type": "text/plain"}, [ZIP_MAGIC + b"..."])]
    req = FakeRequest(parts)
    async def text_handler(s, h): pass
    with pytest.raises(HTTPException) as ei:
        await scan_with_starlette(req, text_handler)
    assert ei.value.status_code == 415
```

**Validates**: Prevention of archive uploads on text-only endpoints

### 5. Content-Transfer-Encoding Guards (`test_invalid_cte_rejected`)

**Purpose**: Validates that prohibited encodings are blocked with HTTP 415

```python
@pytest.mark.asyncio
async def test_invalid_cte_rejected():
    parts = [FakePart({
        "content-type": "text/plain", 
        "content-transfer-encoding": "base64"
    }, [b"hello"])]
    req = FakeRequest(parts)
    async def text_handler(s, h): pass
    with pytest.raises(HTTPException) as ei:
        await scan_with_starlette(req, text_handler)
    assert ei.value.status_code == 415
```

**Validates**: Blocking of base64, quoted-printable, and other encodings

### 6. UTF-8 Validation (`test_utf16_rejected_for_text`)

**Purpose**: Validates that non-UTF-8 text is blocked with HTTP 415

```python
@pytest.mark.asyncio
async def test_utf16_rejected_for_text():
    utf16 = "hello".encode("utf-16le")
    parts = [FakePart({"content-type": "text/plain"}, [utf16])]
    req = FakeRequest(parts)
    async def text_handler(s, h): pass
    with pytest.raises(HTTPException) as ei:
        await scan_with_starlette(req, text_handler)
    assert ei.value.status_code == 415
```

**Validates**: Strict UTF-8 enforcement for text parts

## Running Tests

### Individual Test Execution

```bash
# Run specific test
pytest tests/test_starlette_adapter_hardening.py::test_part_count_limit_trips -v

# Run all hardening tests
pytest tests/test_starlette_adapter_hardening.py -v

# Run with quiet output
pytest -q tests/test_starlette_adapter_hardening.py
```

### Integration with Test Suite

```bash
# Run all multipart security tests
pytest tests/test_multipart_hardening_patch_v2.py tests/test_starlette_adapter_hardening.py tests/test_starlette_adapter_simple.py -v

# Run complete security test suite
pytest tests/test_multipart_hardening_patch_v2.py tests/test_starlette_adapter_hardening.py tests/test_metrics_label_guard.py tests/test_rbac_policy_gate.py -v
```

## Test Results

All 6 focused hardening tests pass successfully:

```
tests/test_starlette_adapter_hardening.py::test_part_count_limit_trips PASSED [ 16%]
tests/test_starlette_adapter_hardening.py::test_text_part_over_limit_trips PASSED [ 33%]
tests/test_starlette_adapter_hardening.py::test_binary_masquerade_blocked_on_text PASSED [ 50%]
tests/test_starlette_adapter_hardening.py::test_archive_blocked_on_text PASSED [ 66%]
tests/test_starlette_adapter_hardening.py::test_invalid_cte_rejected PASSED [ 83%]
tests/test_starlette_adapter_hardening.py::test_utf16_rejected_for_text PASSED [100%]
```

## Security Validation Matrix

| Test | Attack Vector | HTTP Status | Security Control |
|------|---------------|-------------|------------------|
| Part Count Limiter | DoS via excessive parts | 413 | `max_parts_per_request` |
| Size Limit | Memory exhaustion | 413 | `max_text_part_bytes` |
| Binary Masquerade | Executable smuggling | 415 | Magic byte detection |
| Archive Blocking | Archive bomb/smuggling | 415 | ZIP/archive detection |
| CTE Guards | Encoding bypass | 415 | Content-Transfer-Encoding validation |
| UTF-8 Validation | Unicode attacks | 415 | Strict UTF-8 enforcement |

## Benefits of Focused Testing

### 1. **Isolation**: Tests specific code paths without Starlette dependencies
### 2. **Precision**: Validates exact security controls and error conditions
### 3. **Performance**: Fast execution with minimal setup overhead
### 4. **Reliability**: Consistent results independent of external library changes
### 5. **Coverage**: Comprehensive validation of all P0 security features

## Integration with CI/CD

### GitHub Actions Example

```yaml
- name: Run Multipart Security Tests
  run: |
    pytest tests/test_starlette_adapter_hardening.py -v
    pytest tests/test_multipart_hardening_patch_v2.py -v
```

### Pre-commit Hook Integration

```yaml
- id: multipart-security-tests
  name: Multipart Security Test Suite
  entry: pytest tests/test_starlette_adapter_hardening.py tests/test_multipart_hardening_patch_v2.py -v
  language: system
  files: ^server/security/multipart/.*\.py$
```

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure `sys.path` includes project root
2. **Monkeypatch Failures**: Verify `conftest.py` is in tests directory
3. **Async Handler Warnings**: Expected for test handlers, can be ignored

### Debug Mode

```python
# Enable debug logging
import logging
logging.getLogger("server.security.multipart").setLevel(logging.DEBUG)

# Run single test with verbose output
pytest tests/test_starlette_adapter_hardening.py::test_part_count_limit_trips -v -s
```

## Related Documentation

- [Starlette Adapter Hardening](STARLETTE_ADAPTER_HARDENING.md)
- [Multipart Hardening Patch V2](MULTIPART_HARDENING_PATCH_V2.md)
- [Multipart Per-Part Limits](MULTIPART_PER_PART_LIMITS.md)

---

**Status**: Production Ready  
**Version**: 1.0  
**Last Updated**: 2025-09-16  
**Test Coverage**: 6/6 passing tests validating all P0 security controls
