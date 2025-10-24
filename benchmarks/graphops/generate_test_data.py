#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Medhasys LLC
#
"""
Generate realistic test data for GraphOps performance validation.

This creates a dataset large enough to validate that GIN indexes
provide actual performance benefits for Apache AGE Cypher queries.

Based on US #86 findings: need 10,000+ rows to see index benefits.
"""

import argparse
import random
import sys
from datetime import datetime, timedelta
from typing import List
from uuid import uuid4

import psycopg2
from psycopg2.extras import execute_batch


def generate_users(count: int = 1000) -> List[dict]:
    """Generate test users."""
    users = []
    for i in range(count):
        users.append(
            {
                "id": f"test_user_{i:06d}",
                "email": f"user{i}@test.ninaivalaigal.com",
                "name": f"Test User {i}",
                "created_at": datetime.now() - timedelta(days=random.randint(1, 365)),
            }
        )
    return users


def generate_memories(count: int = 10000, user_count: int = 1000) -> List[dict]:
    """Generate test memories distributed across users."""
    memories = []
    topics = [
        "engineering",
        "product",
        "design",
        "research",
        "planning",
        "meeting",
        "documentation",
        "architecture",
        "testing",
        "deployment",
    ]
    types = ["note", "decision", "discussion", "action-item", "reference"]

    for i in range(count):
        user_idx = i % user_count
        memories.append(
            {
                "id": f"test_memory_{i:08d}",
                "user_id": f"test_user_{user_idx:06d}",
                "title": f"Memory {i}: {random.choice(topics).title()} Notes",
                "content": f"This is test memory content for validation. Index: {i}. " * 10,
                "type": random.choice(types),
                "created_at": datetime.now() - timedelta(days=random.randint(1, 180)),
                "tags": random.sample(topics, random.randint(1, 3)),
            }
        )
    return memories


def generate_contexts(count: int = 1000, user_count: int = 1000) -> List[dict]:
    """Generate test contexts."""
    contexts = []
    context_types = ["project", "team", "customer", "research", "product"]

    for i in range(count):
        contexts.append(
            {
                "id": f"test_context_{i:06d}",
                "user_id": f"test_user_{i % user_count:06d}",
                "name": f"Test Context {i}",
                "type": random.choice(context_types),
                "created_at": datetime.now() - timedelta(days=random.randint(1, 365)),
            }
        )
    return contexts


def generate_teams(count: int = 100) -> List[dict]:
    """Generate test teams."""
    teams = []
    for i in range(count):
        teams.append(
            {
                "id": f"test_team_{i:04d}",
                "name": f"Test Team {i}",
                "created_at": datetime.now() - timedelta(days=random.randint(1, 730)),
            }
        )
    return teams


def insert_graph_data(
    conn, graph_name: str, users: List[dict], memories: List[dict], contexts: List[dict], teams: List[dict]
):
    """Insert data into Apache AGE graph."""

    cur = conn.cursor()

    # Load AGE extension
    cur.execute("LOAD 'age';")
    cur.execute(f"SET search_path = {graph_name}, ag_catalog, public;")

    print("📊 Inserting Users...")
    for user in users:
        cypher = f"""
        SELECT * FROM cypher('{graph_name}', $$
            CREATE (u:User {{
                id: '{user['id']}',
                email: '{user['email']}',
                name: '{user['name']}',
                created_at: '{user['created_at'].isoformat()}'
            }})
        $$) as (result agtype);
        """
        cur.execute(cypher)

    print("📊 Inserting Memories...")
    batch_size = 100
    for i in range(0, len(memories), batch_size):
        batch = memories[i : i + batch_size]
        for memory in batch:
            tags_str = ", ".join([f'"{t}"' for t in memory["tags"]])
            cypher = f"""
            SELECT * FROM cypher('{graph_name}', $$
                CREATE (m:Memory {{
                    id: '{memory['id']}',
                    user_id: '{memory['user_id']}',
                    title: '{memory['title']}',
                    content: '{memory['content'][:200]}',
                    type: '{memory['type']}',
                    created_at: '{memory['created_at'].isoformat()}',
                    tags: [{tags_str}]
                }})
            $$) as (result agtype);
            """
            cur.execute(cypher)

        conn.commit()
        print(f"  ✅ Inserted {i+len(batch)}/{len(memories)} memories")

    print("📊 Inserting Contexts...")
    for context in contexts:
        cypher = f"""
        SELECT * FROM cypher('{graph_name}', $$
            CREATE (c:Context {{
                id: '{context['id']}',
                user_id: '{context['user_id']}',
                name: '{context['name']}',
                type: '{context['type']}',
                created_at: '{context['created_at'].isoformat()}'
            }})
        $$) as (result agtype);
        """
        cur.execute(cypher)

    print("📊 Inserting Teams...")
    for team in teams:
        cypher = f"""
        SELECT * FROM cypher('{graph_name}', $$
            CREATE (t:Team {{
                id: '{team['id']}',
                name: '{team['name']}',
                created_at: '{team['created_at'].isoformat()}'
            }})
        $$) as (result agtype);
        """
        cur.execute(cypher)

    print("📊 Creating Relationships...")

    # CREATED relationships (User -> Memory)
    print("  Creating CREATED edges...")
    for i, memory in enumerate(memories):
        if i % 1000 == 0:
            print(f"    {i}/{len(memories)} CREATED edges...")
        cypher = f"""
        SELECT * FROM cypher('{graph_name}', $$
            MATCH (u:User {{id: '{memory['user_id']}'}}),
                  (m:Memory {{id: '{memory['id']}'}})
            CREATE (u)-[:CREATED {{timestamp: '{memory['created_at'].isoformat()}'}}]->(m)
        $$) as (result agtype);
        """
        cur.execute(cypher)

        if i % 100 == 0:
            conn.commit()

    # TAGGED_WITH relationships (Memory -> Topic)
    print("  Creating TAGGED_WITH edges...")
    tag_count = 0
    for memory in memories:
        for tag in memory["tags"]:
            cypher = f"""
            SELECT * FROM cypher('{graph_name}', $$
                MATCH (m:Memory {{id: '{memory['id']}'}})
                MERGE (topic:Topic {{name: '{tag}'}})
                CREATE (m)-[:TAGGED_WITH]->(topic)
            $$) as (result agtype);
            """
            cur.execute(cypher)
            tag_count += 1

            if tag_count % 100 == 0:
                conn.commit()

    conn.commit()
    cur.close()

    print("✅ All data inserted successfully!")


def main():
    parser = argparse.ArgumentParser(description="Generate GraphOps test data")
    parser.add_argument("--users", type=int, default=1000, help="Number of users")
    parser.add_argument("--memories", type=int, default=10000, help="Number of memories")
    parser.add_argument("--contexts", type=int, default=1000, help="Number of contexts")
    parser.add_argument("--teams", type=int, default=100, help="Number of teams")
    parser.add_argument("--db-host", default="localhost", help="Database host")
    parser.add_argument("--db-port", type=int, default=5432, help="Database port")
    parser.add_argument("--db-name", default="ninaivalaigal_dev", help="Database name")
    parser.add_argument("--db-user", default="nina", help="Database user")
    parser.add_argument("--db-password", default="dev_password_change_in_production", help="Database password")
    parser.add_argument("--graph-name", default="ninaivalaigal_intelligence_dev", help="Graph name")

    args = parser.parse_args()

    print("🚀 GraphOps Test Data Generator")
    print("=" * 80)
    print(f"Users:    {args.users:,}")
    print(f"Memories: {args.memories:,}")
    print(f"Contexts: {args.contexts:,}")
    print(f"Teams:    {args.teams:,}")
    print("=" * 80)

    # Generate data
    print("\n📝 Generating data...")
    users = generate_users(args.users)
    memories = generate_memories(args.memories, args.users)
    contexts = generate_contexts(args.contexts, args.users)
    teams = generate_teams(args.teams)

    print(f"✅ Generated {len(users):,} users")
    print(f"✅ Generated {len(memories):,} memories")
    print(f"✅ Generated {len(contexts):,} contexts")
    print(f"✅ Generated {len(teams):,} teams")

    # Connect to database
    print(f"\n🔗 Connecting to {args.db_host}:{args.db_port}/{args.db_name}...")
    try:
        conn = psycopg2.connect(
            host=args.db_host, port=args.db_port, database=args.db_name, user=args.db_user, password=args.db_password
        )
        print("✅ Connected successfully")

        # Insert data
        print(f"\n📊 Inserting data into graph '{args.graph_name}'...")
        insert_graph_data(conn, args.graph_name, users, memories, contexts, teams)

        conn.close()
        print("\n✅ Test data generation complete!")

        # Print summary
        print("\n" + "=" * 80)
        print("📊 Data Summary:")
        print(f"  Users:          {len(users):,}")
        print(f"  Memories:       {len(memories):,}")
        print(f"  Contexts:       {len(contexts):,}")
        print(f"  Teams:          {len(teams):,}")
        print(f"  Relationships:  ~{len(memories) * 2:,} (est.)")
        print("=" * 80)
        print("\n🎯 Next Steps:")
        print("  1. Run benchmark: make graphops-benchmark")
        print("  2. Check EXPLAIN plans to verify index usage")
        print("  3. Compare with US #86 baseline (6 rows)")
        print("=" * 80)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
