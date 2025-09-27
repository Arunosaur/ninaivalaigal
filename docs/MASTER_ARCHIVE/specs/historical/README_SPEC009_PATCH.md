# Spec 009 Patch: JWT Resolver + RBAC Integration

This patch introduces a real JWT claims resolver and wires RBAC decorators to
use it. It also includes role inheritance helpers and end-to-end tests.

## Files
- server/security/rbac/subject_ctx.py
- server/security/rbac/jwt_resolver.py
- server/security/rbac/decorators.py
- rbac/policy.py (role inheritance + expand_roles)
- tests/test_rbac_jwt_matrix.py

## Usage
```python
from server.security.rbac.jwt_resolver import JWTClaimsResolver
from server.security.rbac.decorators import set_jwt_resolver

set_jwt_resolver(JWTClaimsResolver(secret=os.getenv("NINAI_JWT_SECRET"), algorithms=["HS256"]))  # local/dev
# or JWKS:
# set_jwt_resolver(JWTClaimsResolver(jwks_url=os.getenv("NINAI_JWKS_URL"), algorithms=["RS256"], audience="api://ninaiv", issuer="https://issuer"))
```
