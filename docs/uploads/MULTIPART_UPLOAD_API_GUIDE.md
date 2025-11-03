# Multipart Upload API Guide

Comprehensive reference for integrating the Ninaivalaigal Core API multipart upload workflow in production environments. This document covers security controls (JWT auth, rate limiting, audit logging), endpoint contracts, client integration patterns, required infrastructure, and the deployment checklist for US-362.

---

## 1. Overview
- **Service:** `services/core-api` (`ninaivalaigal-dev-em` container)
- **Purpose:** Coordinate S3/MinIO-compatible multipart uploads via FastAPI endpoints backed by Redis session storage and the `ninaivalaigal_storage` abstraction.
- **Key Modules:**
  - `lib/api/upload_api.py` – FastAPI router, auth hooks, rate limiting, audit logging
  - `lib/uploads/multipart_service.py` – Multipart orchestration and Redis-backed session state
  - `lib/dependencies.py` – Dependency injection for Redis, upload service, and rate limiter
  - `shared/storage/ninaivalaigal_storage` – Configurable storage backend factory

---

## 2. Security Requirements
1. **JWT Authentication**
   - Every endpoint requires an `Authorization: Bearer <JWT>` header.
   - Tokens are validated via `auth_utils.get_current_user`; requests missing `user_id` are rejected with `401`.
2. **Per-Endpoint Rate Limiting** (Redis-backed)
   - Enforced in `upload_api` through `get_rate_limiter`. Thresholds:

     | Endpoint                       | Limit / Window | Redis Key Format                |
     |--------------------------------|----------------|----------------------------------|
     | `POST /upload/multipart/start` | 5 per 60s      | `rate:<user_id>:multipart:start` |
     | `POST /{session}/part-url`     | 300 per 60s    | `rate:<user_id>:multipart:part-url` |
     | `POST /{session}/parts`        | 600 per 60s    | `rate:<user_id>:multipart:register` |
     | `POST /{session}/complete`     | 30 per 60s     | `rate:<user_id>:multipart:complete` |
     | `DELETE /{session}`            | 30 per 60s     | `rate:<user_id>:multipart:abort` |
     | `GET /{session}/status`        | 120 per 60s    | `rate:<user_id>:multipart:status` |

   - Exceeding the limit returns HTTP `429` and records `SecurityEventType.RATE_LIMIT_EXCEEDED`.
3. **Audit Logging**
   - Successful aborts emit `SecurityEventType.ADMIN_ACTION` with session metadata.
   - Rate limit violations log the same event type as above.

---

## 3. Endpoint Catalogue

| Method | Path                                   | Description                              | Success Codes |
|--------|----------------------------------------|------------------------------------------|---------------|
| POST   | `/upload/multipart/start`              | Initialize a new multipart session       | `201`         |
| POST   | `/upload/multipart/{session_id}/part-url` | Generate a presigned URL for a part   | `200`         |
| POST   | `/upload/multipart/{session_id}/parts` | Register uploaded part metadata          | `200`         |
| POST   | `/upload/multipart/{session_id}/complete` | Finalize multipart upload             | `200`         |
| DELETE | `/upload/multipart/{session_id}`       | Abort and clean up a multipart session   | `200`         |
| GET    | `/upload/multipart/{session_id}/status` | Retrieve session status & progress    | `200`         |

### 3.1 Start Session
```http
POST /upload/multipart/start
Authorization: Bearer <JWT>
Content-Type: application/json

{
  "object_key": "tenant123/reports/weekly.pdf",
  "filename": "weekly.pdf",
  "content_type": "application/pdf",
  "total_size": 15728640,
  "part_size": 5242880,
  "metadata": {"origin": "web-console"}
}
```

**Response `201`:**
```json
{
  "session_id": "f1f3275ab0674acfb99d067eb57ede19",
  "upload_id": "upload-42",
  "bucket": "ninaivalaigal-dev-attachments",
  "key": "tenant123/reports/weekly.pdf",
  "status": "in_progress",
  "part_size": 5242880,
  "part_count": 3,
  "expires_at": "2025-11-01T18:44:21.132Z"
}
```

### 3.2 Get Part Upload URL
`POST /upload/multipart/{session_id}/part-url`
```json
{
  "part_number": 1,
  "expires_in": 900
}
```
**Response `200`:**
```json
{
  "upload_url": "https://example.com/...",
  "part_number": 1,
  "expires_in": 900
}
```
Errors: `404` (unknown session), `409` (session not active), `429` (rate limit).

### 3.3 Register Part Metadata
`POST /upload/multipart/{session_id}/parts`
```json
{
  "part_number": 1,
  "etag": "etag-1",
  "size": 5242880
}
```
Response: `200` with `{ "success": true, "part_number": 1, "parts_uploaded": 1 }`

### 3.4 Complete Upload
`POST /upload/multipart/{session_id}/complete`
- Returns `409` if no parts uploaded or session already aborted.
- Returns `200` with final location information on success.
- Propagates backend failures as `500`.

### 3.5 Abort Upload
`DELETE /upload/multipart/{session_id}`
- Returns `200` on success, `404` when session is unknown.
- Emits security audit event containing session ID, upload ID, bucket, and object key.

### 3.6 Session Status
`GET /upload/multipart/{session_id}/status`
- Returns progress metrics (`uploaded_bytes`, `parts_uploaded`, timestamps).
- `404` for missing sessions.

---

## 4. Client Integration Flow
1. **Start Session** – call the `start` endpoint, capture `session_id` and `upload_id`.
2. **Upload Parts**
   - Request presigned URLs for each part number sequentially.
   - Upload file chunks directly to storage using the signed URLs.
   - After each upload, call `parts` endpoint with `part_number`, `etag`, and optional `size`.
3. **Monitor Progress** – optionally poll `status` for UI updates.
4. **Complete Session** – invoke `complete` when all parts registered.
5. **Abort if Needed** – call `DELETE` to cancel stalled or failed uploads; check audit logs.

**Retry Guidance**
- Transient failures on `part-url`/`parts` should back off and retry respecting rate limits.
- If client loses local state, call `status` (or implement `sync_remote_parts`) to refresh part list.

---

## 5. Error Handling Summary
- `401 Unauthorized` – missing/invalid JWT token.
- `404 Not Found` – session unknown or expired from Redis.
- `409 Conflict` – invalid session state (completed/aborted) or missing parts on completion.
- `429 Too Many Requests` – rate limit exceeded; retry after `window` seconds.
- `500 Internal Server Error` – storage backend failure (`StorageMultipartError` or unexpected exception).

All errors return JSON bodies with a `detail` message suitable for surfaced client logging.

---

## 6. Environment & Configuration

### Core Requirements
- **Redis:** required for session persistence and rate limiting (`redis_client`). Ensure connectivity and credentials in `services/core-api/.env` or deployment environment.
- **Storage Backend:** configured via `ninaivalaigal_storage.load_storage_settings` with the following notable variables:
  - `STORAGE_PROVIDER` (`s3` or `minio`)
  - `STORAGE_BUCKET` or `STORAGE_S3_BUCKET`
  - `STORAGE_PREFIX` (optional key prefix)
  - `STORAGE_PRESIGN_EXPIRY` (seconds, defaults to 900)
  - `STORAGE_S3_ENDPOINT`, `STORAGE_S3_REGION`, credentials (`STORAGE_S3_ACCESS_KEY`, `STORAGE_S3_SECRET_KEY`, etc.)
  - `STORAGE_S3_USE_SSL`, `STORAGE_S3_VERIFY_SSL`, `STORAGE_S3_FORCE_PATH_STYLE`
- **JWT Secret:** `auth_utils` currently loads `JWT_SECRET` directly from code (follow-up: move to env variable before production). Ensure tokens issued by upstream auth service align with required claims (`user_id`, `email`, `account_type`, `role`).
- **FastAPI Service:** run via container `ninaivalaigal-dev-em` or `make run-core-api`. Ensure `lib/api/upload_api.py` router is included in the main app.

### Observability
- Structured logs (`structlog`) are emitted by `multipart_service` for start/register/complete/abort events.
- Security audit events stored in-memory (`security_alert_manager`) by default; integrate with persistence/alerts in production.

---

## 7. Deployment Checklist
- [ ] **Secrets** – Configure JWT secret, storage credentials, and Redis connection in deployment environment.
- [ ] **Rate Limiter** – Verify Redis availability and confirm `rate:` keys are created during smoke tests.
- [ ] **Storage Bucket** – Ensure target bucket exists (or enable `STORAGE_S3_AUTO_CREATE_BUCKET` for MinIO).
- [ ] **CORS / Networking** – Allow presigned URL access from client domain(s).
- [ ] **Health Checks** – Extend readiness checks to cover Redis and storage via `multipart_service`. Optional: create `/upload/multipart/health` probe.
- [ ] **Monitoring** – Wire security audit events to alerting pipeline; capture 4xx/5xx metrics per endpoint.
- [ ] **Documentation Hand-off** – Link this guide in `API_DOCUMENTATION_INDEX.md` and share with integrators.
- [ ] **Release Notes** – Include US-361/US-362 details in next deployment note.

---

## 8. Testing & Verification
- **Unit Tests:** `python -m pytest services/core-api/tests/uploads/test_multipart_service.py -q`
- **Integration Tests:** `python -m pytest services/core-api/tests/integration/test_upload_flow.py -q`
  - Coverage includes happy path, abort, conflict states, backend failure propagation, rate limiting, and audit logging assertions.
- **Manual Smoke Test:**
  1. Obtain JWT from auth service.
  2. Walk through the integration flow against `ninaivalaigal-dev-em`.
  3. Confirm uploaded object appears in storage bucket; verify Redis session removal on abort/complete.
  4. Inspect security logs (`security_alert_manager.recent_events` or configured sink) for abort/rate-limit entries.

---

## 9. Change Log
- **2025-11-01:** Initial publication for US-362 – documents security hardening, integration steps, and deployment requirements for multipart uploads.
