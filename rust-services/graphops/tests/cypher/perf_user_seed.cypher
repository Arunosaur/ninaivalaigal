MERGE (u1:User {id: 'perf_user_001'})
SET u1.name = 'Performance Persona',
    u1.email = 'perf_user_001@ninaivalaigal.dev',
    u1.role = 'developer',
    u1.team_id = 'team_perf_core',
    u1.organization_id = 'org_perf'
WITH u1
UNWIND [
  {id: 'perf_mem_001', title: 'PgBouncer Dual Mode Design', type: 'architecture', topics: ['performance', 'database'], score: 0.96},
  {id: 'perf_mem_002', title: 'GraphOps Query Optimizations', type: 'research', topics: ['graph', 'performance'], score: 0.92},
  {id: 'perf_mem_003', title: 'Customer Memory Recall', type: 'product', topics: ['memory', 'customer'], score: 0.88},
  {id: 'perf_mem_004', title: 'Latency Budget Analysis', type: 'analysis', topics: ['performance', 'benchmark'], score: 0.95},
  {id: 'perf_mem_005', title: 'GraphOps Alert Playbook', type: 'runbook', topics: ['operations', 'graph'], score: 0.90},
  {id: 'perf_mem_006', title: 'Task 92 Benchmark Inputs', type: 'analysis', topics: ['benchmark', 'planning'], score: 0.91}
] AS mem
MERGE (m:Memory {id: mem.id})
SET m.title = mem.title,
    m.type = mem.type,
    m.relevance_score = mem.score,
    m.updated_at = '2025-10-20T10:00:00Z',
    m.status = 'active'
MERGE (u1)-[:CREATED {confidence: mem.score}]->(m)
WITH u1, mem, m
UNWIND mem.topics AS topic_name
MERGE (t:Topic {name: topic_name})
MERGE (m)-[:TAGGED_WITH]->(t)
WITH u1, collect(m) AS memories
MERGE (u2:User {id: 'perf_user_002'})
SET u2.name = 'Memory Analyst',
    u2.email = 'perf_user_002@ninaivalaigal.dev',
    u2.role = 'analyst',
    u2.team_id = 'team_perf_memory',
    u2.organization_id = 'org_perf'
MERGE (u3:User {id: 'perf_user_003'})
SET u3.name = 'Collaboration Lead',
    u3.email = 'perf_user_003@ninaivalaigal.dev',
    u3.role = 'lead',
    u3.team_id = 'team_perf_collab',
    u3.organization_id = 'org_perf'
MERGE (u1)-[:COLLABORATES_WITH]->(u2)
MERGE (u2)-[:COLLABORATES_WITH]->(u3)
MERGE (u1)-[:COLLABORATES_WITH]->(u3)
WITH u1, u2, u3, memories
UNWIND [
  {user_id: 'perf_user_002', projects: ['proj_search', 'proj_latency']},
  {user_id: 'perf_user_003', projects: ['proj_memory', 'proj_collab']}
] AS row
MERGE (coworker:User {id: row.user_id})
WITH row, coworker, memories
UNWIND row.projects AS project_id
MERGE (p:Project {id: project_id})
SET p.status = 'active'
MERGE (coworker)-[:WORKS_ON]->(p)
WITH memories
UNWIND [
  {source: 'perf_mem_001', target: 'perf_mem_004', score: 0.91},
  {source: 'perf_mem_002', target: 'perf_mem_005', score: 0.87},
  {source: 'perf_mem_003', target: 'perf_mem_006', score: 0.89},
  {source: 'perf_mem_004', target: 'perf_mem_002', score: 0.93}
] AS link
MATCH (source:Memory {id: link.source}), (target:Memory {id: link.target})
MERGE (source)-[:SIMILAR_TO {score: link.score}]->(target)
RETURN size(memories) AS memory_count
