#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""Consolidate user tables - make public.users canonical, ag_catalog.users a materialized view

Revision ID: 0123_consolidate_user_tables
Revises: 0122_update_memories_schema
Create Date: 2025-10-29 20:40:00.000000

Changes:
- Backup ag_catalog.users to ag_catalog.users_backup
- Migrate any unique data from ag_catalog.users to public.users
- Drop ag_catalog.users table
- Create ag_catalog.users as a materialized view of public.users
- Fix all foreign keys to reference public.users instead of ag_catalog.users
- Create indexes on materialized view for graph queries
- Set search_path to prioritize public schema

Background:
This fixes the dual-schema conflict where users were being created in both
public.users and ag_catalog.users, causing foreign key violations for
role_assignments and other relational tables.

The new architecture:
- public.users = canonical source of truth (ACID, FKs, ORMs)
- ag_catalog.users = read-only projection for Apache AGE graph queries
"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "0123_consolidate_user_tables"
down_revision = "0122_update_memories_schema"
branch_labels = None
depends_on = None


def upgrade():
    """Consolidate user tables into single source of truth"""

    # Step 0: Drop all user-related FKs temporarily to allow data migration
    print("🔓 Step 0: Temporarily dropping foreign key constraints...")
    op.execute("ALTER TABLE memories DROP CONSTRAINT IF EXISTS memories_user_id_fkey;")
    op.execute("ALTER TABLE ag_catalog.contexts DROP CONSTRAINT IF EXISTS contexts_user_id_fkey;")
    op.execute("ALTER TABLE team_members DROP CONSTRAINT IF EXISTS team_members_user_id_fkey;")
    op.execute("ALTER TABLE role_assignments DROP CONSTRAINT IF EXISTS role_assignments_user_id_fkey;")
    op.execute("ALTER TABLE role_assignments DROP CONSTRAINT IF EXISTS role_assignments_granted_by_fkey;")

    # Step 1: Create backup of ag_catalog.users
    print("📦 Step 1: Backing up ag_catalog.users...")
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS ag_catalog.users_backup AS
        TABLE ag_catalog.users;
    """
    )

    # Step 2: Handle duplicate emails and migrate users
    print("🔄 Step 2: Reconciling users between ag_catalog and public...")

    # 2a. Find users with same email but different IDs
    duplicates = (
        op.get_bind()
        .execute(
            sa.text(
                """
        SELECT a.id as ag_id, a.email, p.id as pub_id
        FROM ag_catalog.users a
        JOIN public.users p ON a.email = p.email
        WHERE a.id != p.id;
    """
            )
        )
        .fetchall()
    )

    if duplicates:
        print(f"   Found {len(duplicates)} email duplicates with different IDs")
        for dup in duplicates:
            print(f"      {dup[1]}: ag_catalog={dup[0]}, public={dup[2]}")

        # Update foreign key references to point to public.users ID
        for dup in duplicates:
            ag_id = str(dup[0])
            pub_id = str(dup[2])

            # Update memories
            op.execute(
                sa.text(
                    f"""
                UPDATE memories SET user_id = '{pub_id}'
                WHERE user_id = '{ag_id}';
            """
                )
            )

            # Update contexts (in ag_catalog schema)
            op.execute(
                sa.text(
                    f"""
                UPDATE ag_catalog.contexts SET user_id = '{pub_id}'
                WHERE user_id = '{ag_id}';
            """
                )
            )

            # Update team_members
            op.execute(
                sa.text(
                    f"""
                UPDATE team_members SET user_id = '{pub_id}'
                WHERE user_id = '{ag_id}';
            """
                )
            )

            # Update role_assignments
            op.execute(
                sa.text(
                    f"""
                UPDATE role_assignments SET user_id = '{pub_id}'
                WHERE user_id = '{ag_id}';
            """
                )
            )
            op.execute(
                sa.text(
                    f"""
                UPDATE role_assignments SET granted_by = '{pub_id}'
                WHERE granted_by = '{ag_id}';
            """
                )
            )

        print("   ✅ Updated foreign key references for duplicates")

    # 2b. Migrate users that don't exist in public by ID or email
    users_to_migrate = (
        op.get_bind()
        .execute(
            sa.text(
                """
        SELECT COUNT(*) FROM ag_catalog.users a
        WHERE NOT EXISTS (
            SELECT 1 FROM public.users p WHERE p.id = a.id OR p.email = a.email
        );
    """
            )
        )
        .scalar()
    )

    print("   Found " + str(users_to_migrate) + " unique users to migrate from ag_catalog to public")

    if users_to_migrate > 0:
        op.execute(
            """
            INSERT INTO public.users (
                id, username, email, name, password_hash, account_type,
                subscription_tier, role, created_via, email_verified,
                is_active, created_at, updated_at, personal_contexts_limit,
                verification_token, last_login, default_role, is_system_admin
            )
            SELECT
                a.id,
                a.username,
                a.email,
                a.name,
                a.password_hash,
                a.account_type,
                COALESCE(a.subscription_tier, 'free'),
                COALESCE(a.role, 'user'),
                COALESCE(a.created_via, 'signup'),
                COALESCE(a.email_verified, false),
                COALESCE(a.is_active, true),
                COALESCE(a.created_at, NOW()),
                COALESCE(a.updated_at, NOW()),
                COALESCE(a.personal_contexts_limit, 10),
                a.verification_token,
                a.last_login,
                COALESCE(a.default_role, 'MEMBER'),
                COALESCE(a.is_system_admin, false)
            FROM ag_catalog.users a
            WHERE NOT EXISTS (
                SELECT 1 FROM public.users p WHERE p.id = a.id OR p.email = a.email
            );
        """
        )
        print(f"   ✅ Migrated {users_to_migrate} users")
    else:
        print("   ✅ No new users to migrate")

    # Step 3: Drop ag_catalog.users table (CASCADE to remove dependencies)
    print("🗑️  Step 3: Dropping ag_catalog.users table...")
    op.execute("DROP TABLE IF EXISTS ag_catalog.users CASCADE;")

    # Step 4: Create ag_catalog.users as materialized view
    print("✨ Step 4: Creating ag_catalog.users materialized view...")
    op.execute(
        """
        CREATE MATERIALIZED VIEW ag_catalog.users AS
        SELECT
            id,
            email,
            name,
            created_at,
            updated_at,
            account_type,
            subscription_tier,
            is_active,
            email_verified,
            last_login,
            default_role,
            is_system_admin
        FROM public.users;
    """
    )

    # Step 5: Create indexes on materialized view
    print("🔍 Step 5: Creating indexes on materialized view...")
    op.execute(
        """
        CREATE UNIQUE INDEX idx_ag_catalog_users_id
        ON ag_catalog.users(id);
    """
    )
    op.execute(
        """
        CREATE INDEX idx_ag_catalog_users_email
        ON ag_catalog.users(email);
    """
    )
    op.execute(
        """
        CREATE INDEX idx_ag_catalog_users_active
        ON ag_catalog.users(is_active)
        WHERE is_active = true;
    """
    )

    # Step 6: Fix all foreign keys to point to public.users
    print("🔗 Step 6: Fixing foreign key constraints...")

    # Note: FKs already point to public.users, but let's make sure
    # We'll drop and recreate them to ensure they're pointing to the right table

    # Find and fix role_assignments FK
    op.execute(
        """
        ALTER TABLE role_assignments
        DROP CONSTRAINT IF EXISTS role_assignments_user_id_fkey;
    """
    )
    op.execute(
        """
        ALTER TABLE role_assignments
        DROP CONSTRAINT IF EXISTS role_assignments_granted_by_fkey;
    """
    )

    # Only add FKs if there are no orphaned records
    orphan_check = (
        op.get_bind()
        .execute(
            sa.text(
                """
        SELECT COUNT(*) FROM role_assignments ra
        WHERE ra.user_id NOT IN (SELECT id FROM public.users)
           OR ra.granted_by NOT IN (SELECT id FROM public.users);
    """
            )
        )
        .scalar()
    )

    if orphan_check == 0:
        op.execute(
            """
            ALTER TABLE role_assignments
            ADD CONSTRAINT role_assignments_user_id_fkey
            FOREIGN KEY (user_id) REFERENCES public.users(id);
        """
        )
        op.execute(
            """
            ALTER TABLE role_assignments
            ADD CONSTRAINT role_assignments_granted_by_fkey
            FOREIGN KEY (granted_by) REFERENCES public.users(id);
        """
        )
        print("   ✅ Fixed role_assignments FKs")
    else:
        print(f"   ⚠️  Skipping role_assignments FKs - {orphan_check} orphaned records found")

    # Fix other common tables that reference users
    # Team members
    op.execute(
        """
        ALTER TABLE team_members
        DROP CONSTRAINT IF EXISTS team_members_user_id_fkey;
    """
    )
    op.execute(
        """
        ALTER TABLE team_members
        ADD CONSTRAINT team_members_user_id_fkey
        FOREIGN KEY (user_id) REFERENCES public.users(id);
    """
    )

    # Memories - check for orphaned records first
    op.execute(
        """
        ALTER TABLE memories
        DROP CONSTRAINT IF EXISTS memories_user_id_fkey;
    """
    )

    mem_orphan_check = (
        op.get_bind()
        .execute(
            sa.text(
                """
        SELECT COUNT(*) FROM memories m
        WHERE m.user_id NOT IN (SELECT id FROM public.users);
    """
            )
        )
        .scalar()
    )

    if mem_orphan_check == 0:
        op.execute(
            """
            ALTER TABLE memories
            ADD CONSTRAINT memories_user_id_fkey
            FOREIGN KEY (user_id) REFERENCES public.users(id);
        """
        )
        print("   ✅ Fixed memories FK")
    else:
        print("   ⚠️  Skipping memories FK - {} orphaned records found".format(mem_orphan_check))
        print("   Run: DELETE FROM memories WHERE user_id NOT IN (SELECT id FROM public.users);")

    # Contexts (in ag_catalog, uses user_id not owner_id)
    op.execute(
        """
        ALTER TABLE ag_catalog.contexts
        DROP CONSTRAINT IF EXISTS contexts_user_id_fkey;
    """
    )

    ctx_orphan_check = (
        op.get_bind()
        .execute(
            sa.text(
                """
        SELECT COUNT(*) FROM ag_catalog.contexts c
        WHERE c.user_id NOT IN (SELECT id FROM public.users);
    """
            )
        )
        .scalar()
    )

    if ctx_orphan_check == 0:
        op.execute(
            """
            ALTER TABLE ag_catalog.contexts
            ADD CONSTRAINT contexts_user_id_fkey
            FOREIGN KEY (user_id) REFERENCES public.users(id);
        """
        )
        print("   ✅ Fixed contexts FK")
    else:
        print(f"   ⚠️  Skipping contexts FK - {ctx_orphan_check} orphaned records found")

    # Step 7: Set default search path
    print("🔧 Step 7: Setting search path...")
    op.execute(
        """
        ALTER DATABASE ninaivalaigal_dev
        SET search_path = public, ag_catalog, pg_catalog;
    """
    )

    # Step 8: Initial refresh of materialized view
    print("🔄 Step 8: Initial refresh of materialized view...")
    op.execute("REFRESH MATERIALIZED VIEW ag_catalog.users;")

    # Step 9: Verify integrity
    print("✅ Step 9: Verifying data integrity...")
    result = (
        op.get_bind()
        .execute(
            sa.text(
                """
        SELECT
            (SELECT COUNT(*) FROM public.users) as public_count,
            (SELECT COUNT(*) FROM ag_catalog.users) as ag_catalog_count;
    """
            )
        )
        .fetchone()
    )

    print(f"   public.users: {result[0]} rows")
    print(f"   ag_catalog.users (MV): {result[1]} rows")

    if result[0] != result[1]:
        raise Exception(f"Row count mismatch! public: {result[0]}, ag_catalog: {result[1]}")

    print("✅ Migration complete! Single source of truth established.")


def downgrade():
    """Revert to dual user tables (NOT RECOMMENDED)"""

    print("⚠️  WARNING: Reverting to dual user tables...")

    # Drop materialized view
    op.execute("DROP MATERIALIZED VIEW IF EXISTS ag_catalog.users CASCADE;")

    # Restore from backup
    op.execute(
        """
        CREATE TABLE ag_catalog.users AS
        TABLE ag_catalog.users_backup;
    """
    )

    # Restore FKs to point to ag_catalog (this will likely fail if data diverged)
    print("⚠️  Note: Foreign keys NOT restored to ag_catalog - manual intervention required")
    print("⚠️  All FKs remain pointing to public.users for safety")
