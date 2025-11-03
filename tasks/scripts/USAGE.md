# Usage Guide for Task Scripts

## Location

These scripts are located in `tasks/scripts/` and are specifically for task-related work (Taiga integration, developer helpers, etc.).

## Available Scripts

### 1. TaigaImporter Class

**File**: `taiga_import_tasks.py`

Core class for interacting with Taiga API.

```python
from taiga_import_tasks import TaigaImporter

importer = TaigaImporter(
    "http://localhost:9000/api/v1",
    username="admin",
    password="admin123"
)
```

### 2. Developer A Helper Scripts

**Files**:
- `dev_a_helper_fixed.py` - Basic helper for updating US#295
- `dev_a_improved.py` - Enhanced version with better error handling

**Usage**:
```bash
# From project root
python3 tasks/scripts/dev_a_improved.py

# Or from tasks/scripts directory
cd tasks/scripts
python3 dev_a_improved.py
```

## Import Path

When importing `TaigaImporter` from other scripts:

```python
import sys
import os

# Add tasks/scripts to path
script_dir = os.path.dirname(os.path.abspath(__file__))
tasks_scripts = os.path.join(script_dir, '..', '..', 'tasks', 'scripts')
sys.path.insert(0, tasks_scripts)

from taiga_import_tasks import TaigaImporter
```

## Environment Variables

```bash
export TAIGA_URL="http://localhost:9000"
export TAIGA_USERNAME="admin"
export TAIGA_PASSWORD="admin123"
```

## Note

These scripts are **task-related** and should be kept separate from project-level scripts in the main `scripts/` directory.
