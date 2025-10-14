# Developer B - SPEC Dashboard Cleanup Task

**Priority:** Medium  
**Estimated Time:** 4-6 hours  
**Status:** Not Started  
**Date Created:** October 13, 2025

---

## 🎯 **Objective**

Build a clean, production-ready SPEC dashboard system with **ONE source of truth** (the `/specs` directory).

---

## ⚠️ **Current Problem**

The current implementation has issues:
1. **Copying SPECs** from `/specs` to `/docusaurus/docs/specs` creates dual sources
2. **Build errors** from problematic SPEC files (templates, backups, etc.)
3. **Maintenance nightmare** - changes need to be synced between two locations
4. **Contamination risk** - docs showing different content than source

---

## ✅ **Requirements**

### **1. Single Source of Truth**
- All SPEC content must live ONLY in `/specs`
- Docusaurus must read directly from `/specs` (symlink or config)
- No copying, no duplication

### **2. Clean Build Process**
- Filter out problematic files automatically:
  - `000-template/` (contains template files)
  - `PHASE_SUMMARIES/` (date-named files)
  - `.backup-*/` (backup directories)
  - `templates/` (template directories)
  - `_external/` (external references)
  - `SPEC_INDEX.md` (use as data source, not doc)

### **3. YAML Front-Matter Validation**
- All SPECs must have valid YAML front-matter
- Dashboard generator should validate and report errors
- Provide script to add front-matter to SPECs missing it

### **4. Automated Updates**
- Dashboard regenerates automatically when SPECs change
- No manual intervention needed
- CI/CD integration

---

## 📐 **Proposed Architecture**

```
/specs/                           ← SINGLE SOURCE OF TRUTH
├── 000-vision-and-scope/
├── 088-api-versioning-strategy/
└── ...

/docusaurus/
├── docusaurus.config.js         ← Configure to read from /specs
├── static/
│   └── spec_dashboard.json      ← Auto-generated
└── src/
    └── components/              ← Dashboard visualizations
        ├── SpecDashboard.js
        ├── SpecTimeline.js
        └── SpecGanttTimeline.js
```

**Key Change:** Docusaurus reads from `/specs` via:
- **Option A:** Symlink (if supported)
- **Option B:** Custom plugin to filter and load from `/specs`
- **Option C:** Build step that creates filtered copy only at build time

---

## 📋 **Tasks**

### **Phase 1: Research & Design (1-2 hours)**
- [ ] Research Docusaurus configuration for custom doc paths
- [ ] Decide on symlink vs. plugin vs. build-step approach
- [ ] Document decision with pros/cons
- [ ] Create technical design document

### **Phase 2: YAML Front-Matter Audit (2-3 hours)**
- [ ] Scan all 130 SPECs for YAML front-matter
- [ ] Create list of SPECs missing front-matter
- [ ] Write script to add front-matter to SPECs:
  ```bash
  python3 add-frontmatter.py /path/to/spec
  ```
- [ ] Add front-matter to all SPECs (or at least 20 for demo)
- [ ] Validate all YAML syntax

### **Phase 3: Clean Docusaurus Configuration (1-2 hours)**
- [ ] Update `docusaurus.config.js` to read from `/specs`
- [ ] Configure file exclusions (templates, backups, etc.)
- [ ] Test with clean SPECs
- [ ] Verify no build errors
- [ ] Document configuration changes

### **Phase 4: Dashboard Generator Enhancement (1 hour)**
- [ ] Update generator to validate YAML before processing
- [ ] Add error reporting for invalid YAML
- [ ] Add summary statistics (e.g., "5 SPECs missing front-matter")
- [ ] Test with full SPEC directory

### **Phase 5: Testing & Documentation (1 hour)**
- [ ] Test full build process
- [ ] Verify dashboard loads correctly
- [ ] Update `HYBRID_SPEC_SYSTEM.md` with new architecture
- [ ] Create troubleshooting guide
- [ ] Write update instructions for future SPEC authors

---

## 🔧 **Implementation Options**

### **Option A: Symlink Approach**
```bash
cd docusaurus
ln -s ../specs docs/specs
```

**Pros:**
- Simple, no duplication
- Changes reflect immediately

**Cons:**
- May not work with all file systems
- Build tools might not follow symlinks
- No filtering of problematic files

### **Option B: Custom Docusaurus Plugin**
```javascript
// docusaurus.config.js
plugins: [
  [
    'custom-specs-loader',
    {
      specsPath: '../specs',
      exclude: ['000-template', 'PHASE_SUMMARIES', '.backup-*']
    }
  ]
]
```

**Pros:**
- Full control over filtering
- Can validate files before loading
- Professional solution

**Cons:**
- More complex to implement
- Requires understanding Docusaurus plugin API

### **Option C: Build-Time Copy with Filtering**
```javascript
// scripts/prepare-docs.js
const fs = require('fs');
const path = require('path');

function copySpecs() {
  // Copy /specs to /docs/specs
  // Exclude problematic files
  // Validate YAML during copy
}
```

**Pros:**
- Can clean/validate during copy
- Build-time only (no runtime overhead)
- Easy to understand

**Cons:**
- Still creates temporary duplication
- Needs to run before every build

---

## 📊 **Success Criteria**

- [ ] Dashboard builds without errors
- [ ] All visualizations working (dashboard, timeline, gantt)
- [ ] Only ONE source of SPEC content (`/specs`)
- [ ] At least 20 SPECs have YAML front-matter
- [ ] Documentation updated with new architecture
- [ ] CI/CD pipeline configured
- [ ] Zero duplication of SPEC content

---

## 🚨 **Out of Scope**

This task does NOT include:
- Adding front-matter to all 130 SPECs (just enough for demo)
- Container deployment (Docker/Podman)
- GitHub Pages setup
- Advanced features (dependency graphs, health scores)

---

## 📚 **Reference Materials**

### **Existing Work**
- `~/WorkSpace/dev-tools/spec-dashboard-generator/` - Dashboard generator
- `HYBRID_SPEC_SYSTEM.md` - Current architecture doc
- `spec-kit.config.yaml` - Configuration file

### **Docusaurus Docs**
- https://docusaurus.io/docs/configuration
- https://docusaurus.io/docs/api/plugins/@docusaurus/plugin-content-docs

### **YAML Front-Matter Spec**
- https://jekyllrb.com/docs/front-matter/
- https://docusaurus.io/docs/markdown-features#front-matter

---

## 🎯 **Deliverables**

When complete, provide:

1. **Technical Design Doc** - Chosen approach with justification
2. **Updated Docusaurus Config** - Clean, working configuration
3. **YAML Front-Matter Script** - Tool to add front-matter to SPECs
4. **Updated Architecture Doc** - `HYBRID_SPEC_SYSTEM.md` v2
5. **Demo** - Working dashboard with 20+ SPECs
6. **Documentation** - Setup guide and troubleshooting

---

## 💡 **Tips**

1. **Start small** - Get 5 SPECs working perfectly first
2. **Test incrementally** - Don't wait until all 130 SPECs are ready
3. **Document as you go** - Capture decisions and rationale
4. **Ask questions** - If approach isn't working, pivot early
5. **Keep it simple** - Prefer simple working solution over complex perfect one

---

## ⏰ **Estimated Timeline**

| Phase | Time | Dependencies |
|-------|------|--------------|
| Research & Design | 1-2h | None |
| YAML Audit | 2-3h | None |
| Docusaurus Config | 1-2h | Phase 1 complete |
| Generator Enhancement | 1h | Phase 2 complete |
| Testing & Docs | 1h | All phases complete |
| **Total** | **6-9h** | - |

---

## 📝 **Notes**

- Current `/docusaurus/docs/specs/` should be **deleted** after cleanup
- Use `.gitignore` to ignore any build-time copies
- Consider adding YAML linting to pre-commit hooks
- Document the "why" not just the "how"

---

## 🤝 **Support**

If blocked:
1. Check existing Docusaurus issues on GitHub
2. Review similar projects (Gatsby, VuePress)
3. Ask for help in team channel
4. Document blockers for review

---

**Status:** 📋 Ready to Start  
**Priority:** Medium  
**Owner:** Developer B  
**Reviewer:** TBD

---

**Created:** October 13, 2025  
**Last Updated:** October 13, 2025
