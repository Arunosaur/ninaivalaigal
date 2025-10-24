# Tasks Folder Organization Guide

**Last Updated:** October 21, 2025

---

## 📁 Folder Structure

```
tasks/
├── active/           # Current, in-progress task documents
├── completed/        # Finished task documents (archived when done)
├── archive/          # Old/historical tasks
├── reports/          # Milestone reports and completion summaries
├── docs/             # Task-specific guides and documentation
└── README.md         # This guide
```

---

## ✅ What Goes Where

### `tasks/active/`
**Purpose:** Current, in-progress work

**Examples:**
- `US79_PHASE3_STATUS.md` - Active user story status
- `DEVELOPER_A_NEXT_STEPS_OCT21.md` - Current developer tasks
- `SPRINT_OVERVIEW.md` - Current sprint tracking

**Move to `completed/` when:** Task is finished

---

### `tasks/reports/`
**Purpose:** Milestone reports, completion summaries

**Examples:**
- `US79_PHASE3_CORE_API_COMPLETE.md` - Milestone completion report
- `SPRINT_XX_SUMMARY.md` - Sprint retrospective
- `PERFORMANCE_SUMMARY.md` - Benchmark results

**Keep:** Permanently for reference

---

### `tasks/docs/`
**Purpose:** Task-specific guides that are temporary

**Examples:**
- Developer-specific setup guides
- One-off investigation reports
- Task-specific HOWTOs

**Different from `docs/`:** These are temporary or task-specific, not permanent architecture docs

---

### `tasks/completed/`
**Purpose:** Finished tasks (before archiving)

**Lifecycle:**
1. Start in `active/`
2. Move to `completed/` when done
3. Move to `archive/` after sprint/milestone

---

### `tasks/archive/`
**Purpose:** Historical tasks (old sprints, completed phases)

**Retention:** Keep for historical reference, but not actively used

---

## 🚫 What DOESN'T Go in tasks/

**These belong in `docs/`:**
- Permanent architecture guides
- API reference documentation
- System design documents
- Contributing guides
- Security policies
- Testing strategies (permanent)

**Golden Rule:**
- **Task-specific** → `tasks/`
- **Permanent/Reference** → `docs/`

---

## 📝 Naming Conventions

### Active Tasks
```
USXX_<description>.md          # User story tracking
DEVELOPER_X_<topic>.md          # Developer-specific tasks
SPRINT_XX_<item>.md            # Sprint-specific items
```

### Reports
```
USXX_<milestone>_COMPLETE.md   # Completion reports
<SERVICE>_PERFORMANCE_SUMMARY.md # Performance reports
SPRINT_XX_RETROSPECTIVE.md     # Sprint summaries
```

---

## 🔄 Document Lifecycle

```
Creation → tasks/active/
    ↓
Completion → tasks/reports/ (if report) OR tasks/completed/ (if task)
    ↓
Sprint end → tasks/archive/ (completed tasks)
    ↓
Reference → stays in tasks/reports/ or deleted if obsolete
```

---

## ⚠️ Before Creating Any Document

**Ask yourself:**

1. **Is this task-specific or permanent?**
   - Task-specific → `tasks/`
   - Permanent → `docs/`

2. **Is this active work or a report?**
   - Active → `tasks/active/`
   - Report → `tasks/reports/`

3. **Does a similar document already exist?**
   - Update existing rather than creating new

4. **Will this be useful after the task completes?**
   - No → `tasks/completed/` → `tasks/archive/`
   - Yes → `tasks/reports/` or `docs/`

---

## 📊 Current Status (Oct 21, 2025)

**Moved from docs/ to tasks/:**
- ✅ DEVELOPER_A_SUGGESTIONS_OCT21.md → tasks/active/
- ✅ DEVELOPER_A_NEXT_STEPS_OCT21.md → tasks/active/
- ✅ US79_PHASE3_STATUS.md → tasks/active/
- ✅ US79_PHASE3_CORE_API_COMPLETE.md → tasks/reports/

**Kept in docs/ (permanent guides):**
- ✅ CONTRACT_INTEGRATION_GUIDE.md (permanent reference)

---

## 🎯 Organization Principles

1. **"Does it belong here?"** - Ask before creating
2. **Proper organization is key** - Don't clutter
3. **Update, don't duplicate** - Check existing docs first
4. **Lifecycle matters** - Move documents through states
5. **Clean as you go** - Archive completed work

---

**Remember:** Hours spent organizing now saves days later! 🚀
