# 🛠️ External Tools Reference

This document lists tools that are **shared across projects** and stored outside this repository.

---

## 📦 **Generic Development Containers**

### **Location:** `~/WorkSpace/dev-containers/`

#### **1. Docs Builder**
- **Path:** `~/WorkSpace/dev-containers/docs-builder/`
- **Purpose:** Docusaurus + MkDocs documentation builder
- **Runtime:** Apple Container CLI (Podman)
- **Platform:** ARM64 native
- **Used by:** Ninaivalaigal, Medhasys, any project

**Usage:**
```bash
cd ~/WorkSpace/dev-containers/docs-builder
./start-docs-builder.sh /Users/swami/WorkSpace/ninaivalaigal
```

**Documentation:** See `~/WorkSpace/dev-containers/docs-builder/README.md`

---

## 🧠 **Obsidian Vault**

### **Location:** `~/WorkSpace/ninaivalaigal/` (project root)

**Why here?** Obsidian needs direct filesystem access to the repo for:
- Reading `/specs` directory
- Dataview queries
- Graph view
- Cross-linking

**Configuration:** `.obsidian/` (in this repo)

---

## 📊 **Tool Organization Strategy**

| Tool | Location | Reason |
|------|----------|--------|
| **Docs Builder** | `~/WorkSpace/dev-containers/` | Reusable across projects |
| **Obsidian** | Project root | Needs repo access |
| **SPEC Kit CLI** | `~/WorkSpace/dev-tools/` (future) | Reusable CLI tool |
| **Graph Visualizers** | `~/WorkSpace/dev-tools/` (future) | Reusable utilities |

---

## 🎯 **Benefits**

- ✅ **Clean project repos** - only project-specific files
- ✅ **Reusable tools** - one installation, all projects
- ✅ **Version control** - containers don't pollute git history
- ✅ **Easy updates** - update tool once, affects all projects

---

## 📊 **SPEC Dashboard Generator**

### **Location:** `~/WorkSpace/dev-tools/spec-dashboard-generator/`

**Purpose:** Generate JSON analytics from SPEC front-matter  
**Output:** `spec_dashboard.json` with phase completion, timeline, Gantt data  
**Used by:** Docusaurus visualization components

**Usage:**
```bash
cd ~/WorkSpace/dev-tools/spec-dashboard-generator
./generate.sh /Users/swami/WorkSpace/ninaivalaigal
```

**Features:**
- ✅ Phase completion percentages
- ✅ Status breakdown (Draft, Complete, etc.)
- ✅ Owner statistics
- ✅ Timeline data for progress charts
- ✅ Gantt-ready start/end dates
- ✅ Latest SPEC updates tracking

**Documentation:** See `~/WorkSpace/dev-tools/spec-dashboard-generator/README.md`

---

## 🚀 **Future Generic Tools**

Candidates for `~/WorkSpace/dev-tools/` or `~/WorkSpace/dev-containers/`:

1. **SPEC Kit CLI** - YAML front-matter generator & validator
2. **Graph Visualizer** - D3.js/Graphviz for SPEC dependencies
3. **API Docs Generator** - OpenAPI → Markdown
4. **Test Report Dashboard** - Pytest/Playwright results viewer

---

**Last Updated:** October 13, 2025  
**Organization:** Medhasys
