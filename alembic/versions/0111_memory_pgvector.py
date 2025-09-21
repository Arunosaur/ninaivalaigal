"""init pgvector memory schema"""

from alembic import op

revision = '0111_memory_pgvector'
down_revision = None
branch_labels = None
depends_on = None
def upgrade():
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto;")
    op.execute("CREATE EXTENSION IF NOT EXISTS vector;")
    op.execute('''
    CREATE TABLE IF NOT EXISTS memory_records (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      scope TEXT NOT NULL CHECK (scope IN ('personal','team','organization')),
      user_id TEXT NOT NULL,
      team_id TEXT,
      org_id  TEXT,
      kind    TEXT NOT NULL,
      text    TEXT NOT NULL,
      metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
      embedding vector(8),
      created_at TIMESTAMPTZ NOT NULL DEFAULT now()
    );
    ''')
def downgrade():
    op.execute("DROP TABLE IF EXISTS memory_records;")
