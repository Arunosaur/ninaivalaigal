# Phase 1 - Continue Here

## Current Status
- ✅ Baseline captured: 107 errors in server/, 3 in tests/
- ✅ Auto-fix ran (isort completed)
- ✅ Fixed List import in substrate.py
- 🔄 **Current: 103 errors remaining** (down from 107)

## Top Files with Errors (Fix These First)

1. **server/database/operations/context_ops.py** - 32 errors
   - Missing: `from server.database.models import Context`

2. **server/mcp/tools.py** - 19 errors
   - Missing imports for: `spec_context_manager`, `auto_recorder`

3. **server/models/standalone_teams.py** - 14 errors
   - Missing: `from server.database.models import Team, User, Organization`

4. **server/main_monolithic_backup.py** - 7 errors (can skip, it's backup)

5. **server/routers/contexts.py** - 6 errors
   - Missing: dependency injection for `db`

6. **server/routers/recording.py** - 5 errors
   - Missing: dependency injection for `auto_recorder`

7. **server/routers/approvals.py** - 5 errors
   - Missing: dependency injection for `approval_manager`, `db`

## Quick Fix Commands

```bash
# Fix context_ops.py
# Add to imports: from server.database.models import Context

# Fix standalone_teams.py
# Add to imports: from server.database.models import Team, User, Organization

# Fix mcp/tools.py
# Add proper dependency injection or imports

# Check progress
flake8 server/ --count --select=F821 --statistics
```

## After Fixing

1. Update `.pre-commit-config.yaml`:
   - Remove `server/.*\.py` from flake8 exclusions

2. Test:
   ```bash
   pre-commit run flake8 --files server/**/*.py
   ```

3. Commit:
   ```bash
   git add server/ .pre-commit-config.yaml
   git commit -m "fix(hooks): Phase 1 complete - server/ enforcement restored"
   ```

## Progress
- Started: 107 errors
- Current: 103 errors
- Target: 0 errors
