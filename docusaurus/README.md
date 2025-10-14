# Ninaivalaigal Documentation

**Build with:** Generic Docs Builder Container  
**Location:** `~/WorkSpace/dev-containers/docs-builder`

---

## 🚀 **Quick Start**

### **Option 1: Using Container (Recommended)**

```bash
# Build container (one-time)
cd ~/WorkSpace/dev-containers/docs-builder
./build-arm64.sh

# Start docs server
./start-docs-builder.sh /Users/swami/WorkSpace/ninaivalaigal

# Access at http://localhost:3000
```

### **Option 2: Local npm (if needed)**

```bash
cd docusaurus
npm install
npm start
```

---

## 📁 **Structure**

```
docusaurus/
├── docusaurus.config.js   # Main config
├── sidebars.js             # Sidebar auto-generation
├── package.json            # Dependencies (for local use only)
├── docs/
│   └── specs/              # Symlink to /specs (auto-generated)
└── static/
    └── spec_index.json     # Auto-generated SPEC index
```

---

## 🛠️ **Container Benefits**

- ✅ **No local Node.js** installation required
- ✅ **Version-locked** dependencies
- ✅ **Reusable** across all Medhasys projects
- ✅ **ARM64 optimized** for Apple Silicon

---

## 📊 **SPEC Integration**

The container automatically:
1. Mounts `/specs` as read-only
2. Indexes all SPEC front-matter
3. Generates searchable documentation
4. Creates dependency graphs

See: `~/WorkSpace/dev-containers/docs-builder/README.md`
