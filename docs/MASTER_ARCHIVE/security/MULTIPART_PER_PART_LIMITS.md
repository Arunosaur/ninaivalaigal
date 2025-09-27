# Multipart Per-Part Limits with Magic Byte Detection

## Overview

Enhanced multipart validation system with per-part size limits and comprehensive magic byte detection to prevent upload-based security attacks. This implementation provides robust protection against executable uploads, content-type spoofing, and binary masquerade attacks.

## Features

### Magic Byte Detection
- **15+ File Format Signatures**: PE, ELF, PDF, PNG, JPEG, GIF, ZIP, Office docs, audio/video formats
- **Executable Identification**: Automatic detection and blocking of PE (.exe), ELF (Linux), and Java executables
- **Content Integrity Validation**: Detects mismatches between declared content-type and actual file format
- **High-Confidence Detection**: 95% confidence scoring for magic byte matches

### Per-Part Size Limits
- **Differential Limits**: Separate size limits for text (1MB) vs binary (10MB) content
- **Content-Aware Enforcement**: Automatic classification based on magic bytes and binary characteristics
- **Configurable Policies**: Strict and permissive modes with customizable thresholds
- **Fail-Safe Design**: Blocks oversized content with detailed error reporting

### Security Policies
- **Executable Blocking**: Critical severity blocking of executable content by default
- **Content-Type Validation**: Warns on content-type vs magic byte mismatches
- **Binary Masquerade Detection**: Multi-layered approach using null bytes, entropy, and printable ratios
- **Audit Logging**: Structured logging of security violations with metadata

## Implementation

### Core Components

#### 1. Magic Byte Detection (`strict_limits.py`)

```python
from server.security.multipart.strict_limits import detect_magic_bytes, PartLimitConfig

# Detect file format from content
result = detect_magic_bytes(content_bytes)
print(f"Detected: {result.detected_type}, Executable: {result.is_executable}")

# Configure per-part limits
config = PartLimitConfig(
    max_text_part_bytes=1 * 1024 * 1024,     # 1MB for text
    max_binary_part_bytes=10 * 1024 * 1024,  # 10MB for binary
    block_executable_magic_bytes=True,        # Block executables
    enforce_magic_byte_checks=True            # Validate content integrity
)
```

#### 2. Enhanced Multipart Validator (`strict_validator.py`)

```python
from server.security.multipart.strict_validator import StrictMultipartValidator

validator = StrictMultipartValidator()

# Validate multipart request with content analysis
result = validator.validate_part(
    field_name="upload",
    content_type="image/png",
    filename="image.png",
    content=file_bytes,
    part_limit_config=config
)

if not result["valid"]:
    print(f"Validation failed: {result['violations']}")
```

#### 3. Starlette Integration

```python
from server.security.multipart.strict_validator import validate_starlette_multipart

# Validate FastAPI/Starlette multipart request
async def upload_handler(request):
    validation_result = await validate_starlette_multipart(
        request,
        part_limit_config=config,
        read_content=True  # Enable content analysis
    )

    if not validation_result["valid"]:
        raise HTTPException(400, "Invalid multipart content")
```

### Magic Byte Signatures

| Format | Signature | Type | Executable |
|--------|-----------|------|------------|
| PE Executable | `MZ` | `application/x-msdownload` | ✅ |
| ELF Executable | `\x7fELF` | `application/x-executable` | ✅ |
| Java Class | `\xca\xfe\xba\xbe` | `application/java-vm` | ✅ |
| PDF | `%PDF` | `application/pdf` | ❌ |
| PNG | `\x89PNG\r\n\x1a\n` | `image/png` | ❌ |
| JPEG | `\xff\xd8\xff` | `image/jpeg` | ❌ |
| ZIP/Office | `PK\x03\x04` | `application/zip` | ❌ |
| GZIP | `\x1f\x8b\x08` | `application/gzip` | ❌ |

## Configuration

### Production Configuration

```python
# Strict policy for production
config = PartLimitConfig(
    max_part_bytes=10 * 1024 * 1024,         # 10MB absolute limit
    max_text_part_bytes=1 * 1024 * 1024,     # 1MB for text content
    max_binary_part_bytes=10 * 1024 * 1024,  # 10MB for binary content
    enforce_magic_byte_checks=True,           # Enable magic byte validation
    block_executable_magic_bytes=True,        # Block executables (CRITICAL)
    printable_threshold=0.30                  # 30% printable char threshold
)

policy = create_strict_policy(
    allow_binary=True,  # Allow binary uploads
    custom_text_types={"text/plain", "application/json"},
    custom_binary_types={"image/png", "image/jpeg", "application/pdf"}
)
```

### Development Configuration

```python
# Permissive policy for development
config = PartLimitConfig(
    max_part_bytes=50 * 1024 * 1024,         # 50MB limit
    max_text_part_bytes=5 * 1024 * 1024,     # 5MB for text
    max_binary_part_bytes=50 * 1024 * 1024,  # 50MB for binary
    enforce_magic_byte_checks=False,          # Disable for dev
    block_executable_magic_bytes=False,       # Allow executables in dev
    printable_threshold=0.20                  # Relaxed threshold
)

policy = create_permissive_policy()  # More content types allowed
```

## Security Benefits

### Attack Prevention

1. **Executable Upload Prevention**
   - Blocks PE, ELF, and Java executables automatically
   - Prevents malware distribution through file uploads
   - Critical severity violations with audit logging

2. **Content-Type Spoofing Detection**
   - Validates declared content-type against magic bytes
   - Detects attempts to bypass file type restrictions
   - Structured logging for security monitoring

3. **Binary Masquerade Protection**
   - Multi-layered binary detection (null bytes, entropy, magic bytes)
   - Prevents binary content disguised as text
   - Configurable detection thresholds

4. **Size-Based DoS Prevention**
   - Differential limits prevent resource exhaustion
   - Early rejection of oversized content
   - Separate limits for different content types

### Compliance Features

- **Audit Trail**: Comprehensive logging of all security violations
- **Policy Enforcement**: Configurable policies for different environments
- **Metadata Enrichment**: Detailed violation information for compliance reporting
- **Fail-Safe Design**: Secure defaults with explicit opt-in for relaxed policies

## Testing

### Test Coverage

The implementation includes 23 comprehensive tests covering:

```bash
# Run multipart per-part limits tests
cd /Users/asrajag/Workspace/mem0
python -m pytest tests/test_multipart_per_part_limits.py -v

# Expected output: 23 passed
```

### Test Categories

1. **Magic Byte Detection Tests**
   - PE/PDF/PNG/ELF format detection
   - Executable identification
   - Empty content handling

2. **Per-Part Limit Tests**
   - Size limit enforcement
   - Text vs binary differentiation
   - Executable blocking
   - Content-type mismatch detection

3. **Integration Tests**
   - Strict validator integration
   - Starlette multipart validation
   - Policy configuration validation

4. **Edge Case Tests**
   - Large content handling
   - Multiple violations
   - Empty and malformed content

## Performance Considerations

### Optimization Features

1. **Limited Magic Byte Scanning**: Only checks first 512 bytes for efficiency
2. **Early Rejection**: Size limits checked before expensive content analysis
3. **Configurable Thresholds**: Adjustable detection sensitivity for performance tuning
4. **Streaming-Safe**: Designed for integration with streaming multipart parsers

### Memory Usage

- **Magic Byte Detection**: O(1) memory usage, constant 512-byte buffer
- **Content Analysis**: Processes content in chunks, not full file loading
- **Validation Results**: Structured data with minimal memory footprint

## Integration Examples

### FastAPI Middleware

```python
from fastapi import FastAPI, HTTPException, UploadFile
from server.security.multipart.strict_validator import validate_starlette_multipart

app = FastAPI()

@app.post("/upload")
async def upload_file(request: Request):
    # Validate multipart content before processing
    validation = await validate_starlette_multipart(request)

    if not validation["valid"]:
        violations = [v for part in validation["part_results"]
                     for v in part["violations"]]
        raise HTTPException(400, f"Upload validation failed: {violations}")

    # Process validated upload
    form = await request.form()
    # ... handle upload
```

### Custom Validation Pipeline

```python
def validate_upload_content(content: bytes, content_type: str, filename: str):
    """Custom validation with enhanced security."""
    config = PartLimitConfig(
        max_binary_part_bytes=5 * 1024 * 1024,  # 5MB limit
        block_executable_magic_bytes=True
    )

    try:
        result = enforce_part_limits(content, content_type, filename, config)
        return {
            "valid": result["valid"],
            "size": result["size_bytes"],
            "is_binary": result["is_binary"],
            "detected_type": result["magic_byte_result"].detected_type if result["magic_byte_result"] else None
        }
    except ValueError as e:
        return {"valid": False, "error": str(e)}
```

## Monitoring and Alerting

### Security Metrics

Monitor these key metrics for security posture:

1. **Executable Upload Attempts**: Count of blocked executable uploads
2. **Content-Type Mismatches**: Frequency of spoofing attempts
3. **Size Limit Violations**: Patterns in oversized upload attempts
4. **Magic Byte Detection Rate**: Effectiveness of format detection

### Log Analysis

```python
# Example log analysis for security monitoring
import logging

logger = logging.getLogger("server.security.multipart.strict_limits")

# Monitor for these log patterns:
# - "Content-type mismatch detected" (spoofing attempts)
# - "Executable content blocked" (malware uploads)
# - "Part size exceeded" (DoS attempts)
```

## Future Enhancements

### Planned Features

1. **Advanced Entropy Analysis**: Enhanced detection of encrypted/compressed content
2. **Machine Learning Integration**: AI-powered content classification
3. **Real-time Threat Intelligence**: Dynamic signature updates
4. **Performance Profiling**: Detailed timing and resource usage metrics

### Extension Points

The implementation provides extension points for:
- Custom magic byte signatures
- Additional content analysis algorithms
- Integration with external security services
- Custom validation policies and rules

## Conclusion

The enhanced multipart per-part limits implementation provides enterprise-grade security for file upload functionality while maintaining performance and usability. The comprehensive magic byte detection and configurable policies ensure robust protection against common upload-based attack vectors.

For additional security hardening, combine this implementation with:
- Content scanning services (antivirus/malware detection)
- File type allowlists at the application level
- Rate limiting on upload endpoints
- Comprehensive audit logging and monitoring
