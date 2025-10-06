# 📚 Document Cleanup Plan
**Date:** October 5, 2025
**Reason:** Too many duplicate status/summary documents causing confusion

---

## 🔴 Documents to Archive (24 files)

These are duplicate, outdated, or session-specific documents that should be archived:

### Session Summaries (Archive to `docs/archive/sessions/`)
1. `SESSION_COMPLETE_2025-10-03-2300.md`
2. `SESSION_COMPLETE_2025-10-04-2030.md`
3. `SESSION_FINAL_2025-10-03-2235.md`
4. `SESSION_STATUS_2025-10-05_0140.md`
5. `SESSION_SUMMARY_2025-10-03.md`
6. `SESSION_SUMMARY_2025-10-05_0741.md`

### Phase/Feature Completion Docs (Archive to `docs/archive/milestones/`)
7. `PHASE-1-COMPLETION-SUMMARY.md`
8. `PHASE-2A-COMPLETE-SUMMARY.md`
9. `PHASE_2B_COMPLETE.md`
10. `SPEC_085_IMPLEMENTATION_COMPLETE.md`
11. `ARCHITECTURE_IMPLEMENTATION_COMPLETE.md`
12. `DATABASE_RESTORATION_COMPLETE.md`
13. `VALIDATION_COMPLETE.md`
14. `PROFILE_BASED_DEPLOYMENT_COMPLETE.md`
15. `PROFILE_SEPARATION_COMPLETE_v2.md`

### Status Documents (Archive to `docs/archive/status/`)
16. `ADMIN_CONSOLE_STATUS.md`
17. `PGBOUNCER_AUTH_FINAL_STATUS.md`
18. `FINAL_STATUS_2025-10-03.md`

### Summary/Handoff Docs (Archive to `docs/archive/handoffs/`)
19. `FINAL_HANDOFF_SUMMARY.md`
20. `FINAL_SUMMARY.md`
21. `VALIDATION_SUMMARY.md`
22. `EXECUTIVE_SUMMARY.md`

### Duplicate Project Analysis (KEEP ONE, archive others to `docs/archive/analysis/`)
23. `PROJECT_STATUS_VISUAL.md` - KEEP (most recent)
24. `COMPLETE_PROJECT_ANALYSIS.md` - Archive

---

## ✅ Documents to KEEP in Root

### Active Planning Documents
1. ✅ **WORKING_STATE.md** - Current state (just created)
2. ✅ **ACCURATE_SPEC_ANALYSIS.md** - Fresh SPEC analysis (just created)
3. ✅ **PROJECT_STATUS_VISUAL.md** - Visual status dashboard
4. ✅ **README.md** - Project overview
5. ✅ **SPEC_AUDIT_2024_v2.0.md** - Latest SPEC audit

### Reference Documents (Consider moving to `docs/`)
6. `TODO_TRACKER.md` - Active TODO tracking
7. Various `.md` files in specs/ - Keep

---

## 📋 Cleanup Commands

```bash
# Create archive directories
mkdir -p docs/archive/{sessions,milestones,status,handoffs,analysis}

# Move session summaries
mv SESSION_*.md docs/archive/sessions/

# Move phase completion docs
mv PHASE-*.md PHASE_*.md docs/archive/milestones/
mv SPEC_085_IMPLEMENTATION_COMPLETE.md docs/archive/milestones/
mv ARCHITECTURE_IMPLEMENTATION_COMPLETE.md docs/archive/milestones/
mv DATABASE_RESTORATION_COMPLETE.md docs/archive/milestones/
mv VALIDATION_COMPLETE.md docs/archive/milestones/
mv PROFILE_*.md docs/archive/milestones/

# Move status documents
mv ADMIN_CONSOLE_STATUS.md docs/archive/status/
mv PGBOUNCER_AUTH_FINAL_STATUS.md docs/archive/status/
mv FINAL_STATUS_*.md docs/archive/status/

# Move handoff/summary documents
mv FINAL_HANDOFF_SUMMARY.md docs/archive/handoffs/
mv FINAL_SUMMARY.md docs/archive/handoffs/
mv VALIDATION_SUMMARY.md docs/archive/handoffs/
mv EXECUTIVE_SUMMARY.md docs/archive/handoffs/

# Move duplicate analysis (keep PROJECT_STATUS_VISUAL.md in root)
mv COMPLETE_PROJECT_ANALYSIS.md docs/archive/analysis/

# Create archive index
cat > docs/archive/README.md << 'EOF'
# Archived Documents

This directory contains historical status documents, session summaries, and milestone reports.

## Structure
- `sessions/` - Session-specific summaries
- `milestones/` - Phase and feature completion documents
- `status/` - Point-in-time status snapshots
- `handoffs/` - Handoff and summary documents
- `analysis/` - Project analysis documents

## Active Documents
See root directory for current, active documentation.
EOF

# Commit the cleanup
git add docs/archive/
git commit -m "Archive duplicate status documents for clarity"
```

---

## 🎯 Result

**Before:** 24+ status documents in root (confusing)
**After:** 5 active documents in root + organized archive

**Active Documents in Root:**
1. `README.md` - Project overview
2. `WORKING_STATE.md` - Current working state (LIVE)
3. `ACCURATE_SPEC_ANALYSIS.md` - Latest SPEC analysis
4. `PROJECT_STATUS_VISUAL.md` - Visual status dashboard
5. `SPEC_AUDIT_2024_v2.0.md` - SPEC audit reference

**Everything else:** Organized in `docs/archive/`

---

## ⏰ When to Execute

**Execute AFTER Day 1 safety net is complete:**
- Day 1: Build safety net (smoke tests, hooks, documentation)
- Day 2: Clean up documents (this plan)
- Day 3+: Start Phase 1 work

**Don't clean up before safety net** - Focus on one thing at a time.
