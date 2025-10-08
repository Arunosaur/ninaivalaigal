# 🧩 Pre-Commit Hook Restoration – Phase 1 (Server)

## Objective
Restore flake8 enforcement on core `server/` code.

### Scope
- Directory: `server/`
- Total Files: 304
- Current Issues: 107 undefined names, 157 line length violations

### Plan
1. Enable flake8 for `server/` only
2. Fix all E9, F63, F7, F82 errors
3. Commit incremental fixes weekly

### Deliverables
- ✅ server lint clean
- ✅ CI enforcement on core backend
- ✅ Report in `PRE_COMMIT_HOOK_RESTORE_SERVER.md`
