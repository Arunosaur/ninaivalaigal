# Task-Related Scripts

Helper scripts for updating Taiga user stories and tasks. These scripts are specifically for task management and should not be confused with project-level scripts in the `scripts/` directory.

## Location

All task-related scripts are located in `tasks/scripts/`:
- Task-specific helpers (Developer A, Developer B, etc.)
- Taiga integration utilities
- Story update helpers

**Project-level scripts** (infrastructure, deployment, testing) remain in the main `scripts/` directory.

## TaigaImporter Class

The `taiga_import_tasks.py` module provides a `TaigaImporter` class that handles:

- Authentication with Taiga API
- User story retrieval by reference number or ID
- Story updates with automatic version conflict handling
- Description updates (append/prepend)
- Status updates
- Comment creation (with fallback to description if comments fail)

### Usage Example

```python
from taiga_import_tasks import TaigaImporter

# Initialize
importer = TaigaImporter(
    base_url="http://localhost:9000/api/v1",
    username="admin",
    password="admin123"
)

# Get a story
story = importer.get_user_story("ninaivalaigal", 295)

# Update description
if story:
    new_desc = story["description"] + "\n\nNew update text"
    result = importer.update_user_story(
        story["id"],
        story["version"],
        {"description": new_desc}
    )
```

### Key Features

1. **Automatic Version Conflict Handling**: Retries updates when version conflicts occur
2. **Reliable Updates**: Uses PATCH method with proper headers
3. **Error Handling**: Clear error messages and graceful failures
4. **Session Management**: Reuses authenticated sessions

## Helper Scripts

### For Developer A: `dev_a_helper_fixed.py` and `dev_a_improved.py`

Updates US#295 with storage backend completion details.

```bash
# From project root
python3 tasks/scripts/dev_a_improved.py

# Or from tasks/scripts directory
cd tasks/scripts
python3 dev_a_improved.py
```

## Common Issues and Solutions

### Issue: "Story not found"
- **Solution**: Check that the story reference number is correct
- **Solution**: Verify project slug matches exactly (case-sensitive)
- **Solution**: Ensure authentication credentials are correct

### Issue: "Version conflict"
- **Solution**: The script automatically handles this by fetching the latest version
- **Solution**: If manual retry needed, the script includes `max_retries=3`

### Issue: "Comments endpoint 404"
- **Solution**: This is normal - comments API may not be available
- **Solution**: Use `append_to_story_description()` method instead
- **Solution**: The description update method is more reliable

### Issue: "Module not found"
- **Solution**: When importing from other scripts, add `tasks/scripts` to path:
  ```python
  import sys
  import os
  sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'tasks', 'scripts'))
  from taiga_import_tasks import TaigaImporter
  ```

## Environment Variables

Set these if using different credentials:

```bash
export TAIGA_URL="http://localhost:9000"
export TAIGA_USERNAME="admin"
export TAIGA_PASSWORD="admin123"
```

## Troubleshooting

1. **Authentication fails**: Check username/password
2. **Story not found**: Verify story reference number exists in project
3. **Update fails**: Check that version number is current (script handles this automatically)
4. **Import errors**: Ensure `taiga_import_tasks.py` is in the Python path (use sys.path.insert)

## Files in this directory

- `taiga_import_tasks.py` - Core TaigaImporter class
- `dev_a_helper_fixed.py` - Basic helper for Developer A
- `dev_a_improved.py` - Enhanced helper with better error handling
- `README.md` - This file
- `USAGE.md` - Detailed usage guide
- `__init__.py` - Python package marker
