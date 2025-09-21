// Nodes
CREATE (:User {id: 'u1', name: 'Arun'});
CREATE (:Memory {id: 'm1', title: 'Redis Setup', type: 'core'});
CREATE (:Macro {id: 'mac1', name: 'Setup Sequence', tag: 'infra'});
CREATE (:Agent {id: 'a1', name: 'eM'});
CREATE (:Topic {id: 't1', label: 'Deployment'});
CREATE (:Source {id: 's1', kind: 'GitHub', ref: 'specs/053/'});

// Edges
MATCH (u:User {id: 'u1'}), (m:Memory {id: 'm1'}) CREATE (u)-[:CREATED]->(m);
MATCH (m:Memory {id: 'm1'}), (mac:Macro {id: 'mac1'}) CREATE (m)-[:LINKED_TO]->(mac);
MATCH (mac:Macro {id: 'mac1'}), (a:Agent {id: 'a1'}) CREATE (mac)-[:TRIGGERED_BY]->(a);
MATCH (mac:Macro {id: 'mac1'}), (t:Topic {id: 't1'}) CREATE (mac)-[:TAGGED_WITH]->(t);
MATCH (m:Memory {id: 'm1'}), (s:Source {id: 's1'}) CREATE (m)-[:DERIVED_FROM]->(s);
