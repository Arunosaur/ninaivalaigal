# DOCUMENTATION DISCIPLINE FRAMEWORK

**Purpose**: Prevent future documentation chaos and maintain clean organization

## 📏 **DOCUMENTATION RULES**

### **Rule 1: One Source of Truth**
- Each topic has **ONE authoritative document**
- No duplicate information across files
- Link to authoritative source, don't copy content

### **Rule 2: SPEC-First Development**
- All new features must have a SPEC **before** implementation
- Implementation reports go in `IMPLEMENTATION_REPORTS_2024.md`
- No mixing SPEC tracking with implementation details

### **Rule 3: File Creation Approval**
- New `.md` files require justification
- Must fit into existing structure or propose reorganization
- Temporary files must have expiration dates

### **Rule 4: Archive Immediately**
- Completed implementation reports → archive after 30 days
- Temporary analysis → archive after project completion
- Historical documents → move to appropriate archive directory

## 🗂️ **APPROVED DOCUMENTATION STRUCTURE**

### **Root Level (7 files maximum)**
```
├── README.md                    # Main project overview
├── SPEC_AUDIT_2024.md          # SPEC tracking system
├── CHANGELOG.md                 # Version history
├── CONTRIBUTING.md              # Contribution guidelines
├── SECURITY.md                  # Security policies
├── DOCUMENTATION_DISCIPLINE.md  # This file
└── MASSIVE_DOCS_CLEANUP_PLAN.md # Cleanup reference
```

### **docs/ Directory (10 files maximum)**
```
docs/
├── README.md                           # Documentation index
├── COMMAND_REFERENCE.md               # Command documentation
├── IMPLEMENTATION_REPORTS_2024.md     # Current achievements
├── NINA_INTELLIGENCE_STACK_COMPLETE.md # Platform guide
├── PROPOSED_NEW_SPECS.md              # Future SPECs
├── DOCUMENTATION_CLEANUP_PLAN.md      # Cleanup strategy
└── MASTER_ARCHIVE/                    # All archived content
```

### **specs/ Directory (73 directories)**
```
specs/
├── 000-template/README.md              # Each SPEC has ONLY README.md
├── 001-core-memory-system/README.md    # Implementation details in archive/
├── ...
└── 072-apple-container-cli/README.md
```

## 🚨 **ENFORCEMENT MECHANISMS**

### **Pre-commit Hooks**
```bash
# Check for documentation violations
scripts/check-docs-discipline.sh
```

### **Monthly Reviews**
- Count total `.md` files (target: <120)
- Identify files for archival
- Review SPEC vs implementation separation

### **New File Checklist**
Before creating any `.md` file:
1. ❓ Does this information belong in an existing file?
2. ❓ Is this a SPEC (goes in specs/) or implementation (goes in reports)?
3. ❓ Is this temporary (needs expiration date)?
4. ❓ Does this fit the approved structure?

## 📊 **SUCCESS METRICS**

### **Target Metrics**
- **Total .md files**: <120 (currently 118)
- **docs/ files**: <10 (currently 6)
- **SPEC files**: 73 README.md only
- **Archive growth**: <5 files per month

### **Warning Signs**
- 🚨 Total files >150
- 🚨 Multiple files covering same topic
- 🚨 Implementation details in SPEC files
- 🚨 Temporary files >30 days old

## 🔧 **TOOLS & AUTOMATION**

### **Documentation Monitoring Script**
```bash
#!/bin/bash
# scripts/monitor-docs.sh
total_md=$(find . -name "*.md" -not -path "*/node_modules/*" | wc -l)
if [ "$total_md" -gt 150 ]; then
    echo "⚠️  Documentation threshold exceeded: $total_md files"
    echo "Run cleanup review immediately"
fi
```

### **Monthly Cleanup Automation**
```bash
# scripts/monthly-cleanup.sh
# Move old implementation reports to archive
# Identify duplicate content
# Generate documentation health report
```

This framework ensures we **never return to 368 files** and maintain the clean, professional organization we've achieved.
