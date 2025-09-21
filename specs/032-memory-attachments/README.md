# 📦 SPEC-032: Memory Attachment & Artifact Enrichment

## 🎯 Objective

Enable users to attach documents, code snippets, images, or videos to existing memory tokens for enriched recall, enhanced context, and deeper AI integration.

---

## ✅ Use Cases

- Attach grant documents, architectural diagrams, or meeting recordings to relevant memory tokens
- Enrich code review discussions with snippets and changelogs
- Link multimedia assets to planning meetings
- Enable AI to access both textual and non-textual memory inputs

---

## 📐 Data Model

### New Table: `memory_attachments`

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

## 🔧 API Endpoints

### `POST /memory/{memory_id}/attachments`

- Upload and attach one or more files
- Supports `multipart/form-data`
- Fields:
  - `file`: uploaded file
  - `type`: optional override (`document`, `code`, etc.)

### `GET /memory/{memory_id}/attachments`

- List all attachments for a memory token
- Metadata + pre-signed URLs or viewer-ready previews

### `DELETE /attachments/{attachment_id}`

- Remove attachment (soft delete or revoke access)

---

## 💻 CLI Commands

```bash
eM attach --memory mem-abc123 --file notes.pdf --type document
eM attachments list --memory mem-abc123
eM attachments delete --attachment att-xyz456
```

---

## 🖥️ UI Support

- Attachment upload in memory edit/view page
- Show previews for supported types:
  - PDF → render preview
  - Images → thumbnail
  - Videos → embed player
  - Code → syntax highlight

---

## 🧠 MCP Integration

### During `POST /mcp/ask`:

- Include file summaries or inline snippets
- Allow memory score boost for entries with rich artifacts
- Option to inline parsed contents (OCR, PDF to text, etc.)

---

## 🔐 Security & Access Control

- Pre-signed URLs or token-auth gated downloads
- Enforce max file size, type restrictions
- Support scoped visibility (personal/team/org/public)

---

## 🚀 Stretch Goals

- OCR for image-based text extraction
- Auto-tagging and classification of uploaded files
- Version control for evolving artifacts

---

## 📦 Location

- Path: `specs/032-memory-attachments/`
- Status: 📋 PLANNED