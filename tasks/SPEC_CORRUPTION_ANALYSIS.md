# SPEC Corruption Analysis - URGENT

**Time:** October 13, 2025, 7:50 PM  
**Severity:** 🚨 **CRITICAL - Data Loss Detected**

---

## 🔥 **Problem: Not Duplication - It's CORRUPTION**

When Developer B added Docusaurus front-matter to SPECs, **content was deleted** from some files!

---

## 📊 **Damage Assessment**

### **CORRUPTED FILES (Content Lost):**

#### **1. specs/087-api-surface-contracts/README.md**
**Lost Content:**
- Title: "SPEC-087: API Surface Contracts (Public vs Internal OpenAPI)"
- Status, Owner, Related SPECs metadata
- Section 1: Purpose (entire section)
- Part of Section 2: Goals

**Current State:** Only has front-matter + partial content (279 lines → ~250 lines)

**Git History:** Content existed in commit `cd65ead6`

---

#### **2. specs/128-memory-sharing/README.md**
**Lost Content:**
- Title section
- Purpose/Status metadata
- Section 1: Purpose  

**Current State:** Missing first ~10 lines of content

**Git History:** Was specs/088-memory-sharing, renamed to 128

---

### **PLACEHOLDER FILES (Empty, Should Delete):**

#### **3. specs/100-api-surface-contracts/**
- 25 lines of empty placeholder
- Created in commit `c8280b99` but never filled in
- Conflicts with real SPEC-087

#### **4. specs/099-approval-chain-processing/**
- 29 lines of empty placeholder  
- Conflicts with real SPEC-090

#### **5. specs/101-memory-sharing/**
- 27 lines of empty placeholder
- Conflicts with real SPEC-128

---

## 🔍 **Root Cause**

### **What Happened:**

1. **October 8-9:** Developer B working on Docusaurus dashboard
2. **Task:** Add front-matter to all SPEC files for Docusaurus
3. **Process:** Probably used find/replace or script
4. **Mistake:** Script/manual edit **replaced** content instead of **prepending**

### **Evidence:**

```bash
# Before (git cd65ead6):
# SPEC-087: API Surface Contracts (Public vs Internal OpenAPI)
**Status:** 🔄 PARTIAL
...

# After (current):
---
id: spec-087-api-surface-contracts
...
---

## 2) Goals  # ← Section 1 missing!
```

### **Why It Wasn't Noticed:**

- File still has 279 lines (seems complete)
- Front-matter looks professional
- Content "looks okay" at first glance
- No one reviewed the full diff

---

## ✅ **Recovery Plan**

### **Step 1: Restore Corrupted Files**

```bash
# Restore SPEC-087 from git
git show cd65ead6:specs/087-api-surface-contracts/README.md > specs/087-api-surface-contracts/README.md.recovered

# Check if it's good
diff <(git show cd65ead6:specs/087-api-surface-contracts/README.md) specs/087-api-surface-contracts/README.md.recovered

# If good, restore
mv specs/087-api-surface-contracts/README.md.recovered specs/087-api-surface-contracts/README.md

# Add front-matter correctly (prepend, don't replace)
```

**For SPEC-128:** Need to find where it was before renaming (was 088)

---

### **Step 2: Delete Empty Placeholders**

```bash
# These are empty and conflict with real SPECs
rm -rf specs/100-api-surface-contracts
rm -rf specs/099-approval-chain-processing  
rm -rf specs/101-memory-sharing
```

---

### **Step 3: Add Front-Matter Correctly**

Create script to **prepend** front-matter without destroying content:

```bash
#!/bin/bash
# add_frontmatter_safely.sh

for spec_dir in specs/[0-9]*; do
    readme="$spec_dir/README.md"
    if [ ! -f "$readme" ]; then continue; fi
    
    # Skip if already has front-matter
    if head -1 "$readme" | grep -q "^---$"; then
        echo "✅ $spec_dir already has front-matter"
        continue
    fi
    
    # Extract SPEC number and slug
    spec_num=$(basename "$spec_dir" | sed 's/-.*//')
    slug=$(basename "$spec_dir")
    
    # Create temp file with front-matter + original content
    {
        echo "---"
        echo "id: spec-$spec_num-$(echo $slug | sed 's/^[0-9]*-//')"
        echo "slug: /specs/$slug"
        echo "---"
        echo ""
        cat "$readme"
    } > "$readme.tmp"
    
    # Replace only if different
    if ! diff -q "$readme" "$readme.tmp" > /dev/null; then
        mv "$readme.tmp" "$readme"
        echo "✅ Added front-matter to $spec_dir"
    else
        rm "$readme.tmp"
    fi
done
```

---

## 📋 **Complete Recovery Script**

```bash
#!/bin/bash
# recover_corrupted_specs.sh

set -e

echo "🔧 Recovering corrupted SPECs..."
echo ""

# Step 1: Restore SPEC-087
echo "📋 Restoring SPEC-087..."
git show cd65ead6:specs/087-api-surface-contracts/README.md > specs/087-api-surface-contracts/README.md
echo "  ✅ SPEC-087 restored from commit cd65ead6"

# Step 2: Find and restore SPEC-128 (was 088)
echo "📋 Finding original SPEC-128 (was 088)..."
if git show cd65ead6:specs/088-memory-sharing/README.md > /dev/null 2>&1; then
    git show cd65ead6:specs/088-memory-sharing/README.md > specs/128-memory-sharing/README.md
    echo "  ✅ SPEC-128 restored from 088-memory-sharing"
else
    echo "  ⚠️  Could not find original 088-memory-sharing"
fi

# Step 3: Remove placeholder duplicates
echo "📋 Removing empty placeholder specs..."
rm -rf specs/100-api-surface-contracts
echo "  ✅ Removed specs/100-api-surface-contracts"
rm -rf specs/099-approval-chain-processing
echo "  ✅ Removed specs/099-approval-chain-processing"
rm -rf specs/101-memory-sharing
echo "  ✅ Removed specs/101-memory-sharing"

echo ""
echo "✅ Recovery complete!"
echo ""
echo "Next steps:"
echo "1. Review restored files"
echo "2. Run add_frontmatter_safely.sh to add front-matter correctly"
echo "3. Test docusaurus: cd docusaurus && npm start"
echo "4. Commit: git add -A && git commit -m 'fix: restore corrupted SPECs and remove duplicates'"
```

---

## 🎯 **Lessons Learned**

### **What Went Wrong:**
1. ❌ Automated script replaced content instead of prepending
2. ❌ No review/diff check before committing
3. ❌ Didn't test docusaurus after changes
4. ❌ No backup before mass file operations

### **Prevention:**
1. ✅ **Always review diffs** before committing mass changes
2. ✅ **Test prepend scripts** on 1-2 files first
3. ✅ **Create backup branch** before mass operations
4. ✅ **Run docusaurus build** to catch errors early

---

## ⏱️ **Impact**

**Time Lost:** 
- Developer B: ~4 hours debugging docusaurus
- You: ~1 hour investigating  
- Total: ~5 hours

**Data At Risk:**
- 2 SPECs corrupted (087, 128)
- Content recoverable from git ✅
- 3 empty placeholders created

**No permanent data loss if we restore now!**

---

## 🚀 **Immediate Action**

**DO NOT run cleanup_now.sh yet!**

**Instead:**
1. Run recovery script (provided above)
2. Verify restored content
3. Delete empty placeholders
4. Add front-matter safely
5. THEN do root cleanup

**Estimated time:** 15 minutes

---

**Status:** 🔴 **URGENT - Needs immediate recovery**  
**Priority:** Fix this BEFORE root cleanup  
**Risk:** Low (recoverable from git)
