# Acceptance for SPEC <ID>

1. Health:
   - API GET /health → 200
   - mem0 GET /health → 200

2. Memory write/read:
   - POST /remember {text:"hello"} → id
   - GET  /recall?q=hello → returns id

3. Tenant scoping:
   - org/team/user context forwarded to mem0 (unit test)
