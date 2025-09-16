# PR Micro-Diff Pack: Subject Context Hook + Config Validator

Includes:
- `rbac/context_provider.py` — explicit subject_ctx_provider hook & FastAPI dependency.
- `server/security/bundle_patch/with_ctx_bundle.py` — example bundle apply function accepting subject_ctx_provider.
- `server/security/config/validator.py` — central config validator and /healthz/config endpoint.
- Tests for both pieces.

How to use:
1) Install your JWT resolver:
   ```python
   from rbac.context_provider import install_subject_ctx_provider
   install_subject_ctx_provider(app, my_verified_jwt_provider)
   ```
2) Switch your bundle call to the patched variant or add `subject_ctx_provider` arg to your existing function.
3) Validate config on startup and include the health router.
