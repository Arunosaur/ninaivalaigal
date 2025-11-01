# SPEC-032 & SPEC-077 Analysis - File Upload Infrastructure

**Date**: November 1, 2025
**Status**: Comprehensive Analysis Complete
**Recommendation**: Create shared infrastructure (EPIC#022)

---

## 📊 Executive Summary

**Finding**: SPEC-032 (Memory Attachments) and SPEC-077 (Multimodal Memory Capture) require identical file upload and storage infrastructure but were specified independently.

**Recommendation**: Create unified **EPIC#022: File Upload & Storage Infrastructure** to serve both SPECs, eliminating potential duplication and ensuring consistent security/compliance.

**Effort**: 34 story points (~4-5 weeks)
**Priority**: HIGH (enables 2 major features)

---

## 🔍 SPEC-032: Memory Attachments

### Objective
Enable users to attach documents, code snippets, images, or videos to **existing memory tokens** for enriched recall and deeper AI integration.

### Use Cases
- Attach grant documents, architectural diagrams, meeting recordings to memory tokens
- Enrich code review discussions with snippets and changelogs
- Link multimedia assets to planning meetings
- Enable AI to access both textual and non-textual memory inputs

### Status
- **Implementation**: 0% (PLANNED)
- **Documentation**: ✅ Complete (`specs/032-memory-attachments/README.md`)
- **Taiga Tracking**: ⚠️ Needs stories

### Key Features
1. Multipart file upload API
2. Support for documents, code, images, videos
3. Storage URL management
4. Attachment metadata tracking
5. ACL integration for visibility

### Data Model
```sql
CREATE TABLE memory_attachments (
    attachment_id UUID PRIMARY KEY,
    memory_id UUID REFERENCES memory_tokens(memory_id),
    type TEXT CHECK (type IN ('document', 'code', 'image', 'video')),
    filename TEXT,
    mime_type TEXT,
    storage_url TEXT,
    uploaded_at TIMESTAMP DEFAULT now()
);
```

---

## 🔍 SPEC-077: Multimodal Memory Capture

### Objective
Enable users to **create new memories** directly from media files (images, audio, video) with AI-powered transcription and analysis.

### Use Cases
- Voice note → transcribed text memory
- Screenshot → OCR'd and stored memory
- Meeting recording → summarized memory with timestamps
- Image → described and tagged memory

### Status
- **Implementation**: 0% (PLANNED)
- **Documentation**: ✅ Complete (`specs/077-multimodal-memory-capture/README.md`)
- **Taiga Tracking**: ⚠️ Needs stories

### Key Features
1. Multipart media upload API
2. AI transcription (audio/video)
3. OCR for images
4. Automatic memory creation
5. Content analysis and tagging

### Data Model
```sql
CREATE TABLE multimodal_memories (
    memory_id UUID PRIMARY KEY REFERENCES memory_tokens(memory_id),
    source_type TEXT CHECK (source_type IN ('audio', 'video', 'image', 'file')),
    storage_url TEXT,
    transcription_text TEXT,
    analysis_metadata JSONB,
    processed_at TIMESTAMP
);
```

---

## 🔄 Critical Overlap Analysis

### Shared Infrastructure Requirements

| Component | SPEC-032 | SPEC-077 | Overlap % |
|-----------|----------|----------|-----------|
| **File Upload API** | ✅ Required | ✅ Required | 100% |
| **Storage Backend** | ✅ S3/MinIO | ✅ S3/MinIO | 100% |
| **Multipart Support** | ✅ Required | ✅ Required | 100% |
| **MIME Type Validation** | ✅ Required | ✅ Required | 100% |
| **Size Limits** | ✅ Required | ✅ Required | 100% |
| **Security (SPEC-008)** | ✅ Required | ✅ Required | 100% |
| **ACL Integration** | ✅ Required | ✅ Required | 100% |
| **Virus Scanning** | ⚠️ Planned | ⚠️ Planned | 100% |

**Overlap Severity**: 🔴 **CRITICAL** - 100% infrastructure duplication risk

---

## 💡 Consolidation Strategy

### Proposed: EPIC#022 - File Upload & Storage Infrastructure

**Approach**: Create shared infrastructure layer that serves both SPEC-032 and SPEC-077.

**Architecture**:
```
┌─────────────────────────────────────────────────────────┐
│              EPIC#022: Shared Infrastructure             │
│  ┌────────────────────────────────────────────────────┐ │
│  │  File Upload Service (multipart, streaming)        │ │
│  │  Storage Backend (S3/MinIO abstraction)            │ │
│  │  Security Layer (virus scan, MIME validation)      │ │
│  │  ACL Integration (SPEC-043)                        │ │
│  └────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
              │                              │
              ▼                              ▼
   ┌──────────────────────┐      ┌──────────────────────┐
   │   SPEC-032           │      │   SPEC-077           │
   │   Memory Attachments │      │   Multimodal Capture │
   │                      │      │                      │
   │   - Attach to       │      │   - Create from      │
   │     existing memory │      │     media file       │
   │   - Enrich context  │      │   - AI transcription │
   └──────────────────────┘      └──────────────────────┘
```

---

## 📋 Story Breakdown

### EPIC#022: File Upload & Storage Infrastructure (26 points)

**US#265: Storage Backend Implementation** (8 points)
- Set up S3/MinIO bucket configuration
- Implement storage abstraction layer
- Add environment-based storage selection
- Create pre-signed URL generation
- Test upload/download flows

**US#266: Multipart Upload Support** (5 points)
- Implement chunked file upload API
- Add resumable upload support
- Handle large files (>100MB)
- Implement progress tracking
- Test with various file sizes

**US#267: SPEC-032 Attachment Endpoints** (8 points)
- `POST /memory/{memory_id}/attachments`
- `GET /memory/{memory_id}/attachments`
- `GET /memory/{memory_id}/attachments/{attachment_id}`
- `DELETE /memory/{memory_id}/attachments/{attachment_id}`
- Integrate with memory_attachments table
- Add ACL permission checks

**US#268: SPEC-077 Multimodal Capture Endpoints** (13 points)
- `POST /memory/capture/audio`
- `POST /memory/capture/video`
- `POST /memory/capture/image`
- Implement AI transcription integration
- Implement OCR for images
- Auto-create memory tokens
- Add processing status tracking

**Total**: 34 story points (~4-5 weeks with 1 developer)

---

## 🔒 Security & Compliance

### Required Integration (SPEC-008)

1. **File Type Validation**
   - Whitelist: documents, images, audio, video
   - MIME type verification
   - Magic number validation

2. **Size Limits**
   - Documents: 10MB max
   - Images: 5MB max
   - Audio: 50MB max
   - Video: 200MB max

3. **Virus Scanning**
   - ClamAV integration
   - Scan before storage
   - Quarantine suspicious files

4. **Access Control (SPEC-043)**
   - User/team/organization scoping
   - Read/write/delete permissions
   - Audit trail for all uploads

---

## 📈 Benefits of Consolidation

| Benefit | Impact |
|---------|--------|
| **No Code Duplication** | Single upload service vs 2 separate implementations |
| **Consistent Security** | One security layer for both features |
| **Reduced Maintenance** | Single codebase to update |
| **Faster Time to Market** | Implement once, use twice |
| **Better Testing** | Centralized test suite |
| **Scalability** | Single service to optimize |

**Estimated Savings**: ~3-4 weeks of development time

---

## 🎯 Implementation Sequence

### Phase 1: Shared Infrastructure (2 weeks)
1. ✅ **Week 1**: Storage backend + multipart upload (US#265, US#266)
2. ✅ **Week 2**: Security layer + testing

### Phase 2: SPEC-032 Endpoints (1 week)
3. ✅ **Week 3**: Attachment API endpoints (US#267)

### Phase 3: SPEC-077 Endpoints (1.5 weeks)
4. ✅ **Week 4-5**: Multimodal capture + AI integration (US#268)

**Total Timeline**: 4-5 weeks (single developer)
**Parallel Option**: 3 weeks (2 developers split Phase 2 & 3)

---

## ⚠️ Risks & Mitigation

| Risk | Mitigation |
|------|------------|
| **Storage costs** | Implement lifecycle policies, compression |
| **Large file uploads** | Chunked/resumable uploads, client-side compression |
| **Processing delays** | Async processing queue, status endpoints |
| **Security vulnerabilities** | Regular ClamAV updates, input validation |
| **ACL complexity** | Reuse SPEC-043 patterns, comprehensive tests |

---

## 🔗 Related SPECs

- **SPEC-001**: Core Memory System (foundation)
- **SPEC-008**: Security Middleware (file upload security)
- **SPEC-043**: Access Control ACL (attachment visibility)
- **SPEC-070**: Real-Time Dashboard (upload progress)

---

## 📊 Success Metrics

### Technical
- ✅ Upload success rate: >99%
- ✅ P95 upload latency: <2s for files <10MB
- ✅ Virus detection: 100% of known threats
- ✅ Zero security incidents

### Business
- ✅ Enable SPEC-032 (Memory Attachments)
- ✅ Enable SPEC-077 (Multimodal Capture)
- ✅ Consistent user experience across features
- ✅ Foundation for future file-based features

---

## ✅ Recommendations

### Immediate Actions
1. ✅ **Create EPIC#022** in Taiga
2. ✅ **Create Stories US#265-268** in Taiga
3. ⚠️ **Assign to Developer A or B** (experienced with file uploads)
4. ⚠️ **Start with US#265** (storage backend foundation)

### Before Starting Development
- Review S3/MinIO setup in current infrastructure
- Confirm MIME type whitelist with security team
- Verify AI transcription API availability (for SPEC-077)
- Test large file upload in dev environment

---

## 📁 Documentation

- **SPEC-032 README**: `specs/032-memory-attachments/README.md`
- **SPEC-077 README**: `specs/077-multimodal-memory-capture/README.md`
- **This Analysis**: `governance/reports/SPEC_032_077_ANALYSIS.md`

---

**Analysis Completed**: November 1, 2025
**Next Review**: When EPIC#022 starts (sprint planning)
**Analyst**: Architecture Team
