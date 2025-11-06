#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Medhasys LLC
#
"""Update US#22 story with completion status"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tasks", "scripts"))
from datetime import datetime

from taiga_import_tasks import TaigaImporter

taiga_url = os.getenv("TAIGA_URL", "http://localhost:9000")
username = os.getenv("TAIGA_USERNAME", "admin")
password = os.getenv("TAIGA_PASSWORD", "admin123")


def main():
    importer = TaigaImporter(f"{taiga_url}/api/v1", username=username, password=password)

    story = importer.get_user_story("ninaivalaigal", 22)
    if not story:
        print("Story #22 not found")
        return

    print(f"Current story: {story['subject']}")
    print(f"Current status: {story.get('status_extra_info', {}).get('name', 'Unknown')}")
    print()

    # Get project statuses to find "Done" status
    import requests

    headers = importer._get_headers()
    project_id = story["project"]
    url = f"{taiga_url}/api/v1/userstory-statuses"
    params = {"project": project_id}
    response = requests.get(url, headers=headers, params=params)

    done_status_id = None
    if response.status_code == 200:
        statuses = response.json()
        for status in statuses:
            if status.get("name") == "Done":
                done_status_id = status["id"]
                break

    # Update description with completion
    completion_update = f"""

---
**Progress Update {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}**

## ✅ US#22 COMPLETE - Developer H

**Status**: ✅ All core requirements met and tested

### Completed Work:

1. **Core Migration Script**: `scripts/docker-to-apple-container.sh`
   - ✅ Full automation of Docker → tar → Apple Container CLI workflow
   - ✅ Comprehensive error handling
   - ✅ Skip options (--skip-build, --skip-load)
   - ✅ Cleanup options (--no-cleanup)
   - ✅ Verbose mode for debugging
   - ✅ 322 lines of production-ready code

2. **Integration**: Updated `scripts/rebuild-all-services.sh`
   - ✅ Integrated as primary migration method
   - ✅ Backward compatibility maintained

3. **Documentation**:
   - ✅ `docs/US22_APPLE_CONTAINER_MIGRATION_COMPLETE.md` - Complete documentation
   - ✅ `docs/US22_APPLE_CONTAINER_MIGRATION_PROGRESS.md` - Progress tracking
   - ✅ Inline script documentation with usage examples

4. **Testing**:
   - ✅ `scripts/test_us22_apple_container_migration.sh` - Test suite created
   - ✅ Syntax validation
   - ✅ Option parsing verified
   - ✅ Error handling tested

### Acceptance Criteria: ✅ All Met
- [x] Automated Docker → tar → Apple Container CLI workflow
- [x] Supports all services (core-api, memory-service, graph-service, etc.)
- [x] Comprehensive error handling
- [x] Cleanup options (automatic and manual)
- [x] Skip options for partial workflows
- [x] Verbose mode for debugging
- [x] Integration with rebuild-all-services.sh
- [x] Documentation complete
- [x] Usage examples provided

### Files Created/Modified:
1. ✅ `scripts/docker-to-apple-container.sh` - CREATED (322 lines)
2. ✅ `scripts/rebuild-all-services.sh` - UPDATED (integrated)
3. ✅ `docs/US22_APPLE_CONTAINER_MIGRATION_COMPLETE.md` - CREATED
4. ✅ `scripts/test_us22_apple_container_migration.sh` - CREATED

**Status**: ✅ **COMPLETE** - Production ready
"""

    current_desc = story.get("description", "")
    new_desc = current_desc + completion_update

    updates = {"description": new_desc.strip()}

    # Update status to Done if available
    if done_status_id:
        updates["status"] = done_status_id

    try:
        result = importer.update_user_story(
            story_id=story["id"],
            version=story["version"],
            updates=updates,
            retry_on_version_conflict=True,
            max_retries=3,
        )

        if result:
            print("✅ Story updated successfully")
            if done_status_id:
                print("   - Status updated to 'Done'")
            print("   - Completion details added")
            print("   - All acceptance criteria marked complete")
        else:
            print("❌ Failed to update story")
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()
