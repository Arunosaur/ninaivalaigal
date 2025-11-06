#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# Create Taiga stories for SPEC-108: Image Backup & Disaster Recovery
# Assigns stories to Developer C

import os
import sys
from pathlib import Path

# Add tasks/scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent / "tasks" / "scripts"))

try:
    from taiga_import_tasks import TaigaImporter
except ImportError:
    print("❌ Failed to import TaigaImporter")
    sys.exit(1)

# Configuration
TAIGA_URL = os.getenv("TAIGA_URL", "http://localhost:9000")
API_ENDPOINT = f"{TAIGA_URL}/api/v1"
TAIGA_USERNAME = os.getenv("TAIGA_USERNAME", "admin")
TAIGA_PASSWORD = os.getenv("TAIGA_PASSWORD", "admin123")
PROJECT_SLUG = "ninaivalaigal"
DEVELOPER_C_USERNAME = "developer-c"

# SPEC-108 stories to create (based on implementation checklist)
STORIES = [
    {
        "subject": "SPEC-108: Install backup scripts in /scripts/backup/ directory",
        "description": """**Goal**: Create comprehensive backup script directory structure

**Context**: SPEC-108 requires organized backup scripts in `/scripts/backup/` directory.

**Tasks**:
- [ ] Create `/scripts/backup/` directory structure
- [ ] Organize backup scripts by category (postgres, redis, images, volumes, secrets)
- [ ] Set up proper permissions and ownership
- [ ] Document script organization

**Acceptance Criteria**:
- ✅ `/scripts/backup/` directory exists
- ✅ Scripts organized by backup type
- ✅ Proper permissions set (755 for scripts, 700 for backup directories)
- ✅ README.md in backup directory explaining structure

**Reference**: SPEC-108 Section 11 (Implementation Checklist)""",
        "tags": ["spec-108", "backup", "infrastructure", "scripts"],
    },
    {
        "subject": "SPEC-108: Configure PostgreSQL WAL archiving for PITR",
        "description": """**Goal**: Enable PostgreSQL Point-in-Time Recovery (PITR) with WAL archiving

**Context**: SPEC-108 requires continuous WAL archiving for disaster recovery with <5 minute RPO.

**Tasks**:
- [ ] Update PostgreSQL configuration to enable WAL archiving
- [ ] Set `wal_level = replica`
- [ ] Set `archive_mode = on`
- [ ] Configure `archive_command` to copy WAL files to `/backups/wal_archive/`
- [ ] Set `archive_timeout = 300` (5 minutes)
- [ ] Configure WAL retention (max_wal_size, min_wal_size)
- [ ] Test WAL archiving works
- [ ] Verify no gaps in WAL archive

**Acceptance Criteria**:
- ✅ PostgreSQL WAL archiving enabled
- ✅ WAL files archived to `/backups/wal_archive/`
- ✅ Archive command working correctly
- ✅ No gaps in WAL archive
- ✅ WAL retention configured appropriately

**Reference**: SPEC-108 Section 2.2.B (Point-in-Time Recovery)""",
        "tags": ["spec-108", "postgresql", "pitr", "wal-archiving", "disaster-recovery"],
    },
    {
        "subject": "SPEC-108: Create pg_basebackup.sh script for PITR base backups",
        "description": """**Goal**: Implement PostgreSQL base backup script for PITR

**Context**: SPEC-108 requires `pg_basebackup` for PITR base backups.

**Tasks**:
- [ ] Create `/scripts/backup/pg-basebackup.sh`
- [ ] Implement base backup with proper flags
- [ ] Create backup metadata JSON (backup_date, database, wal_position, restore_command)
- [ ] Add progress reporting
- [ ] Test base backup creation
- [ ] Verify backup metadata is correct

**Acceptance Criteria**:
- ✅ `pg-basebackup.sh` script exists in `/scripts/backup/`
- ✅ Creates base backups in tar.gz format
- ✅ Generates backup metadata JSON
- ✅ Base backups can be used for PITR restore
- ✅ Script is executable and tested

**Reference**: SPEC-108 Section 2.2.B (Base backup script)""",
        "tags": ["spec-108", "postgresql", "pitr", "pg-basebackup", "backup-scripts"],
    },
    {
        "subject": "SPEC-108: Configure Redis RDB + AOF persistence",
        "description": """**Goal**: Enable Redis persistence for backup and recovery

**Context**: SPEC-108 requires Redis RDB snapshots and AOF for data durability.

**Tasks**:
- [ ] Update Redis configuration for RDB snapshots
- [ ] Configure automatic RDB snapshots (save directives)
- [ ] Enable AOF (appendonly yes)
- [ ] Configure AOF sync strategy (appendfsync everysec)
- [ ] Set up AOF rewrite settings
- [ ] Test RDB snapshot creation
- [ ] Test AOF backup
- [ ] Verify both persistence methods work

**Acceptance Criteria**:
- ✅ Redis RDB snapshots configured and working
- ✅ Redis AOF enabled and working
- ✅ Automatic snapshots trigger correctly
- ✅ AOF rewrites happen automatically
- ✅ Backup scripts can copy RDB and AOF files

**Reference**: SPEC-108 Section 2.3 (Redis Persistence)""",
        "tags": ["spec-108", "redis", "rdb", "aof", "persistence", "backup"],
    },
    {
        "subject": "SPEC-108: Create comprehensive backup-all.sh script",
        "description": """**Goal**: Create unified backup script that backs up all components

**Context**: SPEC-108 requires a single script that backs up PostgreSQL, Redis, images, volumes, and secrets.

**Tasks**:
- [ ] Create `/scripts/backup/backup-all.sh`
- [ ] Implement PostgreSQL pg_dump backup
- [ ] Implement PostgreSQL pg_basebackup (PITR)
- [ ] Implement Redis RDB backup
- [ ] Implement Redis AOF backup
- [ ] Implement Docker image backup (docker save)
- [ ] Implement volume backup (tar)
- [ ] Implement encrypted secrets backup
- [ ] Generate backup manifest.json with SHA256 checksums
- [ ] Add error handling and logging
- [ ] Test complete backup flow

**Acceptance Criteria**:
- ✅ `backup-all.sh` script exists
- ✅ Backs up all components (PostgreSQL, Redis, images, volumes, secrets)
- ✅ Generates manifest.json with checksums
- ✅ All backups complete successfully
- ✅ Script is executable and tested
- ✅ Backup time < 15 minutes for dev environment

**Reference**: SPEC-108 Section 3 (Comprehensive Backup Flow)""",
        "tags": ["spec-108", "backup-all", "comprehensive-backup", "scripts"],
    },
    {
        "subject": "SPEC-108: Set up cron jobs for automated backups",
        "description": """**Goal**: Automate daily backups via cron

**Context**: SPEC-108 requires nightly automated backups with retention tiers.

**Tasks**:
- [ ] Create cron job for daily backup at 2 AM
- [ ] Configure retention policy (7 daily, 4 weekly, 3 monthly)
- [ ] Set up backup rotation script
- [ ] Configure backup logging
- [ ] Test cron job execution
- [ ] Verify backups run automatically
- [ ] Verify retention policy works

**Acceptance Criteria**:
- ✅ Cron job configured for daily backups
- ✅ Backups run automatically at scheduled time
- ✅ Retention policy enforced (7 daily, 4 weekly, 3 monthly)
- ✅ Old backups cleaned up automatically
- ✅ Backup logs stored for monitoring

**Reference**: SPEC-108 Section 5 (Retention Policy)""",
        "tags": ["spec-108", "cron", "automation", "retention-policy"],
    },
    {
        "subject": "SPEC-108: Configure S3/NAS for off-site replication",
        "description": """**Goal**: Implement 3-2-1 backup rule with off-site replication

**Context**: SPEC-108 requires 3 copies, 2 media types, 1 off-site (3-2-1 rule).

**Tasks**:
- [ ] Set up S3 bucket or NAS for off-site backups
- [ ] Configure backup replication script
- [ ] Implement rsync or S3 sync for off-site copy
- [ ] Test off-site replication
- [ ] Verify backups are accessible off-site
- [ ] Document off-site restore procedure

**Acceptance Criteria**:
- ✅ Off-site storage configured (S3 or NAS)
- ✅ Backups automatically replicated off-site
- ✅ 3-2-1 backup rule satisfied (3 copies, 2 media types, 1 off-site)
- ✅ Off-site backups verified and accessible
- ✅ Restore from off-site tested

**Reference**: SPEC-108 Section 1 (3-2-1 backup rule)""",
        "tags": ["spec-108", "off-site", "s3", "nas", "replication", "disaster-recovery"],
    },
    {
        "subject": "SPEC-108: Set up backup monitoring and alerts",
        "description": """**Goal**: Monitor backup health and alert on failures

**Context**: SPEC-108 requires backup monitoring with alerts for failures.

**Tasks**:
- [ ] Create Prometheus metrics exporter for backup health
- [ ] Export metrics: backup_duration_seconds, backup_size_bytes, backup_success, backup_age_seconds
- [ ] Configure Prometheus alerts for backup failures
- [ ] Configure alerts for backup age (no backup in 24h)
- [ ] Set up notification channels (email/Slack)
- [ ] Test alert triggers
- [ ] Verify alerts notify within 5 minutes of failure

**Acceptance Criteria**:
- ✅ Prometheus metrics exported for backup health
- ✅ Backup success/failure metrics tracked
- ✅ Alerts configured for backup failures
- ✅ Alerts configured for backup age
- ✅ Notifications sent within 5 minutes of failure
- ✅ Monitoring dashboard created

**Reference**: SPEC-108 Section 9 (Monitoring & Alerts)""",
        "tags": ["spec-108", "monitoring", "alerts", "prometheus", "observability"],
    },
    {
        "subject": "SPEC-108: Create comprehensive restore-all.sh script",
        "description": """**Goal**: Create unified restore script for disaster recovery

**Context**: SPEC-108 requires 1-click restore with RTO < 30 minutes.

**Tasks**:
- [ ] Create `/scripts/backup/restore-all.sh`
- [ ] Implement restore from backup manifest
- [ ] Support full disaster restore
- [ ] Support data-only restore
- [ ] Support PITR restore to arbitrary timestamp
- [ ] Implement restore verification (checksums)
- [ ] Add health check validation after restore
- [ ] Test restore procedures
- [ ] Document restore runbook

**Acceptance Criteria**:
- ✅ `restore-all.sh` script exists
- ✅ Can restore from backup manifest
- ✅ Supports full, data-only, and PITR restore
- ✅ Restore time < 15 minutes for dev environment
- ✅ Restore includes health check verification
- ✅ All services start and pass health checks after restore
- ✅ Data integrity verified after restore

**Reference**: SPEC-108 Section 4 (Restore Flow)""",
        "tags": ["spec-108", "restore", "disaster-recovery", "scripts"],
    },
    {
        "subject": "SPEC-108: Conduct first restore drill and document RTO/RPO",
        "description": """**Goal**: Validate backup/restore procedures and document actual metrics

**Context**: SPEC-108 requires proven restore drills with documented RTO/RPO.

**Tasks**:
- [ ] Conduct first full restore drill
- [ ] Measure actual RTO (Recovery Time Objective)
- [ ] Measure actual RPO (Recovery Point Objective)
- [ ] Document restore drill results
- [ ] Update runbooks with actual metrics
- [ ] Schedule monthly restore drills
- [ ] Create restore drill checklist

**Acceptance Criteria**:
- ✅ First restore drill completed successfully
- ✅ RTO measured and documented (< 30 minutes target)
- ✅ RPO measured and documented (< 5 minutes target)
- ✅ Runbooks updated with actual metrics
- ✅ Monthly restore drill schedule established
- ✅ Restore drill checklist created

**Reference**: SPEC-108 Section 10 (Disaster Recovery Runbook)""",
        "tags": ["spec-108", "restore-drill", "rto", "rpo", "validation", "documentation"],
    },
]


def get_user_id(importer, username):
    """Get user ID by username - checks project members first, then global users."""
    print(f"   Looking up user: {username}")
    import requests

    headers = importer._get_headers()

    # First, try to get from project members
    project = importer.get_project(PROJECT_SLUG)
    if project:
        members_url = f"{importer.base_url}/projects/{project['id']}/members"
        try:
            response = requests.get(members_url, headers=headers)
            if response.status_code == 200:
                members = response.json()
                for member in members:
                    user = member.get("user", {})
                    if user.get("username", "").lower() == username.lower():
                        user_id = user.get("id")
                        print(f"   ✅ Found user in project members: {user.get('username')} (ID: {user_id})")
                        return user_id
        except Exception as e:
            print(f"⚠️  Error getting project members: {e}")

    # Fallback: search global users list
    print(f"   User not in project members, searching global users...")
    users_url = f"{importer.base_url}/users"
    try:
        response = requests.get(users_url, headers=headers)
        if response.status_code == 200:
            users = response.json()
            for user in users:
                if user.get("username", "").lower() == username.lower():
                    user_id = user.get("id")
                    print(f"   ✅ Found user in global users: {user.get('username')} (ID: {user_id})")
                    print(f"   ⚠️  Note: User exists but may not be a project member")
                    return user_id
    except Exception as e:
        print(f"⚠️  Error getting global users: {e}")

    print(f"   ❌ User '{username}' not found")
    return None


def create_story(importer, story_data, developer_c_id, project_id, status_id):
    """Create a user story in Taiga."""
    story_url = f"{importer.base_url}/userstories"
    headers = importer._get_headers()

    payload = {
        "project": project_id,
        "subject": story_data["subject"],
        "description": story_data["description"],
        "assigned_to": developer_c_id,
        "status": status_id,
        "tags": story_data.get("tags", []),
    }

    import requests

    response = requests.post(story_url, headers=headers, json=payload)

    if response.status_code in [200, 201]:
        story = response.json()
        print(f"   ✅ Created story: US#{story.get('ref', '?')} - {story.get('subject', '')}")
        return story
    else:
        print(f"   ❌ Failed to create story: {response.status_code}")
        print(response.text)
        return None


def main():
    print("🚀 Creating Taiga stories for SPEC-108: Image Backup & Disaster Recovery")
    print("=" * 80)

    # Initialize importer
    importer = TaigaImporter(API_ENDPOINT, username=TAIGA_USERNAME, password=TAIGA_PASSWORD)
    print("✅ Authenticated with Taiga")

    # Get project
    project = importer.get_project(PROJECT_SLUG)
    if not project:
        print(f"❌ Project not found: {PROJECT_SLUG}")
        sys.exit(1)

    project_id = project["id"]
    print(f"✅ Found project: {project.get('name')} (ID: {project_id})")

    # Get Developer C user ID
    developer_c_id = get_user_id(importer, DEVELOPER_C_USERNAME)
    if not developer_c_id:
        print(f"⚠️  Developer C ({DEVELOPER_C_USERNAME}) not found, will use admin")
        # Get admin user ID as fallback
        import requests

        headers = importer._get_headers()
        me_url = f"{importer.base_url}/users/me"
        response = requests.get(me_url, headers=headers)
        if response.status_code == 200:
            developer_c_id = response.json().get("id")
            print(f"   Using admin user ID: {developer_c_id}")
        else:
            print("❌ Could not get user ID")
            sys.exit(1)
    else:
        print(f"✅ Found Developer C: {developer_c_id}")

    # Get "New" or "Ready" status ID
    import requests

    headers = importer._get_headers()
    statuses_url = f"{importer.base_url}/userstory-statuses?project={project_id}"
    response = requests.get(statuses_url, headers=headers)

    if response.status_code != 200:
        print("❌ Failed to get statuses")
        sys.exit(1)

    statuses = response.json()
    status_id = None
    for status in statuses:
        if status["name"].lower() in ["new", "ready", "in progress"]:
            status_id = status["id"]
            print(f"✅ Using status: {status['name']} (ID: {status_id})")
            break

    if not status_id:
        print("⚠️  No suitable status found, using first available")
        status_id = statuses[0]["id"] if statuses else None

    # Create stories
    created_stories = []
    for story_data in STORIES:
        story = create_story(importer, story_data, developer_c_id, project_id, status_id)
        if story:
            created_stories.append(story)

    # Summary
    print("\n" + "=" * 80)
    print(f"✅ Created {len(created_stories)}/{len(STORIES)} stories for SPEC-108")

    if created_stories:
        print("\n📋 Created Stories:")
        for story in created_stories:
            story_ref = story.get("ref", "?")
            story_subject = story.get("subject", "")
            print(f"   - US#{story_ref}: {story_subject}")

    print("\n🎯 Next Steps:")
    print("   1. Update SPEC-108 README.md to reference these stories")
    print("   2. Update SPEC-108 status (currently marked Complete but implementation incomplete)")
    print("   3. Assign stories to Developer C (already done)")
    print("   4. Begin implementation work")


if __name__ == "__main__":
    main()
