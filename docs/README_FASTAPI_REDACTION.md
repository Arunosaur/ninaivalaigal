# FastAPI Redaction Middleware

A comprehensive FastAPI middleware package that provides streaming redaction for HTTP requests and responses, protecting sensitive data in real-time.

## Overview

This middleware package implements enterprise-grade redaction capabilities for FastAPI applications, featuring:

- **Request Body Redaction**: Automatically redacts secrets in incoming HTTP requests
- **Response Body Redaction**: Protects sensitive data in outgoing HTTP responses
- **Streaming Support**: Handles large payloads with chunk-by-chunk processing
- **Overlap Detection**: Catches secrets split across chunk boundaries
- **Detector Integration**: Plugs into existing redaction engines or provides fallback patterns

## Components

### 1. RedactionASGIMiddleware
ASGI middleware that intercepts HTTP request messages and redacts the body before it reaches your routes.

```python
from fastapi import FastAPI
from server.security.middleware.fastapi_redaction import RedactionASGIMiddleware
from server.security.redaction.detector_glue import detector_fn

app = FastAPI()
app.add_middleware(RedactionASGIMiddleware, detector_fn=detector_fn, overlap=64)
```

### 2. ResponseRedactionASGIMiddleware
ASGI middleware that redacts HTTP response bodies before they go out to clients.

```python
from server.security.middleware.response_redaction import ResponseRedactionASGIMiddleware

app.add_middleware(ResponseRedactionASGIMiddleware, detector_fn=detector_fn, overlap=64)
```

### 3. StreamingRedactor
Utility class for redacting streaming data with overlap handling.

```python
from server.security.middleware.streaming_redaction import StreamingRedactor

redactor = StreamingRedactor(detector_fn=detector_fn, overlap=32)
async for redacted_chunk in redactor.redact_stream(stream):
    # Process redacted chunk
    pass
```

### 4. Detector Glue System
Provides a unified interface that attempts to use the existing redaction engine, with fallback to basic regex patterns.

```python
from server.security.redaction.detector_glue import detector_fn, enhanced_detector_fn

# Basic detection
redacted = detector_fn("Text with sk-1234567890abcdef1234567890abcdef12345678")

# Enhanced detection with entropy analysis
redacted = enhanced_detector_fn("Text with high entropy secrets")
```

## Features

### Supported Secret Types
- **OpenAI API Keys**: `sk-*` patterns
- **AWS Access Keys**: `AKIA*` patterns
- **GitHub Tokens**: `ghp_*` patterns
- **JWT Tokens**: Standard JWT format
- **PEM Keys**: Certificate and private key blocks
- **Credit Cards**: Standard credit card number patterns
- **Email Addresses**: Partial redaction preserving domain
- **Phone Numbers**: US phone number formats
- **High-Entropy Strings**: Configurable entropy threshold detection

### Performance Features
- **Streaming Processing**: Handles large payloads efficiently
- **Overlap Window**: Configurable overlap to catch boundary-split secrets
- **UTF-8 Safe**: Proper encoding handling with error recovery
- **Non-Blocking**: Asynchronous processing for high throughput

### Integration Features
- **Engine Integration**: Automatically uses existing `server.security.redaction` engine
- **Fallback Patterns**: Basic regex patterns when engine unavailable
- **Configurable**: Adjustable overlap windows and detection thresholds
- **Error Handling**: Graceful degradation on processing errors

## Usage Examples

### Basic FastAPI Integration
```python
from fastapi import FastAPI
from server.security.middleware.fastapi_redaction import RedactionASGIMiddleware
from server.security.middleware.response_redaction import ResponseRedactionASGIMiddleware
from server.security.redaction.detector_glue import detector_fn

app = FastAPI()

# Add request redaction
app.add_middleware(RedactionASGIMiddleware, detector_fn=detector_fn, overlap=64)

# Add response redaction
app.add_middleware(ResponseRedactionASGIMiddleware, detector_fn=detector_fn, overlap=64)

@app.post("/api/data")
async def handle_data(data: dict):
    # Request body automatically redacted before reaching here
    # Response will be redacted before sending to client
    return {"processed": data}
```

### Custom Detector Function
```python
def custom_detector(text: str) -> str:
    # Custom redaction logic
    redacted = text.replace("CUSTOM_SECRET", "[REDACTED]")
    return redacted

app.add_middleware(RedactionASGIMiddleware, detector_fn=custom_detector)
```

### Streaming Response Handling
```python
from fastapi.responses import StreamingResponse

@app.get("/stream")
async def stream_data():
    async def generate():
        for chunk in large_dataset:
            yield f"data: {chunk}\n"

    # Response will be automatically redacted chunk-by-chunk
    return StreamingResponse(generate(), media_type="text/plain")
```

## Configuration

### Environment Variables
- `REDACTION_ENABLED`: Enable/disable redaction (default: true)
- `REDACTION_MIN_ENTROPY`: Minimum entropy for high-entropy detection (default: 4.0)
- `REDACTION_MIN_LENGTH`: Minimum length for entropy analysis (default: 8)

### Middleware Parameters
- `detector_fn`: Function that takes text and returns redacted text
- `overlap`: Number of characters to overlap between chunks (default: 64)

## Testing

Run the comprehensive test suite:
```bash
python -m pytest tests/test_fastapi_redaction_middleware.py -v
python -m pytest tests/test_response_redaction_middleware.py -v
python -m pytest tests/test_streaming_redaction.py -v
```

## Security Considerations

1. **Memory Safety**: Middleware processes chunks to avoid loading large payloads into memory
2. **Encoding Safety**: Uses UTF-8 with error replacement to prevent crashes
3. **Performance**: Configurable overlap windows balance security vs. performance
4. **Audit Trail**: Integrates with existing audit logging when available
5. **Fail-Safe**: Graceful degradation ensures application availability

## Integration with Existing Systems

The middleware is designed to integrate seamlessly with the existing Ninaivalaigal security architecture:

- **RBAC Integration**: Respects user context and sensitivity tiers
- **Audit Logging**: Automatically logs redaction events when audit system available
- **Configuration**: Uses existing redaction configuration and rules
- **Detection Engine**: Leverages existing `ContextualRedactor` and `CombinedSecretDetector`

## Benchmarks

Performance characteristics on typical hardware:
- **Small Payloads** (<1KB): <1ms overhead
- **Medium Payloads** (1-100KB): 2-5ms overhead
- **Large Payloads** (>1MB): Streaming processing, constant memory usage
- **Throughput**: Minimal impact on request/response throughput

See `benchmarks/asgi_upload_harness.py` for detailed performance testing.
