# Taiga Workflow - Task Assignment & Tracking

**Effective:** Oct 16, 2025
**Status:** Active - All new tasks use Taiga

---

## 🎯 Quick Access

**Taiga URL:** http://localhost:9000/project/ninaivalaigal
**Login:** admin / admin123

---

## 📋 Task Assignment Workflow

### 1. **Creating New Tasks**

**In Taiga UI:**
```
1. Go to http://localhost:9000/project/ninaivalaigal
2. Click "+ New User Story" or "+ New Task"
3. Fill in:
   - Subject: Brief task description
   - Description: Detailed requirements
   - Epic: Link to SPEC (e.g., SPEC-093)
   - Tags: Add relevant tags (spec-093, rust, database, etc.)
   - Assigned to: Select developer
   - Status: New / Ready / In Progress / Done
4. Save
```

**Via API (for automation):**
```bash
# See taiga-import-tasks.py for examples
# Use TaigaImporter class methods
```

---

### 2. **Developer Assignments**

**Instead of:** `/tasks/active/DEVELOPER_A_*.md`
**Use:** Taiga's assignment feature

**Assign tasks:**
- Click task → "Assigned to" → Select developer
- Filter by assignee to see developer's workload
- Track progress in real-time

---

### 3. **SPEC Traceability**

**Every task links to a SPEC via Epics:**

| Epic ID | SPEC | Description |
|---------|------|-------------|
| #1 | SPEC-086 | Multi-Runtime Port Allocation |
| #2 | SPEC-093 | Memory Service Architecture (Rust) |
| #3 | SPEC-094 | Graph Service Architecture (Rust) |
| #4 | Core API | Core API Service (Python) |
| #5 | Taiga Integration | Docusaurus + Taiga |

**To view SPEC progress:**
```
1. Go to Epics view
2. Click on SPEC epic
3. See all linked tasks + progress
```

---

### 4. **Status Updates**

**Developers update their own tasks:**

```
1. Login to Taiga
2. Find your assigned tasks
3. Drag-and-drop between columns:
   - New
   - Ready
   - In Progress
   - Review/QA
   - Done
4. Add comments with updates
```

**No more editing markdown docs!**

---

## 🔄 Migration from Docs to Taiga

### What Stays in `/tasks/active/`
- ✅ **Sprint planning docs** (SPRINT_OVERVIEW.md)
- ✅ **Major milestones** (migration guides, summaries)
- ✅ **Onboarding docs** (README_TEAM_DOCS.md)

### What Moves to Taiga
- ✅ **Individual task assignments**
- ✅ **Task status tracking**
- ✅ **SPEC-linked work items**
- ✅ **Developer workload**

---

## 📊 Viewing Work

### By Developer
```
Filter: Assigned to → Developer A/B/C
See all their tasks across all SPECs
```

### By SPEC
```
View: Epics → Select SPEC-093
See all tasks for that specification
```

### By Status
```
View: Kanban/Scrum Board
Drag tasks between status columns
```

### Overall Progress
```
View: Dashboard
See burn-down charts, velocity, etc.
```

---

## 🔗 Integration with Docusaurus

**We have live integration!**

**In any MDX doc:**
```mdx
import TaigaTaskList from '@site/src/components/TaigaTaskList';

# Memory Service Development

<TaigaTaskList
  project="ninaivalaigal"
  epic="SPEC-093"
  showCompleted={false}
/>
```

**SPEC Traceability Component:**
```mdx
import SpecTraceability from '@site/src/components/SpecTraceability';

<SpecTraceability
  specId="SPEC-093"
  project="ninaivalaigal"
/>
```

**Pulls live data from Taiga!**

---

## 📝 Daily Workflow

### Developer Workflow
```bash
# Morning:
1. Check Taiga for assigned tasks
2. Move task to "In Progress"
3. Work on task

# During work:
4. Add comments/updates to task
5. Link commits/PRs in task description

# End of day:
6. Update task status
7. Add notes on progress/blockers
```

### Manager/Lead Workflow
```bash
# Daily:
1. Check Taiga dashboard
2. Review task progress
3. Assign new tasks
4. Unblock developers

# Weekly:
5. Sprint planning in Taiga
6. Update SPEC epic progress
7. Generate reports
```

---

## ✅ Benefits

### Before (Markdown Docs)
- ❌ Scattered across multiple files
- ❌ Manual updates needed
- ❌ Hard to track progress
- ❌ No visual workflow
- ❌ Stale quickly

### After (Taiga)
- ✅ Single source of truth
- ✅ Real-time updates
- ✅ Visual kanban/scrum boards
- ✅ Automatic progress tracking
- ✅ SPEC traceability built-in
- ✅ Team collaboration features
- ✅ Docusaurus integration

---

## 🚀 Quick Commands

```bash
# View Taiga
open http://localhost:9000/project/ninaivalaigal

# Check if Taiga is running
curl -s http://localhost:9000/api/v1/projects | jq .

# Start Taiga (if needed)
cd /Users/swami/WorkSpace/taiga
docker-compose -f taiga-docker/docker-compose.yml up -d

# Stop Taiga
docker-compose -f taiga-docker/docker-compose.yml down

# Import more tasks
cd /Users/swami/WorkSpace/taiga
TAIGA_USERNAME='admin' TAIGA_PASSWORD='admin123' python3 taiga-import-tasks.py
```

---

## 🎓 Learning Resources

**Taiga Docs:** https://docs.taiga.io/
**Our Plugin:** `/Users/swami/WorkSpace/taiga/docusaurus-plugin-taiga/README.md`
**Import Script:** `/Users/swami/WorkSpace/taiga/taiga-import-tasks.py`

---

## 🔐 Credentials

**Admin Account:**
- Username: `admin`
- Password: `admin123`
- Email: `admin@taiga.local`

**Create more users:**
```bash
docker exec -it taiga-docker-taiga-back-1 python manage.py createsuperuser
```

---

**Going forward: All task assignments happen in Taiga!** 🎯
