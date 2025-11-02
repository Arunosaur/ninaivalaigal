# SPEC-074 GDPR Compliance - Quick Start Guide

**For**: Developer G
**Status**: Phase 1 Complete - Ready for Testing

---

## 🚀 Getting Started

### 1. Apply Database Migration

```bash
cd server
alembic upgrade head
```

This creates:
- `public.data_subject_requests` table
- `public.data_exports` table
- Indexes and triggers

### 2. Verify Installation

```bash
# Check tables exist
psql -d ninaivalaigal_dev -c "\dt public.data_*"

# Check API is registered
curl http://localhost:8000/docs | grep compliance
```

### 3. Test DSAR Endpoint

```bash
# Get auth token
TOKEN=$(curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"password"}' \  # pragma: allowlist secret
  | jq -r '.jwt_token')

# Submit DSAR request
curl -X POST http://localhost:8000/api/v1/compliance/dsar \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"description":"Requesting my data"}'

# Check request status
curl http://localhost:8000/api/v1/compliance/requests \
  -H "Authorization: Bearer $TOKEN"
```

---

## 📋 API Endpoints Quick Reference

### Submit Requests

```bash
# DSAR (Article 15)
POST /api/v1/compliance/dsar
Body: {"description": "optional"}

# Erasure (Article 17)
POST /api/v1/compliance/erasure
Body: {"confirm_erasure": true, "description": "optional"}

# Portability (Article 20)
POST /api/v1/compliance/portability
Body: {"format": "json", "description": "optional"}
```

### Check Status

```bash
# Get specific request
GET /api/v1/compliance/requests/{request_id}

# List all requests
GET /api/v1/compliance/requests

# Get export status
GET /api/v1/compliance/exports/{export_id}

# Download export
GET /api/v1/compliance/exports/{export_id}/download
```

---

## 🔍 Code Locations

- **Migration**: `alembic/versions/0127_spec074_gdpr_compliance_schema.py`
- **Models**: `server/compliance/models.py`
- **GDPR Manager**: `server/compliance/gdpr.py`
- **Data Collector**: `server/compliance/data_collector.py`
- **Export System**: `server/compliance/export.py`
- **API Endpoints**: `server/compliance/api.py`

---

## ⚠️ Important Notes

1. **Erasure is Irreversible**: Test with test users only
2. **Legal Obligations**: Billing records may be retained
3. **Encryption**: Phase 2 - currently placeholder
4. **Export Storage**: In-memory - Phase 2 will add S3/Azure

---

## 📚 Full Documentation

See `/docs/spec-analysis/SPEC_074_*` for complete documentation.
