# Ninaivalaigal Compliance Pack

**Version 1.0 | Created: October 2025**

This compliance pack contains all the governance documents needed to maintain legal and operational compliance for the Ninaivalaigal open-core project.

---

## 📦 What's Included

### 1. **TRADEMARK.md**
**Purpose**: Usage guidelines for Ninaivalaigal and Medhasys trademarks

**Use this when**:
- Someone wants to use "Ninaivalaigal" in a product name
- Creating marketing materials that reference our brands
- Developing community resources
- Reporting trademark violations

**Key sections**:
- Permitted vs prohibited uses
- Logo usage policy
- Community resource guidelines
- Reporting misuse

---

### 2. **CONTRIBUTOR_LICENSE_AGREEMENT.md**
**Purpose**: Legal framework for accepting code contributions

**Use this when**:
- Onboarding new contributors
- Accepting pull requests
- Protecting IP rights
- Determining which CLA tier applies

**Key features**:
- Two-tier CLA (Public vs Proprietary)
- Clear IP ownership rules
- Patent grant clauses
- Employer ownership handling

---

### 3. **SPDX-header-inserter.py**
**Purpose**: Automated tool to add license headers to source files

**Use this when**:
- Adding new source files
- Quarterly compliance audits
- CI/CD license checks
- Converting to new licensing model

**Features**:
- Auto-detects license based on file location
- Supports Python, TypeScript, JavaScript, Shell, YAML
- Dry-run mode for safety
- CI integration ready

**Usage**:
```bash
# Dry run
python3 SPDX-header-inserter.py --dry-run

# Apply headers
python3 SPDX-header-inserter.py

# Check compliance (CI)
python3 SPDX-header-inserter.py --check
```

---

### 4. **COMPLIANCE.md**
**Purpose**: Comprehensive guide for license compliance management

**Use this when**:
- Running dependency audits
- Quarterly compliance reviews
- Adding new dependencies
- Responding to compliance issues

**Key sections**:
- Dependency license compatibility
- Automated audit procedures
- SPDX header requirements
- CI/CD integration
- Exception request process

---

### 5. **ENFORCEMENT_POLICY.md**
**Purpose**: How we detect and respond to license violations

**Use this when**:
- Responding to violation reports
- Determining enforcement actions
- Setting up monitoring systems
- Explaining our approach to violators

**Key sections**:
- Violation tier system
- Detection methods
- Response procedures (4 stages)
- Compliance pathways
- Transparency reporting

---

### 6. **LICENSE_FAQ.md**
**Purpose**: Answers to common licensing questions

**Use this when**:
- Onboarding community members
- Responding to "Can I...?" questions
- Explaining open-core model
- Clarifying commercial vs free use

**Key topics**:
- General licensing questions
- Specific use cases
- Contribution guidelines
- Commercial licensing
- Trademark use

---

## 🚀 Quick Start

### For Development Teams

**Initial Setup** (one-time):
```bash
# 1. Add SPDX headers to all files
python3 SPDX-header-inserter.py

# 2. Set up pre-commit hook
cat >> .git/hooks/pre-commit << 'EOF'
#!/bin/bash
python3 SPDX-header-inserter.py --check
if [ $? -ne 0 ]; then
  echo "Error: Some files missing SPDX headers"
  echo "Run: python3 SPDX-header-inserter.py"
  exit 1
fi
EOF
chmod +x .git/hooks/pre-commit

# 3. Run initial compliance audit
pip install pip-licenses
pip-licenses > compliance/initial-audit.txt
cd frontend-nextjs-customer
npx license-checker --summary > ../compliance/frontend-audit.txt
```

**Ongoing Maintenance** (quarterly):
```bash
# 1. Update dependencies audit
pip-licenses --format=markdown > compliance/dep-licenses-$(date +%Y-Q%q).md

# 2. Check for GPL contamination
pip-licenses | grep -iE "GPL|AGPL" && echo "⚠️ GPL found!"

# 3. Verify SPDX headers
python3 SPDX-header-inserter.py --check

# 4. Archive audit results
mkdir -p compliance/audits/$(date +%Y-Q%q)
cp compliance/*.md compliance/audits/$(date +%Y-Q%q)/
```

---

### For Community Managers

**Responding to Questions**:
1. Check [LICENSE_FAQ.md](LICENSE_FAQ.md) first
2. If not covered, consult LICENSE-MATRIX.md
3. For complex cases, escalate to legal@medhasys.com

**Accepting Contributions**:
1. Ensure contributor has signed CLA
2. Verify correct tier (Public vs Proprietary)
3. Check files don't mix licensed code
4. Approve PR only after CLA confirmation

**Handling Violations**:
1. Verify violation using [ENFORCEMENT_POLICY.md](ENFORCEMENT_POLICY.md)
2. Determine tier (1/2/3)
3. Follow prescribed response procedure
4. Escalate if needed

---

### For Legal Teams

**Commercial License Requests**:
1. Review use case (SaaS vs self-hosted vs OEM)
2. Determine pricing tier (see internal pricing guide)
3. Draft license agreement
4. Execute and file

**Violation Responses**:
1. Assess severity using ENFORCEMENT_POLICY.md
2. Draft appropriate response (email vs formal notice vs C&D)
3. Send via certified mail + email
4. Track in violation log
5. Monitor for compliance

**Quarterly Reviews**:
1. Review enforcement log
2. Update policies if needed
3. Check for policy violations internally
4. Report to stakeholders

---

## 📋 Integration Checklist

### CI/CD Integration

Add to `.github/workflows/compliance.yml`:
```yaml
name: License Compliance

on: [push, pull_request]

jobs:
  spdx-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Check SPDX Headers
        run: python3 SPDX-header-inserter.py --check

  dependency-audit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Check Python Dependencies
        run: |
          pip install pip-licenses
          pip-licenses | grep -iE "GPL|AGPL" && exit 1 || exit 0
```

### Pre-commit Hooks

Add to `.pre-commit-config.yaml`:
```yaml
repos:
  - repo: local
    hooks:
      - id: spdx-headers
        name: SPDX Header Check
        entry: python3 SPDX-header-inserter.py --check
        language: system
        pass_filenames: false
```

### Make Targets

Add to `Makefile`:
```makefile
# Compliance targets
.PHONY: compliance-check compliance-audit compliance-fix

compliance-check:
	python3 SPDX-header-inserter.py --check

compliance-audit:
	pip-licenses --format=markdown > compliance/audit-$(shell date +%Y%m%d).md
	cd frontend-nextjs-customer && npx license-checker --summary

compliance-fix:
	python3 SPDX-header-inserter.py
```

---

## 🔄 Maintenance Schedule

### Weekly
- [ ] Check for new violation reports
- [ ] Respond to licensing questions

### Monthly
- [ ] Review new dependencies
- [ ] Update FAQ if new questions arise
- [ ] Check for trademark violations (Google Alerts)

### Quarterly
- [ ] Run full dependency audit
- [ ] Verify all SPDX headers present
- [ ] Update NOTICE file if needed
- [ ] Review enforcement log
- [ ] Archive compliance reports

### Annually
- [ ] Legal review of all policy documents
- [ ] Update copyright years
- [ ] Publish transparency report
- [ ] Review and renew trademarks

---

## 📞 Contact Information

### General Questions
- **Email**: compliance@medhasys.com
- **GitHub**: https://github.com/Arunosaur/ninaivalaigal/discussions

### Legal Matters
- **Email**: legal@medhasys.com
- **Phone**: +1-XXX-XXX-XXXX

### Trademark Issues
- **Email**: trademark@medhasys.com

### Violation Reports
- **Email**: violations@medhasys.com
- **Urgent**: Call legal team

---

## 📚 Related Documents

- **LICENSE** - Root license file explaining open-core model
- **LICENSE-MATRIX.md** - Component-by-component license breakdown
- **CONTRIBUTING.md** - General contribution guidelines
- **SECURITY.md** - Security policy (separate from licensing)

---

## 🔐 Document Versioning

All compliance documents use semantic versioning:

- **Major version** (1.x): Significant policy changes requiring re-review
- **Minor version** (x.1): Clarifications or additions
- **Patch version** (x.x.1): Typo fixes or formatting

**Version History**:
- v1.0 (Oct 2025): Initial release

**Change Notifications**:
- Major: Email all stakeholders + blog post
- Minor: GitHub Discussions announcement
- Patch: Git commit message only

---

## ⚖️ Legal Status

These documents represent Medhasys LLC's policies and are:
- ✅ Legally reviewed (as of creation date)
- ✅ Enforceable under contract law
- ✅ Subject to change with notice

**Not a substitute for legal advice.** Consult an attorney for your specific situation.

---

## 🤝 Contributing to This Pack

Found an error or have a suggestion?

1. **For typos/clarifications**:
   - Submit PR against this repo
   - Tag with `compliance` label

2. **For policy changes**:
   - Open GitHub Discussion first
   - Tag legal team for review
   - Changes require legal approval

3. **For new documents**:
   - Propose via GitHub Issue
   - Explain use case and value
   - Await legal review

---

**Version**: 1.0
**Last Updated**: October 2025
**Maintained by**: Medhasys LLC Legal, Engineering, and Community Teams

**SPDX-License-Identifier**: CC-BY-4.0 (this README only)

© 2025 Medhasys LLC. All rights reserved.
