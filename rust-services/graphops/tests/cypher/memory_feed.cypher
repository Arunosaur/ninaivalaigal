// Returning list of maps to satisfy MCP ingestion expectations.
MATCH (u:User {id: 'perf_user_001'})-[:CREATED]->(m:Memory)
RETURN {memory_id: m.id, title: m.title, memory_type: m.type}
ORDER BY m.id
LIMIT 20
