# Ninaivalaigal Database Image

**Production-grade PostgreSQL 15 with all required extensions for the Ninaivalaigal platform.**

## 📦 What's Included

### Core Extensions (Must Have)
- **pgvector** - Vector embeddings for AI/ML (SPEC-061, SPEC-040)
- **Apache AGE** - Graph database functionality (SPEC-061)
- **pg_stat_statements** - Query performance monitoring (SPEC-018)
- **auto_explain** - Automatic query plan logging (SPEC-069)
- **pg_repack** - Online table reorganization (SPEC-019)
- **pg_cron** - Scheduled tasks (SPEC-071)
- **citext** - Case-insensitive text (SPEC-002)
- **pgcrypto** - Cryptographic functions (SPEC-008)
- **pgAudit** - Audit logging (SPEC-065)

### Complementary Extensions
- **uuid-ossp** - UUID generation
- **pg_similarity** - Similarity measures for RAG (SPEC-041)

### Platform Support
- ✅ **linux/arm64** (Apple Silicon, ARM servers)
- ✅ **linux/amd64** (Intel/AMD x86_64)

---

## 🚀 Quick Start

### Option 1: Use Pre-Built Image (Recommended)
```bash
# Pull from GitHub Container Registry
docker pull ghcr.io/arunosaur/ninaivalaigal-db:1.0.0

# Use in docker-compose
image: ghcr.io/arunosaur/ninaivalaigal-db:1.0.0
```

### Option 2: Build Locally
```bash
# Build for your architecture
cd containers/ninaivalaigal-db
docker build --platform linux/arm64 -t ninaivalaigal-db:local .

# Or for x86_64
docker build --platform linux/amd64 -t ninaivalaigal-db:local .
```

### Option 3: Build and Push to Registry
```bash
# Login to GitHub Container Registry
echo $GITHUB_TOKEN | docker login ghcr.io -u USERNAME --password-stdin

# Build and push multi-arch image
cd containers/ninaivalaigal-db
./build-and-push.sh 1.0.0
```

---

## 🔧 Configuration

### Environment Variables
```bash
POSTGRES_DB=ninaivalaigal_dev          # Database name
POSTGRES_USER=nina                      # Database user
POSTGRES_PASSWORD=secure_password       # Database password
POSTGRES_HOST_AUTH_METHOD=md5          # Authentication method
```

### Enabled Extensions
All extensions are enabled automatically on first startup via:
- `/docker-entrypoint-initdb.d/01-init-extensions.sql`
- `/docker-entrypoint-initdb.d/02-init-config.sql`

### Performance Tuning
The image includes pre-configured settings for:
- Query monitoring (pg_stat_statements)
- Automatic query explain (auto_explain for queries > 1s)
- Audit logging (pgAudit for write/DDL operations)
- Scheduled cleanup (pg_cron daily at 2 AM)

---

## 📊 Extension Usage

### pgvector (AI Embeddings)
```sql
-- Create table with vector column
CREATE TABLE documents (
    id UUID PRIMARY KEY,
    content TEXT,
    embedding vector(1536)  -- OpenAI embeddings
);

-- Vector similarity search
SELECT * FROM documents
ORDER BY embedding <-> '[0.1, 0.2, ...]'::vector
LIMIT 10;
```

### Apache AGE (Graph Database)
```sql
-- Load AGE extension
LOAD 'age';
SET search_path = ag_catalog, "$user", public;

-- Create graph
SELECT create_graph('knowledge_graph');

-- Query graph
SELECT * FROM cypher('knowledge_graph', $$
    MATCH (n:Person)-[:KNOWS]->(m:Person)
    RETURN n.name, m.name
$$) AS (person1 agtype, person2 agtype);
```

### pg_cron (Scheduled Tasks)
```sql
-- Schedule daily cleanup
SELECT cron.schedule(
    'daily-cleanup',
    '0 2 * * *',
    'VACUUM ANALYZE;'
);

-- View scheduled jobs
SELECT * FROM cron.job;
```

---

## 🐛 Troubleshooting

### Image Won't Build
```bash
# Clean build cache
docker buildx prune -a

# Rebuild from scratch
docker build --no-cache --platform linux/arm64 -t ninaivalaigal-db:local .
```

### Extension Not Found
```bash
# Check installed extensions
docker exec -it <container> psql -U nina -d ninaivalaigal_dev -c "\dx"

# Check shared libraries
docker exec -it <container> ls -la /usr/lib/postgresql/15/lib/
```

### Segmentation Fault
This usually indicates:
1. **Architecture mismatch** - Ensure platform matches your system
2. **Corrupted build** - Rebuild with `--no-cache`
3. **Version conflict** - Check PostgreSQL and extension versions

**Solution:**
```bash
# Stop and remove old containers/volumes
docker compose down -v

# Pull/build fresh image
docker pull ghcr.io/arunosaur/ninaivalaigal-db:1.0.0

# Start with clean state
docker compose up -d
```

---

## 📝 Version History

### v1.0.0 (2025-10-05)
- Initial stable release
- PostgreSQL 15.14
- pgvector 0.5.1
- Apache AGE 1.5.0-rc0
- All core extensions enabled
- Multi-arch support (ARM64 + AMD64)

---

## 🔐 Security Notes

1. **Always change default passwords** in production
2. **pgAudit is enabled** - logs all DDL and write operations
3. **pg_cron requires** `cron.database_name` to be set
4. **SSL/TLS** - Enable in production with proper certificates

---

## 📚 References

- [pgvector Documentation](https://github.com/pgvector/pgvector)
- [Apache AGE Documentation](https://age.apache.org/)
- [PostgreSQL Extensions](https://www.postgresql.org/docs/15/contrib.html)
- [Ninaivalaigal Specifications](../../docs/SPECS.md)

---

**Maintained by:** Arunosaur/Ninaivalaigal Team
**License:** Same as Ninaivalaigal project
**Registry:** ghcr.io/arunosaur/ninaivalaigal-db
