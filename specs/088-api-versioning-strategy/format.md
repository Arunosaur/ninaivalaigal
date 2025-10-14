# API Versioning Format

## URL Versioning

## Header Versioning

## Hybrid Approach

## Recommendation

## Version Header Examples

### Request Examples

**Requesting v1:**
```http
GET /api/memories
Accept: application/vnd.ninaivalaigal.v1+json
```

**Requesting v2:**
```http
GET /api/memories
Accept: application/vnd.ninaivalaigal.v2+json
```

### Response Format Differences

**v1 Response:**
```json
{
  "data": [
    {
      "id": "123",
      "text": "This is a memory."
    }
  ]
}
```

**v2 Response (with new `metadata` field):**
```json
{
  "data": [
    {
      "id": "123",
      "text": "This is a memory.",
      "metadata": {
        "source": "API"
      }
    }
  ]
}
```

### Content Negotiation

If a client requests a version that does not exist, the server should respond with a `406 Not Acceptable` status code. If the client does not specify a version, the server should default to the latest stable version.
