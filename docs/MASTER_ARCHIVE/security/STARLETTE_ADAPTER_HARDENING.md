# Starlette Multipart Adapter Hardening

## Overview

The hardened Starlette multipart adapter provides comprehensive security enhancements for processing multipart uploads in FastAPI/Starlette applications. This implementation includes P0 security fixes identified in external security reviews.

## Features

### Core Security Enhancements

- **Part Count DoS Prevention**: Configurable limit on parts per request (default: 256)
- **Stream-time Size Enforcement**: Early abort during streaming to prevent memory exhaustion
- **Binary Masquerade Detection**: Identifies binary content masquerading as text
- **Archive Blocking**: Prevents ZIP/archive uploads to text-only endpoints
- **UTF-8 Enforcement**: Strict UTF-8 validation for text parts
- **Content-Transfer-Encoding Guards**: Blocks base64, quoted-printable, and other encodings
- **Magic Byte Detection**: Enhanced detection including Mach-O, Java class, MP4 offset-aware scanning

### HTTP Exception Mapping

- **413 Request Entity Too Large**: Part size exceeded, too many parts
- **415 Unsupported Media Type**: Invalid encoding, archive blocked, binary masquerade
- **400 Bad Request**: Malformed multipart stream

### Metrics Integration

Bounded reason buckets for monitoring:
- `engine_error`: Parser or stream processing errors
- `policy_denied`: Policy violation (reserved)
- `magic_mismatch`: Binary content in text part
- `part_too_large`: Size limit exceeded
- `too_many_parts`: Part count limit exceeded
- `invalid_encoding`: UTF-8 or CTE validation failure
- `archive_blocked`: Archive detected on text endpoint

## Usage

### Basic Usage

```python
from server.security.multipart.starlette_adapter import scan_with_starlette
from starlette.requests import Request

async def handle_upload(request: Request):
    texts = []
    binaries = []

    def text_handler(content: str, headers: dict):
        texts.append({"content": content, "headers": headers})

    def binary_handler(content: bytes, headers: dict):
        binaries.append({"content": content, "headers": headers})

    await scan_with_starlette(
        request,
        text_handler,
        binary_handler,
        max_text_part_bytes=1024*1024,    # 1MB text limit
        max_binary_part_bytes=10*1024*1024, # 10MB binary limit
        max_parts_per_request=100         # 100 parts max
    )

    return {"texts": len(texts), "binaries": len(binaries)}
```

### Custom Configuration

```python
await scan_with_starlette(
    request,
    text_handler,
    binary_handler,
    max_text_part_bytes=512*1024,      # 512KB for text-only endpoints
    max_binary_part_bytes=50*1024*1024, # 50MB for file uploads
    max_parts_per_request=10           # Strict limit for sensitive endpoints
)
```

### Text-Only Endpoints

```python
# For text-only endpoints, omit binary_handler
await scan_with_starlette(
    request,
    text_handler,
    max_text_part_bytes=256*1024,  # 256KB limit
    max_parts_per_request=5        # Very restrictive
)
```

## Security Validations

### 1. Part Count Limiting

```python
# Blocks requests with excessive parts
if part_count > max_parts_per_request:
    raise HTTPException(413, "too many multipart parts")
```

### 2. Size Enforcement

```python
# Stream-time size checking with early abort
total_size = 0
async for chunk in part.stream():
    total_size += len(chunk)
    if total_size > size_limit:
        raise HTTPException(413, "multipart part exceeds size limit")
```

### 3. Archive Detection

```python
# Detect and block archives on text endpoints
magic_result = detect_enhanced_magic_bytes(content)
if is_text_endpoint and "zip" in magic_result.get("mime_type", ""):
    raise HTTPException(415, "archive payload not allowed for text endpoints")
```

### 4. Binary Masquerade Detection

```python
# Detect binary content in text parts
if is_text_part and looks_binary(content):
    raise HTTPException(415, "content-type mismatch: binary payload in text part")
```

### 5. UTF-8 Validation

```python
# Strict UTF-8 enforcement for text parts
utf8_result = require_utf8_text(content)
if not utf8_result.get("valid"):
    raise HTTPException(415, "text parts must be UTF-8")
```

### 6. Content-Transfer-Encoding Guards

```python
# Block prohibited encodings
cte_result = reject_content_transfer_encoding(cte_header)
if not cte_result.get("valid"):
    raise HTTPException(415, "unsupported Content-Transfer-Encoding for text part")
```

## Testing

### Running Tests

```bash
# Run adapter-specific tests
python -m pytest tests/test_starlette_adapter_simple.py -v

# Run comprehensive multipart security tests
python -m pytest tests/test_multipart_hardening_patch_v2.py -v

# Run all security tests
python -m pytest tests/test_multipart_hardening_patch_v2.py tests/test_starlette_adapter_simple.py tests/test_metrics_label_guard.py -v
```

### Test Coverage

The test suite covers:
- **Part count limiting**: Blocks excessive parts (>256)
- **Size limiting**: Blocks oversized parts (>1MB text, >10MB binary)
- **Text processing**: UTF-8 validation and handler integration
- **Binary processing**: Binary content detection and routing
- **Custom limits**: Configurable thresholds and validation
- **Error handling**: Proper HTTPException mapping

## Integration Examples

### FastAPI Route

```python
from fastapi import FastAPI, Request, HTTPException
from server.security.multipart.starlette_adapter import scan_with_starlette

app = FastAPI()

@app.post("/upload")
async def upload_files(request: Request):
    if not request.headers.get("content-type", "").startswith("multipart/"):
        raise HTTPException(400, "Expected multipart request")

    processed_parts = []

    def handle_text(content: str, headers: dict):
        processed_parts.append({
            "type": "text",
            "content": content[:100] + "..." if len(content) > 100 else content,
            "size": len(content.encode('utf-8'))
        })

    def handle_binary(content: bytes, headers: dict):
        processed_parts.append({
            "type": "binary",
            "content_type": headers.get("content-type", "unknown"),
            "size": len(content)
        })

    try:
        await scan_with_starlette(request, handle_text, handle_binary)
        return {"status": "success", "parts": processed_parts}
    except HTTPException as e:
        # Log security violation
        logger.warning(f"Multipart security violation: {e.detail}")
        raise
```

### Middleware Integration

```python
from starlette.middleware.base import BaseHTTPMiddleware

class MultipartSecurityMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        if request.method in ["POST", "PUT", "PATCH"]:
            content_type = request.headers.get("content-type", "")
            if content_type.startswith("multipart/"):
                # Pre-validate multipart structure
                try:
                    await self.validate_multipart(request)
                except HTTPException:
                    # Block malicious requests early
                    return Response("Multipart validation failed", status_code=400)

        return await call_next(request)
```

## Performance Considerations

### Memory Usage

- **Stream Processing**: Parts are processed as streams, not loaded entirely into memory
- **Early Abort**: Size limits enforced during streaming to prevent memory exhaustion
- **Bounded Buffers**: Magic byte detection uses limited scan windows (32 bytes for MP4)

### CPU Usage

- **Efficient Magic Byte Scanning**: Limited to first 512 bytes for most signatures
- **UTF-8 Validation**: Optimized for common cases with BOM detection
- **Regex-Free**: Content-Transfer-Encoding detection uses simple string matching

## Security Impact

### Attack Vectors Mitigated

1. **DoS via Part Count**: Prevents requests with thousands of parts
2. **Memory Exhaustion**: Stream-time size limits prevent OOM attacks
3. **Binary Smuggling**: Detects executables and archives in text parts
4. **Encoding Bypasses**: Blocks base64 and other encoding schemes
5. **Archive Bombs**: Prevents ZIP uploads to text endpoints
6. **Unicode Attacks**: Strict UTF-8 validation with BOM handling

### Compliance Benefits

- **Input Validation**: Comprehensive multipart content validation
- **Data Integrity**: Ensures uploaded content matches declared types
- **Audit Trail**: Detailed rejection reasons for security monitoring
- **Resource Protection**: Prevents resource exhaustion attacks

## Configuration Recommendations

### Production Defaults

```python
# Conservative settings for production
PRODUCTION_LIMITS = {
    "max_text_part_bytes": 1 * 1024 * 1024,    # 1MB
    "max_binary_part_bytes": 10 * 1024 * 1024,  # 10MB
    "max_parts_per_request": 256                # 256 parts
}
```

### Text-Only Services

```python
# Strict settings for text-only APIs
TEXT_ONLY_LIMITS = {
    "max_text_part_bytes": 256 * 1024,  # 256KB
    "max_binary_part_bytes": 0,         # No binary allowed
    "max_parts_per_request": 10         # Very restrictive
}
```

### File Upload Services

```python
# Generous settings for file uploads
FILE_UPLOAD_LIMITS = {
    "max_text_part_bytes": 1 * 1024 * 1024,    # 1MB metadata
    "max_binary_part_bytes": 100 * 1024 * 1024, # 100MB files
    "max_parts_per_request": 50                 # Multiple files
}
```

## Monitoring and Alerting

### Metrics to Track

```python
# Example metrics integration
def _emit_multipart_reject(reason: str) -> None:
    metrics.counter("multipart_reject_total", tags={"reason": reason}).increment()

    # Alert on suspicious patterns
    if reason in ["too_many_parts", "part_too_large"]:
        logger.warning(f"Potential DoS attempt: {reason}")
```

### Recommended Alerts

- **High rejection rate**: >5% of requests rejected
- **Part count attacks**: Multiple `too_many_parts` rejections
- **Size attacks**: Frequent `part_too_large` rejections
- **Binary smuggling**: `magic_mismatch` or `archive_blocked` events

## Troubleshooting

### Common Issues

1. **413 Errors on Valid Uploads**
   - Check part size limits vs actual content
   - Verify text vs binary classification
   - Review custom limit configuration

2. **415 Errors on Text Content**
   - Ensure content is valid UTF-8
   - Check for prohibited Content-Transfer-Encoding headers
   - Verify no binary signatures in text parts

3. **400 Errors on Multipart Parsing**
   - Validate multipart boundary format
   - Check for malformed headers
   - Ensure proper Content-Type header

### Debug Mode

```python
# Enable verbose logging for debugging
import logging
logging.getLogger("server.security.multipart").setLevel(logging.DEBUG)

# Test with minimal limits
await scan_with_starlette(
    request,
    text_handler,
    max_text_part_bytes=10*1024*1024,    # Large limits for testing
    max_binary_part_bytes=100*1024*1024,
    max_parts_per_request=1000
)
```

## Related Documentation

- [Multipart Hardening Patch V2](MULTIPART_HARDENING_PATCH_V2.md)
- [Multipart Per-Part Limits](MULTIPART_PER_PART_LIMITS.md)
- [Metrics Label Guard](../observability/METRICS_LABEL_GUARD.md)

---

**Status**: Production Ready
**Version**: 1.0
**Last Updated**: 2025-09-16
**Security Review**: External review completed
