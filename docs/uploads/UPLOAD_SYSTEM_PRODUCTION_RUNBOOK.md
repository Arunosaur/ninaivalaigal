# Upload System Production Runbook

Operational guide for deploying, verifying, and maintaining the Ninaivalaigal multipart upload stack in production (US#406). Pair this runbook with the [Multipart Upload API Guide](MULTIPART_UPLOAD_API_GUIDE.md) for endpoint-level details.

---

## 1. System Summary
- **Service:** `services/core-api` (FastAPI app served by container `ninaivalaigal-dev-em` / production equivalent)
- **Responsibilities:**
  - Issue presigned URLs for multipart S3/MinIO uploads
  - Persist upload session state in Redis
  - Orchestrate completion/abort logic via `ninaivalaigal_storage`
  - Enforce JWT auth, per-user rate limits, and audit logging for aborts & throttling events
- **Primary Modules:**
  - `lib/api/upload_api.py`
  - `lib/uploads/multipart_service.py`
  - `lib/dependencies.py`
  - `shared/storage/ninaivalaigal_storage`

---

## 2. Prerequisites & Configuration

| Component | Requirement | Notes |
|-----------|-------------|-------|
| **Python env** | 3.11+ (conda env `nina` recommended) | Ensure FastAPI & httpx installed (`pip install -r requirements.txt`) |
| **Redis** | Accessible Redis cluster | `REDIS_URL`, `REDIS_HOST`, `REDIS_PORT`, credentials configured in service env |
| **Object Storage** | S3/MinIO bucket | Configure via `STORAGE_*` variables (see table below) |
| **JWT Secret** | Shared with auth service | Move `JWT_SECRET` into environment variable before production |
| **Networking** | Allow presigned URL traffic | Confirm CORS/ACLs for client domains |
| **Containers** | `ninaivalaigal-dev-em` / production analog | Should expose FastAPI router with multipart endpoints |

### Storage Environment Variables

| Variable | Purpose | Default |
|----------|---------|---------|
| `STORAGE_PROVIDER` | `s3` or `minio` | `s3` |
| `STORAGE_BUCKET` / `STORAGE_S3_BUCKET` | Target bucket | `ninaivalaigal-{env}-attachments` |
| `STORAGE_PREFIX` | Optional object prefix | _empty_ |
| `STORAGE_S3_REGION` | Region for AWS | `us-east-1` |
| `STORAGE_S3_ENDPOINT` | Custom endpoint for MinIO | `http://localhost:9000` when provider=`minio` |
| `STORAGE_S3_ACCESS_KEY` / `STORAGE_S3_SECRET_KEY` | Credentials | _required_ |
| `STORAGE_PRESIGN_EXPIRY` | URL TTL (seconds) | `900` |
| `STORAGE_S3_FORCE_PATH_STYLE` | Force path-style URLs | `true` for MinIO |
| `STORAGE_S3_AUTO_CREATE_BUCKET` | Auto-create bucket | `true` when provider=`minio` |

### Rate Limiter Settings
- Uses Redis sorted sets with keys `rate:<user_id>:<endpoint>`.
- Default thresholds defined in `upload_api.py`. Override via constants or environment patch (future enhancement).

---

## 3. Deployment Procedure

1. **Prepare Environment**
   ```bash
   # Load environment variables
   source envs/prod/upload-service.env
   # Activate Python environment
   conda activate nina
   pip install -r requirements.txt
   ```

2. **Validate Dependencies**
   - Redis reachable: `redis-cli -h <host> -p <port> PING`
   - Storage credentials: run `python -m ninaivalaigal_storage.tests.smoke` (optional) or perform presign dry run via `MultipartUploadService` shell.

3. **Run Service**
   - Via container orchestrator (Kubernetes/compose) ensure `ninaivalaigal-core-api` deployment references updated image/tag.
   - Confirm `upload_api` router is included (check logs on startup for `multipart` route registration).

4. **Apply Config Maps / Secrets**
   - JWT secret, storage credentials, Redis URL.
   - Update K8s secrets or `.env` files accordingly.

5. **Deploy**
   - Rolling update or blue/green according to environment standards.
   - Monitor logs for `structlog` entries (`multipart session started`, etc.).

---

## 4. Post-Deployment Verification

1. **Automated Tests**
   ```bash
   # Run from repo root
   python -m pytest services/core-api/tests/integration/test_upload_flow.py -q
   ```
   Confirms happy path, abort workflow, backend failure handling, rate limiting, and audit logging.

2. **Smoke Test Script**
   Use the checked-in client script (`scripts/uploads/smoke_test_multipart.py`) described in section 6 to execute an end-to-end multipart upload against production.

3. **Manual Checks**
   - Acquire valid JWT from auth service.
   - Start session, upload a small file in three parts using presigned URLs (see API guide).
   - Verify object appears in storage bucket.
   - Abort a test session and ensure it no longer exists in Redis.
   - Inspect audit logs for `multipart_upload_abort` event (see Monitoring section).

---

## 5. Monitoring & Alerting

| Signal | Source | Action |
|--------|--------|--------|
| **Rate limit violations** | `security_alert_manager.recent_events` (`RATE_LIMIT_EXCEEDED`) | Trigger warning alert if burst > threshold; indicates potential abuse |
| **Abort audit events** | `SecurityEventType.ADMIN_ACTION` | Log to SIEM for compliance |
| **Redis availability** | Health checks from `redis_client` | Alert on connection failures |
| **Storage errors** | Exceptions thrown by `MultipartUploadService` (log key `failed to list multipart parts`, `abort multipart upload failed`) | Investigate AWS/MinIO connectivity |
| **HTTP metrics** | 4xx/5xx rates for `/upload/multipart/*` | Configure in API gateway or observability stack |

### Audit Log Persistence
Current implementation stores alerts in-memory. For production:
- Configure background task to push events to existing security pipeline or database.
- Consider enabling the `security_integration` middleware to forward alerts.

---

## 6. Example Smoke Test Script

A reference script is available in `scripts/uploads/smoke_test_multipart.py`. Adapt credentials and object path as needed.

```python
#!/usr/bin/env python3
"""End-to-end multipart upload smoke test."""

import asyncio
import os
from typing import Any

import httpx

API_BASE = os.environ.get("UPLOAD_API_BASE", "http://localhost:13390/upload/multipart")
JWT_TOKEN = os.environ["UPLOAD_JWT"]
FILE_PATH = os.environ.get("UPLOAD_FILE", "./fixtures/sample.bin")

HEADERS = {"Authorization": f"Bearer {JWT_TOKEN}"}


async def main() -> None:
    async with httpx.AsyncClient(base_url=API_BASE, headers=HEADERS) as client:
        start_resp = await client.post(
            "/start",
            json={
                "object_key": "smoke-tests/sample.bin",
                "filename": "sample.bin",
                "content_type": "application/octet-stream",
                "total_size": os.path.getsize(FILE_PATH),
            },
        )
        start_resp.raise_for_status()
        session = start_resp.json()
        session_id = session["session_id"]

        print("session", session_id)

        # Upload single-part file
        url_resp = await client.post(f"/{session_id}/part-url", json={"part_number": 1})
        url_resp.raise_for_status()
        upload_url = url_resp.json()["upload_url"]

        with open(FILE_PATH, "rb") as fh:
            upload_resp = httpx.put(upload_url, data=fh)
            upload_resp.raise_for_status()
        etag = upload_resp.headers.get("etag", "smoke-etag")

        reg_resp = await client.post(
            f"/{session_id}/parts",
            json={"part_number": 1, "etag": etag},
        )
        reg_resp.raise_for_status()

        complete_resp = await client.post(f"/{session_id}/complete")
        complete_resp.raise_for_status()
        print("complete", complete_resp.json())


if __name__ == "__main__":
    asyncio.run(main())
```

**Run:**
```bash
UPLOAD_API_BASE="https://api.prod/upload/multipart" \
UPLOAD_JWT="$(cat jwt.txt)" \
UPLOAD_FILE="./assets/test.bin" \
python scripts/uploads/smoke_test_multipart.py
```

---

## 7. Incident Response

1. **Upload Failures (500s)**
   - Check storage connectivity (AWS IAM credentials, MinIO endpoint).
   - Review logs for `StorageMultipartError` details.
   - Use `sync_remote_parts` to reconcile partial uploads before retrying completion.

2. **Rate Limit Complaints**
   - Examine Redis keys for offending user (`redis-cli KEYS "rate:<user_id>:multipart*"`).
   - Adjust thresholds cautiously; escalate to security for potential abuse patterns.

3. **Stale Sessions**
   - Sessions auto-expire via Redis TTL. If cleanup required, invoke `DELETE /upload/multipart/{session}` endpoint or `MultipartUploadService.delete_session` in maintenance script.

4. **Audit Log Gaps**
   - Ensure security middleware is emitting events; consider enabling persistent sink.

---

## 8. Rollback Strategy

- Rollback deployment to previous service image.
- Invalidate new environment variables if incompatible.
- Revert rate limiter configuration if changed.
- Verify integration tests on rollback version.

---

## 9. Reference Materials
- [Multipart Upload API Guide](MULTIPART_UPLOAD_API_GUIDE.md)
- `services/core-api/lib/api/upload_api.py`
- `services/core-api/lib/uploads/multipart_service.py`
- Example Task/Taiga automation scripts (for documentation updates): `tasks/tmp/scripts`

---

_Last updated: 2025-11-01_
