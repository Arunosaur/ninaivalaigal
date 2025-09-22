#!/bin/bash

echo "=== Testing Colima for Postgres + pgvector ==="

# Check current Docker context
echo "Current Docker context:"
docker context list

echo -e "\n=== Testing Postgres with pgvector via Colima ==="

# Create a test docker-compose for Colima
cat > /tmp/colima-postgres-test.yml << 'EOF'
version: '3.8'
services:
  postgres:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: postgres
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 5s
      retries: 5

volumes:
  postgres_data:
EOF

echo "Starting Postgres via Colima..."
docker-compose -f /tmp/colima-postgres-test.yml up -d

echo -e "\n=== Waiting for Postgres to be ready ==="
timeout 30 bash -c 'until docker-compose -f /tmp/colima-postgres-test.yml exec postgres pg_isready -U postgres; do sleep 1; done'

if [ $? -eq 0 ]; then
    echo "✅ Postgres is ready!"

    echo -e "\n=== Testing pgvector extension ==="
    docker-compose -f /tmp/colima-postgres-test.yml exec postgres psql -U postgres -c "CREATE EXTENSION IF NOT EXISTS vector;"
    docker-compose -f /tmp/colima-postgres-test.yml exec postgres psql -U postgres -c "SELECT extname FROM pg_extension WHERE extname = 'vector';"

    echo -e "\n=== Resource usage ==="
    docker stats --no-stream

    echo -e "\n=== Colima VM stats ==="
    colima status

else
    echo "❌ Postgres failed to start"
fi

echo -e "\n=== Cleanup ==="
docker-compose -f /tmp/colima-postgres-test.yml down -v
rm /tmp/colima-postgres-test.yml

echo -e "\n=== Performance comparison ready ==="
echo "Next: Compare with Docker Desktop if needed"
