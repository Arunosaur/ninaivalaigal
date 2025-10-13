# Technical Debt Documentation Index

**Last Updated**: October 11, 2025
**Folder Purpose**: Centralized tracking of technical debt, code quality issues, and remediation plans

---

## 📋 **Documentation Structure**

### **1. README.md** (Main Tracker)
**Purpose**: Current technical debt log and active issues
**Created**: October 11, 2025
**Status**: ✅ Active

**Contents**:
- TD-001: Flake8 violations (30 issues, 19 files)
- TD-002: GPL v3 contamination (PyQt investigation)
- TD-003: UNLICENSED JavaScript packages
- Remediation plans and timelines
- Quarterly review schedule
- Technical debt metrics

**Use This For**: Current active technical debt tracking

---

### **2. historical-debt.md**
**Purpose**: Historical technical debt from previous sprints
**Origin**: Previously `docs/TECHNICAL_DEBT.md`
**Status**: 📚 Historical reference

**Contents**:
- Older technical debt items that have been resolved
- Historical context for past decisions
- Patterns and lessons learned

**Use This For**: Understanding past technical debt and resolution patterns

---

### **3. progress.md**
**Purpose**: Track resolution progress on technical debt items
**Origin**: Previously `docs/TECHNICAL_DEBT_PROGRESS.md`
**Status**: 📊 Progress tracking

**Contents**:
- Status updates on debt resolution
- Completion metrics
- Timeline tracking
- Blockers and dependencies

**Use This For**: Monitoring debt resolution progress

---

### **4. session-summary.md**
**Purpose**: Session-by-session summary of debt work
**Origin**: Previously `docs/TECHNICAL_DEBT_SESSION_SUMMARY.md`
**Status**: 📝 Session notes

**Contents**:
- Daily/weekly debt resolution sessions
- What was fixed in each session
- Effort estimates vs. actual
- Learnings and insights

**Use This For**: Detailed session-level tracking

---

### **5. fix-plan.md**
**Purpose**: Strategic plans for fixing technical debt
**Origin**: Previously `docs/TECHNICAL_DEBT_FIX_PLAN.md`
**Status**: 🗺️ Planning document

**Contents**:
- Debt resolution strategies
- Prioritization framework
- Resource allocation
- Risk mitigation plans

**Use This For**: Planning debt resolution sprints

---

## 🔄 **Workflow**

### **Adding New Technical Debt**:
1. Document in `README.md` with TD-XXX identifier
2. Add to appropriate priority section (High/Medium/Low)
3. Include remediation plan and timeline
4. Assign owner if known

### **Tracking Progress**:
1. Update `progress.md` with status changes
2. Log detailed work in `session-summary.md`
3. Move completed items to "Resolved" section in `README.md`

### **Planning Debt Resolution**:
1. Review `README.md` for active items
2. Create resolution plan in `fix-plan.md`
3. Estimate effort and allocate resources
4. Execute and track in `progress.md`

---

## 📊 **Current Metrics**

**Total Active Debt Items**: 3 (TD-001, TD-002, TD-003)
**High Priority**: 2 (TD-001, TD-002)
**Medium Priority**: 1 (TD-003)
**Estimated Total Effort**: 4-7 hours

**By Category**:
- Code Quality: 1 (TD-001)
- License Compliance: 2 (TD-002, TD-003)

---

## 📅 **Review Schedule**

- **Weekly**: Review new debt items, update status
- **Monthly**: Review and prioritize debt backlog
- **Quarterly**: Major cleanup sprint for accumulated debt

**Next Reviews**:
- TD-001 (Flake8): Sprint 2025-Q4
- TD-002 (GPL): November 1, 2025
- TD-003 (UNLICENSED): Sprint 2025-Q4

---

## 🎯 **Goals**

**Q4 2025 Target**: Resolve all High priority items
**2025 End Target**: Zero High priority debt
**Continuous Target**: Keep debt below 10 items total

---

## 📚 **Related Documentation**

- `../COMPLIANCE_ADDONS_README.md` - Compliance infrastructure overview
- `../compliance/exceptions.md` - License exception tracking
- `../NOTICE.md` - Third-party attributions
- `../.pre-commit-config.yaml` - Automated quality checks

---

## 📧 **Contacts**

**Technical Debt Owner**: Engineering Team
**Review Authority**: CTO + Engineering Lead
**Questions**: engineering@medhasys.com

---

**Folder Maintained By**: Engineering Team
**Last Audit**: October 11, 2025
**Next Audit**: November 11, 2025
