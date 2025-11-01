# Ninaivalaigal Storage Library

Shared storage abstraction powering EPIC#022 (file upload infrastructure).

## Features

- Environment-driven configuration for S3 or MinIO-compatible endpoints
- Pluggable backend factory with single entrypoint
- Upload, download, delete, and pre-signed URL helpers
- Optional bucket auto-provisioning for local development

## Usage

```python
from ninaivalaigal_storage import create_storage_backend

storage = create_storage_backend()
key = storage.upload_bytes(b"hello", "attachments/welcome.txt", content_type="text/plain")
print(storage.generate_presigned_url(key, expires_in=300))
```

Configuration values are read from environment variables (see `.env.dev`).
