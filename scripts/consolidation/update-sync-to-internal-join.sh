#!/bin/bash
# ============================================================================
# SINGLE DATABASE CONSOLIDATION: Update Sync Scripts for Internal Operations
# ============================================================================
# Converts external sync scripts to use internal SQL+Cypher operations
# Eliminates cross-database synchronization complexity

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="${SCRIPT_DIR}/sync-update-$(date +%Y%m%d-%H%M%S).log"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "$LOG_FILE"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$LOG_FILE"
}

# Update graph intelligence integration API
update_graph_intelligence_api() {
    log "Updating graph intelligence integration API..."

    local api_file="server/graph_intelligence_integration_api.py"

    if [[ -f "$api_file" ]]; then
        # Backup original
        cp "$api_file" "${api_file}.backup-$(date +%Y%m%d-%H%M%S)"

        # Update connection logic to use single database
        sed -i.tmp 's/graph_db_host/nv_db_host/g' "$api_file"
        sed -i.tmp 's/graph_db_port/nv_db_port/g' "$api_file"
        sed -i.tmp 's/separate.*graph.*database/consolidated database with Apache AGE/g' "$api_file"

        rm -f "${api_file}.tmp"
        success "Updated $api_file"
    else
        warning "$api_file not found"
    fi
}

# Create new internal sync functions
create_internal_sync_functions() {
    log "Creating internal sync functions..."

    cat > "server/internal_graph_sync.py" << 'EOF'
"""
Internal Graph Synchronization for Consolidated Database
Replaces external sync with internal SQL+Cypher operations
"""

import asyncio
from typing import Dict, List
from sqlalchemy import text
from database import get_db

class InternalGraphSync:
    """Handles synchronization within single database using SQL+Cypher"""

    def __init__(self, db_session):
        self.db = db_session

    async def sync_memories_to_graph(self) -> Dict[str, int]:
        """Sync memories from relational tables to graph nodes"""

        # Use SQL to get memories, then Cypher to create nodes
        result = await self.db.execute(text("""
            WITH memory_data AS (
                SELECT id, content, user_id, created_at
                FROM memories
                WHERE updated_at > NOW() - INTERVAL '1 hour'
            )
            SELECT ag_catalog.cypher('ninaivalaigal_intelligence', $$
                UNWIND $memory_list AS mem
                MERGE (m:Memory {id: mem.id})
                SET m.content = mem.content,
                    m.user_id = mem.user_id,
                    m.synced_at = timestamp()
                RETURN m
            $$, jsonb_build_object('memory_list',
                jsonb_agg(jsonb_build_object(
                    'id', id::text,
                    'content', content,
                    'user_id', user_id::text
                ))
            )) FROM memory_data;
        """))

        return {"memories_synced": result.rowcount}

    async def create_user_memory_relationships(self) -> Dict[str, int]:
        """Create relationships between users and memories"""

        result = await self.db.execute(text("""
            SELECT ag_catalog.cypher('ninaivalaigal_intelligence', $$
                MATCH (u:User), (m:Memory)
                WHERE u.id = m.user_id
                MERGE (u)-[r:CREATED]->(m)
                SET r.created_at = timestamp()
                RETURN count(r) as relationships_created
            $$);
        """))

        return {"relationships_created": result.scalar()}

# Usage example
async def perform_internal_sync():
    """Main sync function using internal operations"""
    async with get_db() as db:
        sync = InternalGraphSync(db)

        # Sync data internally
        memory_result = await sync.sync_memories_to_graph()
        relationship_result = await sync.create_user_memory_relationships()

        return {
            **memory_result,
            **relationship_result
        }
EOF

    success "Created internal sync functions"
}

# Update Makefile targets
update_makefile_targets() {
    log "Updating Makefile targets..."

    if [[ -f "Makefile" ]]; then
        # Backup
        cp "Makefile" "Makefile.backup-$(date +%Y%m%d-%H%M%S)"

        # Remove old graph targets and add new ones
        cat >> "Makefile" << 'EOF'

# ============================================================================
# CONSOLIDATED DATABASE TARGETS (Single PostgreSQL + Apache AGE)
# ============================================================================

install-age-in-nv-db:
	@echo "Installing Apache AGE in nv-db..."
	container exec nv-db psql -U nina -d nina -f /tmp/install-age-in-nv-db.sql

sync-internal-graph:
	@echo "Running internal graph synchronization..."
	python -c "import asyncio; from server.internal_graph_sync import perform_internal_sync; asyncio.run(perform_internal_sync())"

test-consolidated-graph:
	@echo "Testing consolidated graph functionality..."
	container exec nv-db psql -U nina -d nina -c "LOAD 'age'; SET search_path = ag_catalog, \"\$$user\", public; SELECT * FROM cypher('ninaivalaigal_intelligence', \$$\$$ MATCH (n) RETURN count(n) \$$\$$) as (node_count agtype);"

health-check-consolidated:
	@echo "Checking consolidated database health..."
	@curl -s http://localhost:13370/health
	@echo ""
	@curl -s http://localhost:13370/graph-intelligence/health

EOF

        success "Updated Makefile with consolidated targets"
    fi
}

main() {
    log "Starting sync script consolidation..."

    update_graph_intelligence_api
    create_internal_sync_functions
    update_makefile_targets

    success "Sync script consolidation completed!"
    success "New internal sync functions created"
    success "Makefile updated with consolidated targets"

    log "Next steps:"
    log "1. Test internal sync: make sync-internal-graph"
    log "2. Test consolidated health: make health-check-consolidated"
    log "3. Update application code to use internal sync"
}

main "$@"
