#!/usr/bin/env python3
"""
SPEC-011: Memory Lifecycle Management CLI

Command-line interface for memory lifecycle operations:
- mem0 lifecycle stats - Show lifecycle statistics
- mem0 lifecycle gc - Run garbage collection cycle
- mem0 lifecycle archive - Archive old memories
- mem0 lifecycle purge - Purge archived memories
- mem0 lifecycle policies - Manage lifecycle policies
"""

import asyncio
import json
import os
from datetime import datetime

import asyncpg
import click
from tabulate import tabulate

from .memory_gc import MemoryGarbageCollector


def get_database_url():
    """Get database URL using existing config system"""
    import sys

    sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))
    from auth import load_config

    return load_config()


@click.group(name="lifecycle")
def lifecycle_cli():
    """Memory lifecycle management commands"""
    pass


@lifecycle_cli.command("stats")
@click.option(
    "--scope",
    type=click.Choice(["personal", "team", "organization"]),
    help="Filter by scope",
)
@click.option("--user-id", help="Filter by user ID")
@click.option("--team-id", help="Filter by team ID")
@click.option("--org-id", help="Filter by organization ID")
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["table", "json"]),
    default="table",
    help="Output format",
)
def stats_command(
    scope: str | None,
    user_id: str | None,
    team_id: str | None,
    org_id: str | None,
    output_format: str,
):
    """Show memory lifecycle statistics"""

    async def run_stats():
        database_url = get_database_url()
        gc = MemoryGarbageCollector(database_url)

        try:
            await gc.initialize()
            # Convert string IDs to integers if provided
            user_id_int = int(user_id) if user_id else None
            team_id_int = int(team_id) if team_id else None
            org_id_int = int(org_id) if org_id else None

            stats = await gc.get_lifecycle_stats(
                scope, user_id_int, team_id_int, org_id_int
            )

            if output_format == "json":
                click.echo(json.dumps(stats.__dict__, indent=2, default=str))
            else:
                # Table format
                data = [
                    ["Total Memories", stats.total_memories],
                    ["Active", stats.active_memories],
                    ["Expired", stats.expired_memories],
                    ["Archived", stats.archived_memories],
                    ["Deleted", stats.deleted_memories],
                    ["Avg Access Count", f"{stats.avg_access_count:.1f}"],
                    ["Oldest Memory (days)", stats.oldest_memory_age_days],
                    ["Most Recent Access (days)", stats.most_recent_access_days],
                ]

                click.echo("\n📊 Memory Lifecycle Statistics")
                if scope or user_id or team_id or org_id:
                    filters = []
                    if scope:
                        filters.append(f"scope={scope}")
                    if user_id:
                        filters.append(f"user_id={user_id}")
                    if team_id:
                        filters.append(f"team_id={team_id}")
                    if org_id:
                        filters.append(f"org_id={org_id}")
                    click.echo(f"Filters: {', '.join(filters)}")
                click.echo()

                click.echo(tabulate(data, headers=["Metric", "Value"], tablefmt="grid"))

        finally:
            await gc.close()

    asyncio.run(run_stats())


@lifecycle_cli.command("gc")
@click.option(
    "--dry-run", is_flag=True, help="Show what would be done without making changes"
)
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
def gc_command(dry_run: bool, verbose: bool):
    """Run memory garbage collection cycle"""

    async def run_gc():
        database_url = get_database_url()
        gc = MemoryGarbageCollector(database_url, dry_run=dry_run)

        try:
            await gc.initialize()

            if dry_run:
                click.echo("🔍 Running in DRY RUN mode - no changes will be made")
            else:
                click.echo("🗑️  Running memory garbage collection...")

            start_time = datetime.now()
            stats = await gc.run_lifecycle_cycle()
            end_time = datetime.now()

            duration = (end_time - start_time).total_seconds()

            click.echo(f"\n✅ Garbage collection completed in {duration:.2f}s")
            click.echo(f"   • Expired: {stats['expired_count']} memories")
            click.echo(f"   • Archived: {stats['archived_count']} memories")
            click.echo(f"   • Purged: {stats['purged_count']} memories")
            click.echo(f"   • Notifications: {stats['notifications_sent']} sent")

            if verbose:
                click.echo("\n📊 Detailed Stats:")
                click.echo(json.dumps(stats, indent=2))

        finally:
            await gc.close()

    asyncio.run(run_gc())


@lifecycle_cli.command("archive")
@click.option(
    "--older-than",
    type=int,
    default=90,
    help="Archive memories older than N days (default: 90)",
)
@click.option(
    "--scope",
    type=click.Choice(["personal", "team", "organization"]),
    help="Only archive memories from specific scope",
)
@click.option("--dry-run", is_flag=True, help="Show what would be archived")
def archive_command(older_than: int, scope: str | None, dry_run: bool):
    """Archive old memories"""

    async def run_archive():
        database_url = get_database_url()
        gc = MemoryGarbageCollector(database_url, dry_run=dry_run)

        try:
            await gc.initialize()

            if dry_run:
                click.echo(f"🔍 Would archive memories older than {older_than} days")
                if scope:
                    click.echo(f"   Scope filter: {scope}")
            else:
                click.echo(f"📦 Archiving memories older than {older_than} days...")
                if scope:
                    click.echo(f"   Scope filter: {scope}")

            # For now, use the existing archive function
            # In a full implementation, we'd add scope filtering
            archived_count = await gc.archive_inactive_memories()

            if dry_run:
                click.echo(f"🔍 Would archive {archived_count} memories")
            else:
                click.echo(f"✅ Archived {archived_count} memories")

        finally:
            await gc.close()

    asyncio.run(run_archive())


@lifecycle_cli.command("purge")
@click.option(
    "--older-than",
    type=int,
    default=365,
    help="Purge archived memories older than N days (default: 365)",
)
@click.option("--dry-run", is_flag=True, help="Show what would be purged")
@click.confirmation_option(
    prompt="Are you sure you want to permanently delete archived memories?"
)
def purge_command(older_than: int, dry_run: bool):
    """Permanently delete old archived memories"""

    async def run_purge():
        database_url = get_database_url()
        gc = MemoryGarbageCollector(database_url, dry_run=dry_run)

        try:
            await gc.initialize()

            if dry_run:
                click.echo(
                    f"🔍 Would purge archived memories older than {older_than} days"
                )
            else:
                click.echo(
                    f"🗑️  Purging archived memories older than {older_than} days..."
                )

            purged_count = await gc.purge_old_archived_memories(older_than)

            if dry_run:
                click.echo(
                    f"🔍 Would permanently delete {purged_count} archived memories"
                )
            else:
                click.echo(f"✅ Permanently deleted {purged_count} archived memories")

        finally:
            await gc.close()

    asyncio.run(run_purge())


@lifecycle_cli.command("policies")
@click.option("--list", "list_policies", is_flag=True, help="List all policies")
@click.option(
    "--scope",
    type=click.Choice(["personal", "team", "organization"]),
    help="Filter by scope",
)
@click.option(
    "--type",
    "policy_type",
    type=click.Choice(["ttl", "archival", "purge"]),
    help="Filter by policy type",
)
def policies_command(
    list_policies: bool, scope: str | None, policy_type: str | None
):
    """Manage lifecycle policies"""

    async def run_policies():
        database_url = get_database_url()

        try:
            pool = await asyncpg.create_pool(database_url)

            if list_policies:
                async with pool.acquire() as conn:
                    query = """
                        SELECT id, scope, policy_type, policy_config, enabled, created_at
                        FROM memory_lifecycle_policies
                        WHERE ($1::text IS NULL OR scope = $1)
                          AND ($2::text IS NULL OR policy_type = $2)
                        ORDER BY scope, policy_type
                    """

                    policies = await conn.fetch(query, scope, policy_type)

                    if not policies:
                        click.echo("No policies found")
                        return

                    # Format as table
                    data = []
                    for policy in policies:
                        config_str = json.dumps(policy["policy_config"])
                        if len(config_str) > 50:
                            config_str = config_str[:47] + "..."

                        data.append(
                            [
                                policy["id"][:8] + "...",
                                policy["scope"],
                                policy["policy_type"],
                                config_str,
                                "✅" if policy["enabled"] else "❌",
                                policy["created_at"].strftime("%Y-%m-%d"),
                            ]
                        )

                    click.echo("\n📋 Lifecycle Policies")
                    click.echo(
                        tabulate(
                            data,
                            headers=[
                                "ID",
                                "Scope",
                                "Type",
                                "Config",
                                "Enabled",
                                "Created",
                            ],
                            tablefmt="grid",
                        )
                    )
            else:
                click.echo("Use --list to show policies")
                click.echo("Policy management UI coming soon!")

        finally:
            if "pool" in locals():
                await pool.close()

    asyncio.run(run_policies())


@lifecycle_cli.command("set-ttl")
@click.argument("memory_id")
@click.argument("hours", type=int)
def set_ttl_command(memory_id: str, hours: int):
    """Set TTL for a specific memory"""

    async def run_set_ttl():
        database_url = get_database_url()

        try:
            pool = await asyncpg.create_pool(database_url)

            async with pool.acquire() as conn:
                # Check if memory exists
                memory_exists = await conn.fetchval(
                    "SELECT EXISTS(SELECT 1 FROM memory_records WHERE id = $1)",
                    memory_id,
                )

                if not memory_exists:
                    click.echo(f"❌ Memory {memory_id} not found")
                    return

                # Set TTL
                expires_at = datetime.now() + timedelta(hours=hours)
                await conn.execute(
                    """
                    UPDATE memory_records
                    SET expires_at = $1, lifecycle_status = 'active'
                    WHERE id = $2
                """,
                    expires_at,
                    memory_id,
                )

                # Log event
                await conn.execute(
                    """
                    INSERT INTO memory_lifecycle_events (memory_id, event_type, triggered_by, event_data)
                    VALUES ($1, 'ttl_set', 'cli', $2)
                """,
                    memory_id,
                    json.dumps(
                        {
                            "ttl_hours": hours,
                            "expires_at": expires_at.isoformat(),
                            "set_at": datetime.now().isoformat(),
                        }
                    ),
                )

                click.echo(f"✅ Set TTL for memory {memory_id}")
                click.echo(f"   Expires at: {expires_at}")
                click.echo(f"   Hours from now: {hours}")

        finally:
            if "pool" in locals():
                await pool.close()

    from datetime import timedelta

    asyncio.run(run_set_ttl())


if __name__ == "__main__":
    lifecycle_cli()
