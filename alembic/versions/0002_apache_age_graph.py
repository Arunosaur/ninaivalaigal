"""Apache AGE Graph Initialization

Revision ID: 0002_apache_age_graph
Revises: 0001_extensions
Create Date: 2025-10-10 22:01:00.000000

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "0002_apache_age_graph"
down_revision = "0001_extensions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create Apache AGE graph with all vertex and edge labels."""

    # Load AGE extension and set search path
    op.execute("LOAD 'age';")
    op.execute("SET search_path = ag_catalog, '$user', public;")

    # Create the main graph for ninaivalaigal intelligence
    op.execute("SELECT ag_catalog.create_graph('ninaivalaigal_intelligence');")

    # Create vertex labels (node types)
    vertex_labels = [
        "User",
        "Memory",
        "Context",
        "Agent",
        "Team",
        "Organization",
        "Session",
        "Macro",
        "Token",
        "Narrative",
    ]

    for label in vertex_labels:
        op.execute(f"SELECT ag_catalog.create_vlabel('ninaivalaigal_intelligence', '{label}');")

    # Create edge labels (relationship types)
    edge_labels = [
        "CREATED",
        "ACCESSED",
        "BELONGS_TO",
        "MEMBER_OF",
        "OWNS",
        "LINKED_TO",
        "SIMILAR_TO",
        "REFERENCES",
        "TAGGED_WITH",
        "EXECUTED",
        "CONTAINS",
        "SHARED_WITH",
        "DERIVED_FROM",
        "FEEDBACK",
        "SUGGESTS",
        "RELATED_TO",
        "INFLUENCED_BY",
        "PROMOTED_BY",
        "ANNOTATED_BY",
        "FOLLOWED",
        "COLLABORATED_ON",
    ]

    for label in edge_labels:
        op.execute(f"SELECT ag_catalog.create_elabel('ninaivalaigal_intelligence', '{label}');")

    # Create view for graph statistics
    op.execute(
        """
        CREATE OR REPLACE VIEW graph_stats AS
        SELECT
            'ninaivalaigal_intelligence' as graph_name,
            COALESCE((SELECT count(*) FROM ag_catalog.ag_label WHERE name LIKE '%' AND kind = 'v'), 0) as node_types,
            COALESCE((SELECT count(*) FROM ag_catalog.ag_label WHERE name LIKE '%' AND kind = 'e'), 0) as edge_types,
            'Graph schema initialized' as status;
    """
    )


def downgrade() -> None:
    """Drop the Apache AGE graph."""

    # Drop the view first
    op.execute("DROP VIEW IF EXISTS graph_stats;")

    # Drop the entire graph (cascades to all labels and tables)
    op.execute("SELECT ag_catalog.drop_graph('ninaivalaigal_intelligence', true);")
