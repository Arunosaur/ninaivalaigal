# Taiga API Update Script

**Purpose**: Update Taiga story statuses via API
**Stories to Update**: BILL-002, BILL-003, BILL-004
**Target Status**: "Done"

## Taiga API Configuration

```bash
# Set these environment variables
export TAIGA_URL="https://your-taiga-instance.com"
export TAIGA_TOKEN="your-api-token"
```

## Update Script

```python
#!/usr/bin/env python3
"""
Update Taiga story statuses for completed SPEC-147 stories.
"""
import os
import requests
import json

TAIGA_URL = os.getenv("TAIGA_URL")
TAIGA_TOKEN = os.getenv("TAIGA_TOKEN")

# Story IDs to update
STORIES_TO_UPDATE = {
    765: "BILL-002: Real-time usage metering",
    766: "BILL-003: Quota enforcement",
    767: "BILL-004: Stripe integration",
}

# Status mapping (need to find actual status ID for "Done")
DONE_STATUS_ID = None  # Update with actual status ID from Taiga

def get_project_id():
    """Get project ID (you'll need to find this from Taiga)"""
    # This is a placeholder - you'll need to implement based on your Taiga setup
    pass

def get_status_id(status_name="Done"):
    """Get status ID for 'Done' status"""
    # GET /api/v1/projects/{project_id}/us_statuses
    # Find the status with name "Done" and return its ID
    pass

def update_story_status(story_id, status_id):
    """Update story status to Done"""
    url = f"{TAIGA_URL}/api/v1/userstories/{story_id}"
    headers = {
        "Authorization": f"Bearer {TAIGA_TOKEN}",
        "Content-Type": "application/json",
    }
    data = {
        "status": status_id,
    }
    response = requests.patch(url, headers=headers, json=data)
    return response.json()

def main():
    """Main update function"""
    # Get status ID for "Done"
    done_status_id = get_status_id("Done")

    # Update each story
    for story_id, story_name in STORIES_TO_UPDATE.items():
        print(f"Updating {story_name} (ID: {story_id})...")
        result = update_story_status(story_id, done_status_id)
        print(f"✅ Updated: {result.get('subject', 'Unknown')}")

    print("\n✅ All stories updated successfully!")

if __name__ == "__main__":
    main()
```

## Manual Update Instructions

If API access is not available, update manually in Taiga:

1. **Navigate to Story #765 (BILL-002)**
   - Open story in Taiga
   - Change status from "New" to "Done"
   - Add note: "Completed January 2025. 13/13 tests passing. Usage metering service, FastAPI middleware, and Redis caching implemented."
   - Assign to Developer D
   - Set completion date: January 2025

2. **Navigate to Story #766 (BILL-003)**
   - Open story in Taiga
   - Change status from "New" to "Done"
   - Add note: "Completed January 2025. 11/11 tests passing. Quota enforcement with soft/hard blocks implemented. Email integration pending."
   - Assign to Developer D
   - Set completion date: January 2025

3. **Navigate to Story #767 (BILL-004)**
   - Open story in Taiga
   - Change status from "New" to "Done"
   - Add note: "Completed January 2025. Core functionality 100% complete. Stripe integration, webhook handling, subscription sync implemented. Payment method UI pending (future enhancement)."
   - Assign to Developer D
   - Set completion date: January 2025

## Completion Notes Template

For each story, add this completion note:

```
✅ COMPLETED: January 2025

Implementation Details:
- [List key files implemented]
- [Test results: X/Y tests passing]
- [Performance metrics if applicable]

Status:
- Core functionality: ✅ Complete
- Testing: ✅ Complete
- Documentation: ✅ Complete
- Pending enhancements: [List any]

Files:
- server/billing/[relevant_files]
- tests/[relevant_test_files]

Total: [X lines of code, Y tests]
```

---

**Note**: This script is a template. Actual implementation will depend on your Taiga API version and authentication method.
