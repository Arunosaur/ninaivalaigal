# Multipart Security (Consolidated)

Merges the hardened multipart validation into the main security bundle.

## Included
- Stream-time per-part limit with early abort
- Executable detection: Mach-O, Java .class, PE/ELF
- MP4/ISO-BMFF offset-aware detection
- Archive blocking for text endpoints
- UTF-8-only text enforcement
- Content-Transfer-Encoding guard
- Tests for each category

## Integration
- Ensure Starlette adapter calls the helpers from `server/security/multipart/strict_limits.py`
- Cap parts per request in the adapter (e.g., 256)
- Expose active limits in `/healthz/config`

## Rollout
- Use feature flag if needed (`MULTIPART_STRICT_MODE=true`)
- Canary and monitor `multipart_reject_total{reason}`
