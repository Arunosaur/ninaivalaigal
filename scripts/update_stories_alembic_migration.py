#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Medhasys LLC
#
"""
Update US#156, US#157, US#158 in Taiga to mention Alembic migration completion
"""

import os
import sys
from datetime import datetime

# Add tasks/scripts to path
script_dir = os.path.dirname(os.path.abspath(__file__))
tasks_scripts = os.path.join(script_dir, "..", "tasks", "scripts")
sys.path.insert(0, tasks_scripts)

try:
    from taiga_import_tasks import TaigaImporter
except ImportError:
    print("❌ Failed to import TaigaImporter")
    sys.exit(1)


def update_stories():
    taiga_url = os.getenv("TAIGA_URL", "http://localhost:9000")
    username = os.getenv("TAIGA_USERNAME", "admin")
    password = os.getenv("TAIGA_PASSWORD", "admin123")
    project_slug = "ninaivalaigal"

    importer = TaigaImporter(f"{taiga_url}/api/v1", username=username, password=password)
    importer._get_auth_token()
    print("✅ Authenticated with Taiga")

    alembic_update = """
---

✅ **Alembic Migration Created - {{timestamp}}**

**Migration:** `0126_spec026_team_billing_schema.py`
- Created Alembic migration for all SPEC-026 Phase 1 tables
- Includes upgrade() and downgrade() functions
- All tables can be created via: `alembic upgrade head`
- Migration is reversible for rollback safety

**Migration Includes:**
- All tables from US#156, US#157, US#158
- Foreign key constraints with CASCADE delete
- Performance indexes on all key columns
- CHECK constraints for data integrity
- UUID primary keys with gen_random_uuid()

**Git Commit:** `feat(spec-026): add Alembic migration for US#156-158 billing schema`
"""

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    update_text = alembic_update.replace("{{timestamp}}", timestamp)

    stories_updated = []
    for story_ref in [156, 157, 158]:
        story = importer.get_user_story(project_slug, story_ref)
        if story:
            result = importer.append_to_story_description(project_slug, story_ref, update_text)
            if result:
                stories_updated.append(story_ref)
                print(f"✅ Updated story #{story_ref}: {story['subject']}")
            else:
                print(f"❌ Failed to update story #{story_ref}")
        else:
            print(f"❌ Story #{story_ref} not found")

    print(f"\n✅ Updated {len(stories_updated)} stories with Alembic migration info")
    return 0 if len(stories_updated) == 3 else 1


if __name__ == "__main__":
    sys.exit(update_stories())
