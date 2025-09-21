// Test: Find all macros created by a specific user with traversal depth
MATCH (u:User {id: 'u1'})-[:CREATED]->(:Memory)-[:LINKED_TO]->(m:Macro)
RETURN m.name LIMIT 10;

// Test: Traverse memory → macro → agent
MATCH (:Memory)-[:LINKED_TO]->(:Macro)-[:TRIGGERED_BY]->(a:Agent)
RETURN DISTINCT a.name;

// Test: Weighted relevance (mock score)
MATCH (m:Memory)-[r:LINKED_TO]->(mac:Macro)
WHERE r.weight > 0.7
RETURN mac.name, r.weight
ORDER BY r.weight DESC LIMIT 5;
